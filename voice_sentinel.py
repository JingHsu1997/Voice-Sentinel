import os
import asyncio
import argparse
import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv

# Optional Gemini SDK — imported at module level to allow graceful degradation.
try:
    from google import genai as _genai_module
    from google.genai import types as _genai_types
except ImportError:
    _genai_module = None
    _genai_types = None

# Load env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if _genai_module and API_KEY:
    print(f"[INFO] Gemini API Ready (Key prefix: {API_KEY[:4]}...)")
else:
    print("[WARNING] Gemini not initialized")

FS = 16000
DURATION = 5
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)
FILENAME = os.path.join(RECORDINGS_DIR, "input.wav")

# Vc degradation reference (Greeley et al., 2007)
# Rested=1.0, ~27h awake≈0.82, ~66h awake≈0.19
VC_THRESHOLDS = {"rested": 0.90, "mild_fatigue": 0.60, "severe_fatigue": 0.0}

class VoiceSentinel:
    def __init__(self, baseline_rate=3.0, baseline_pitch=120.0, test=False):
        self.baseline_rate = baseline_rate
        self.baseline_pitch = baseline_pitch
        self.test = test
        self._baseline_vector = None  # 36-D baseline (Trial 1 / rested state)
        if _genai_module and API_KEY:
            self.client = _genai_module.Client(api_key=API_KEY)
        else:
            self.client = None

    def _extract_voice_vector(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Build the 36-D characteristic voice vector per Greeley et al. (2007):
        12 MFCCs + 12 delta-MFCCs + 12 delta-delta-MFCCs, mean-pooled over frames.

        Signal parameters (paper §2.2):
          - sr = 16 000 Hz
          - Hamming window, 25 ms (400 samples)
          - 10 ms hop (160 samples) → 100 Hz frame rate
        """
        n_fft  = int(0.025 * sr)   # 400 samples @ 16 kHz
        hop    = int(0.010 * sr)   # 160 samples
        mfcc   = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=12,
                                       n_fft=n_fft, hop_length=hop,
                                       window='hamming')
        delta  = librosa.feature.delta(mfcc, order=1)
        delta2 = librosa.feature.delta(mfcc, order=2)
        # Mean over time → shape (36,)
        return np.concatenate([mfcc.mean(axis=1),
                                delta.mean(axis=1),
                                delta2.mean(axis=1)])

    def _compute_vc(self, test_vec: np.ndarray) -> float:
        """
        Voice Correlation (Vc) — Pearson r between baseline and test vectors.
        Returns 1.0 when identical to rested baseline (Greeley et al., 2007 §2.3).
        """
        if self._baseline_vector is None:
            return 1.0  # First recording becomes the baseline
        r = np.corrcoef(self._baseline_vector, test_vec)[0, 1]
        return float(np.clip(r, -1.0, 1.0))

    def set_baseline(self, file_path: str):
        """Explicitly record a rested-state baseline from a file."""
        y, sr = librosa.load(file_path, sr=FS)
        self._baseline_vector = self._extract_voice_vector(y, sr)
        print(f"[INFO] Baseline vector set from {file_path}")

    def _compute_dysphonia(self, y: np.ndarray, sr: int) -> dict:
        """
        Compute jitter (local), shimmer (local), and HNR via autocorrelation.
        Based on Teixeira et al. (2013) "Vocal Acoustic Analysis - Jitter, Shimmer and HNR".

        Fundamental period detection:
          - Uses |y| with a moving-average envelope (~10 ms window) for peak detection
          - Ensures both positive and negative glottal pulses are captured

        Thresholds (Teixeira et al., 2013):
          Jitter > 1.04%  → pathological
          Shimmer > 3.81% → pathological
          HNR < 7 dB      → pathological
        """
        # --- Fundamental period detection via |y| + moving-average smoothing ---
        win = max(1, int(0.010 * sr))          # ~10 ms window
        env = np.convolve(np.abs(y), np.ones(win) / win, mode='same')

        # Minimum peak distance: 2 ms (500 Hz max F0); max: 20 ms (50 Hz min F0)
        min_dist = max(1, int(0.002 * sr))
        max_dist = int(0.020 * sr)

        # Simple peak picking on envelope
        peaks = []
        for i in range(1, len(env) - 1):
            if env[i] > env[i - 1] and env[i] > env[i + 1]:
                if not peaks or (i - peaks[-1]) >= min_dist:
                    peaks.append(i)

        # Need at least 3 peaks for period differences
        if len(peaks) < 3:
            return {"jitter_local": None, "shimmer_local": None, "hnr_db": None}

        periods = np.diff(peaks).astype(float)          # T_i in samples
        amplitudes = np.array([env[p] for p in peaks[:-1]], dtype=float)

        # Filter out periods outside physiological range
        mask = (periods >= min_dist) & (periods <= max_dist)
        periods = periods[mask]
        amplitudes = amplitudes[mask]

        if len(periods) < 2 or amplitudes.mean() == 0:
            return {"jitter_local": None, "shimmer_local": None, "hnr_db": None}

        # --- Jitter (local, %) ---
        # |T_i - T_{i+1}| / mean(T) × 100
        jitter = (np.mean(np.abs(np.diff(periods))) / periods.mean()) * 100

        # --- Shimmer (local, %) ---
        # |A_i - A_{i+1}| / mean(A) × 100
        shimmer = (np.mean(np.abs(np.diff(amplitudes))) / amplitudes.mean()) * 100

        # --- HNR via autocorrelation (Boersma, 1993 / Teixeira et al., 2013) ---
        # HNR = 10 * log10( AC(T) / (AC(0) - AC(T)) )
        ac = np.correlate(y, y, mode='full')
        ac = ac[len(ac) // 2:]          # keep non-negative lags
        ac0 = ac[0]
        lag = int(round(periods.mean()))  # mean fundamental period in samples
        lag = min(lag, len(ac) - 1)
        ac_T = ac[lag]
        denom = ac0 - ac_T
        if denom <= 0 or ac_T <= 0:
            hnr_db = None
        else:
            hnr_db = round(10 * np.log10(ac_T / denom), 2)

        return {
            "jitter_local": round(float(jitter), 4),
            "shimmer_local": round(float(shimmer), 4),
            "hnr_db": hnr_db,
        }

    def analyze_health(self, file_path: str) -> dict:
        """
        Combined analysis:
          1. Voice Correlation (Vc) — fatigue detection (Greeley et al., 2007)
          2. Dysphonia parameters — jitter, shimmer, HNR (Teixeira et al., 2013)

        abnormal = True if Vc indicates fatigue OR any dysphonia threshold exceeded.
        """
        y, sr = librosa.load(file_path, sr=FS)
        vec = self._extract_voice_vector(y, sr)

        is_first = self._baseline_vector is None
        vc = self._compute_vc(vec)
        if is_first:
            self._baseline_vector = vec

        # --- Fatigue classification ---
        if vc >= VC_THRESHOLDS["rested"]:
            fatigue_level, vc_abnormal, vc_msg = "Rested", False, "Normal"
        elif vc >= VC_THRESHOLDS["mild_fatigue"]:
            fatigue_level, vc_abnormal, vc_msg = "Mild fatigue", True, "Mild fatigue detected (Vc ≈ 0.82 at ~27 h awake)"
        else:
            fatigue_level, vc_abnormal, vc_msg = "Severe fatigue", True, "Severe fatigue detected (Vc ≈ 0.19 at ~66 h awake)"

        # --- Dysphonia parameters (reference only, not used for abnormal classification) ---
        dp = self._compute_dysphonia(y, sr)

        # --- Merge ---
        abnormal = vc_abnormal
        msg = vc_msg

        return {
            "vc": round(vc, 4),
            "fatigue_level": fatigue_level,
            "jitter_local": dp["jitter_local"],
            "shimmer_local": dp["shimmer_local"],
            "hnr_db": dp["hnr_db"],
            "abnormal": abnormal,
            "msg": msg,
            "baseline_set": is_first,
        }

    # Legacy alias so existing callers (analyze_audio.py) keep working
    def analyze_health_features(self, file_path: str) -> dict:
        return self.analyze_health(file_path)

    # -------------------------
    # 🎤 Record Audio
    # -------------------------
    def record_audio(self):
        if self.test:
            print("[TEST] Generating synthetic audio...")
            t = np.linspace(0, 2, int(FS * 2), endpoint=False)
            y = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
            sf.write(FILENAME, y, FS)
            return FILENAME

        print(">>> Listening... (5 seconds)")
        recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1)
        sd.wait()
        sf.write(FILENAME, recording, FS)
        return FILENAME

    # -------------------------
    # Gemini AI
    # -------------------------
    async def get_ai_response(self, analysis):
        if self.test:
            return "Test Mode: You sound a bit tired. Maybe take a break."

        if not self.client:
            return "AI not available"

        vc = analysis.get('vc', 1.0)
        fatigue = analysis.get('fatigue_level', 'Rested')
        prompt = f"""
You are a warm, empathetic companion robot (like Erica from Osaka University).

Voice analysis results:
- Vc score: {vc:.4f}  (1.0 = fully rested, ~0.82 = ~27 h awake, ~0.19 = ~66 h awake)
- Fatigue level: {fatigue}
- Status: {analysis['msg']}

Respond with genuine empathy in under 60 words. Adjust tone to fatigue level.
"""

        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=prompt,
                    config=_genai_types.GenerateContentConfig(
                        max_output_tokens=100,
                        temperature=0.7,
                    )
                ),
                timeout=10.0
            )
            return response.text if response.text else "No response"

        except asyncio.TimeoutError:
            print("[ERROR] Gemini request timed out.")
            return self.fallback_response(analysis)
        except Exception as e:
            print(f"[ERROR] Gemini failed: {e}")
            return self.fallback_response(analysis)

    # -------------------------
    # 🧯 Fallback AI (critical)
    # -------------------------
    def fallback_response(self, analysis):
        if analysis["abnormal"]:
            return "You sound a bit tired. Please take a break and drink some water."
        return "You sound good! Keep going!"

    # -------------------------
    # TTS
    # -------------------------
    async def speak(self, text):
        print(f"\n[AI Reply]: {text}")
        if self.test: return
        try:
            import edge_tts
            import pygame
            tts = edge_tts.Communicate(text, "en-US-AriaNeural")
            output_path = os.path.join(RECORDINGS_DIR, "output.mp3")
            await tts.save(output_path)
            pygame.mixer.init()
            pygame.mixer.music.load(output_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            pygame.mixer.quit()
        except Exception as e:
            print(f"[TTS ERROR]: {e}")

# -------------------------
# Main Flow
# -------------------------
BASELINE_PATH = os.path.join(RECORDINGS_DIR, "baseline.wav")

async def main(test_mode=False):
    sentinel = VoiceSentinel(test=test_mode)

    if not test_mode and os.path.exists(BASELINE_PATH):
        sentinel.set_baseline(BASELINE_PATH)

    audio = sentinel.record_audio()

    print("[INFO] Analyzing...")
    features = sentinel.analyze_health(audio)
    print(f"[Result] {features}")
    if features['baseline_set']:
        import shutil
        shutil.copy(audio, BASELINE_PATH)
        print(f"[INFO] First run — baseline saved to {BASELINE_PATH}")

    reply = await sentinel.get_ai_response(features)

    await sentinel.speak(reply)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    asyncio.run(main(test_mode=args.test))