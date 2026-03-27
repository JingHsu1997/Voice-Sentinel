import os
import asyncio
import argparse
import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv

try:
    import parselmouth
    from parselmouth.praat import call as praat_call
except ImportError:
    parselmouth = None

try:
    from google import genai as _genai_module
    from google.genai import types as _genai_types
except ImportError:
    _genai_module = None
    _genai_types = None

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


def check_snr_and_score(biometrics: dict) -> tuple[str, float | None, bool]:
    """
    1. SNR noise check (< 15 dB rejected immediately)
    2. Local hard scoring (no Token cost)
    Returns: (summary_str, score_or_None, need_ai)
    """
    if biometrics.get('snr', 20) < 15:
        return "⚠️ Environment too noisy. Please test in a quiet place to avoid false readings.", None, False

    score, alerts = 0.0, []

    if biometrics.get('jitter_local') and biometrics['jitter_local'] > 1.0:
        score += min(35, (biometrics['jitter_local'] / 5.0) * 35)
        alerts.append("Unstable vocal fold vibration")

    if biometrics.get('shimmer_local') and biometrics['shimmer_local'] > 3.8:
        score += min(35, (biometrics['shimmer_local'] / 15.0) * 35)
        alerts.append("Weak amplitude control")

    pitch_sd = biometrics.get('pitch_sd', 0)
    if pitch_sd > 0 and pitch_sd < 15:
        score += 30 * (1 - (pitch_sd / 15))
        alerts.append("Extremely monotone pitch")

    if score >= 70:
        status, need_ai = "Severe fatigue / Possible pathology", True
    elif score >= 40:
        status, need_ai = "Moderate fatigue", True
    else:
        status, need_ai = "Good", False

    summary = f"Composite score: {round(score, 1)}/100 ({status})\nAlerts: {', '.join(alerts) if alerts else 'All clear'}"
    return summary, round(score, 1), need_ai


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
        n_fft  = int(0.025 * sr)
        hop    = int(0.010 * sr)
        mfcc   = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=12,
                                       n_fft=n_fft, hop_length=hop,
                                       window='hamming')
        delta  = librosa.feature.delta(mfcc, order=1)
        delta2 = librosa.feature.delta(mfcc, order=2)
        return np.concatenate([mfcc.mean(axis=1),
                                delta.mean(axis=1),
                                delta2.mean(axis=1)])

    def _compute_vc(self, test_vec: np.ndarray) -> float:
        """
        Voice Correlation (Vc) — Pearson r between baseline and test vectors.
        Returns 1.0 when identical to rested baseline (Greeley et al., 2007 §2.3).
        """
        if self._baseline_vector is None:
            return 1.0
        r = np.corrcoef(self._baseline_vector, test_vec)[0, 1]
        return float(np.clip(r, -1.0, 1.0))

    def set_baseline(self, file_path: str):
        """Explicitly record a rested-state baseline from a file."""
        y, sr = librosa.load(file_path, sr=FS)
        self._baseline_vector = self._extract_voice_vector(y, sr)
        print(f"[INFO] Baseline vector set from {file_path}")

    def _compute_dysphonia(self, audio_path: str, y: np.ndarray, sr: int) -> dict:
        """
        Compute jitter (local), shimmer (local), HNR, pitch SD, and pause ratio.

        Jitter & Shimmer via Praat (parselmouth) when available, fallback to
        envelope peak picking otherwise.
        Thresholds from Teixeira et al. (2013) and Farrús et al. (2007):
          Jitter > 1.04%, Shimmer > 3.81%, HNR < 7 dB
        """
        pitch_sd = 0.0
        pause_ratio = 0.0
        jitter_local = None
        shimmer_local = None
        hnr_db = None

        # --- Praat-based Jitter, Shimmer, Pitch SD ---
        if parselmouth and audio_path:
            try:
                sound = parselmouth.Sound(audio_path)
                pp = praat_call(sound, "To PointProcess (periodic, cc)", 75, 500)
                jitter_local = round(praat_call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100, 4)
                shimmer_local = round(praat_call([sound, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100, 4)

                pitch = sound.to_pitch()
                f0 = pitch.selected_array['frequency']
                f0 = f0[f0 > 0]
                pitch_sd = round(float(np.std(f0)), 2) if len(f0) > 0 else 0.0
            except Exception:
                pass  # fall through to envelope method

        # --- Fallback: envelope peak picking for Jitter/Shimmer/HNR ---
        if jitter_local is None:
            win = max(1, int(0.010 * sr))
            env = np.convolve(np.abs(y), np.ones(win) / win, mode='same')
            min_dist = max(1, int(0.002 * sr))
            max_dist = int(0.020 * sr)

            peaks = []
            for i in range(1, len(env) - 1):
                if env[i] > env[i - 1] and env[i] > env[i + 1]:
                    if not peaks or (i - peaks[-1]) >= min_dist:
                        peaks.append(i)

            if len(peaks) >= 3:
                periods = np.diff(peaks).astype(float)
                amplitudes = np.array([env[p] for p in peaks[:-1]], dtype=float)
                mask = (periods >= min_dist) & (periods <= max_dist)
                periods = periods[mask]
                amplitudes = amplitudes[mask]

                if len(periods) >= 2 and amplitudes.mean() > 0:
                    jitter_local = round((np.mean(np.abs(np.diff(periods))) / periods.mean()) * 100, 4)
                    shimmer_local = round((np.mean(np.abs(np.diff(amplitudes))) / amplitudes.mean()) * 100, 4)

                    ac = np.correlate(y, y, mode='full')[len(y) - 1:]
                    lag = min(int(round(periods.mean())), len(ac) - 1)
                    denom = ac[0] - ac[lag]
                    if denom > 0 and ac[lag] > 0:
                        hnr_db = round(10 * np.log10(ac[lag] / denom), 2)

        # --- Pause ratio via librosa ---
        non_silent = librosa.effects.split(y, top_db=25)
        total_dur = len(y) / sr
        speech_dur = sum((e - s) / sr for s, e in non_silent)
        pause_ratio = round((total_dur - speech_dur) / total_dur, 3) if total_dur > 0 else 0.0

        return {
            "jitter_local": jitter_local,
            "shimmer_local": shimmer_local,
            "hnr_db": hnr_db,
            "pitch_sd": pitch_sd,
            "pause_ratio": pause_ratio,
        }

    def analyze_health(self, file_path: str) -> dict:
        """
        Combined analysis:
          1. Voice Correlation (Vc) — fatigue detection (Greeley et al., 2007)
          2. Dysphonia parameters — jitter, shimmer, HNR (Teixeira et al., 2013;
             Farrús et al., 2007)
          3. Local scoring via check_snr_and_score()
        """
        y, sr = librosa.load(file_path, sr=FS)
        vec = self._extract_voice_vector(y, sr)

        is_first = self._baseline_vector is None
        vc = self._compute_vc(vec)
        if is_first:
            self._baseline_vector = vec

        # --- Fatigue classification (Vc) ---
        if vc >= VC_THRESHOLDS["rested"]:
            fatigue_level, vc_abnormal, vc_msg = "Rested", False, "Normal"
        elif vc >= VC_THRESHOLDS["mild_fatigue"]:
            fatigue_level, vc_abnormal, vc_msg = "Mild fatigue", True, "Mild fatigue detected (Vc ≈ 0.82 at ~27 h awake)"
        else:
            fatigue_level, vc_abnormal, vc_msg = "Severe fatigue", True, "Severe fatigue detected (Vc ≈ 0.19 at ~66 h awake)"

        # --- Dysphonia + biometrics ---
        dp = self._compute_dysphonia(file_path, y, sr)

        # --- SNR estimate ---
        rms = float(np.sqrt(np.mean(y ** 2)))
        noise_floor = float(np.sqrt(np.mean(np.sort(y ** 2)[:len(y) // 10])))
        snr = round(20 * np.log10(rms / noise_floor) if noise_floor > 0 else 99.0, 1)

        # --- Local scoring ---
        bio = {**dp, "vc": vc, "snr": snr}
        summary, score, need_ai = check_snr_and_score(bio)

        return {
            "vc": round(vc, 4),
            "fatigue_level": fatigue_level,
            "jitter_local": dp["jitter_local"],
            "shimmer_local": dp["shimmer_local"],
            "hnr_db": dp["hnr_db"],
            "pitch_sd": dp["pitch_sd"],
            "pause_ratio": dp["pause_ratio"],
            "score": score,
            "need_ai": need_ai,
            "bio_summary": summary,
            "abnormal": vc_abnormal,
            "msg": vc_msg,
            "baseline_set": is_first,
        }

    # Legacy alias
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
        fatigue = str(analysis.get('fatigue_level', 'Rested'))[:50]
        status  = str(analysis.get('msg', ''))[:100]
        score   = analysis.get('score')
        need_ai = analysis.get('need_ai', vc < VC_THRESHOLDS["rested"])

        if not need_ai:
            return self.fallback_response(analysis)

        prompt = (
            "You are a warm, empathetic companion robot (like Erica from Osaka University).\n\n"
            "Voice analysis results:\n"
            f"- Vc score: {vc:.4f}  (1.0 = fully rested, ~0.82 = ~27 h awake, ~0.19 = ~66 h awake)\n"
            f"- Fatigue level: {fatigue}\n"
            f"- Status: {status}\n"
            + (f"- Composite score: {score}/100\n" if score is not None else "") +
            "\nRespond with genuine empathy in under 60 words. Adjust tone to fatigue level."
        )

        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=_genai_types.GenerateContentConfig(
                        temperature=0.7,
                    )
                ),
                timeout=30.0
            )
            return response.text if response.text else "No response"

        except asyncio.TimeoutError:
            print("[ERROR] Gemini request timed out.")
            return self.fallback_response(analysis)
        except Exception as e:
            print(f"[ERROR] Gemini failed: {e}")
            return self.fallback_response(analysis)

    def fallback_response(self, analysis):
        import random
        fatigue = analysis.get("fatigue_level", "Rested")
        if fatigue == "Severe fatigue":
            responses = [
                "Your voice shows signs of severe fatigue. Please rest as soon as possible.",
                "You sound very exhausted. Try to get some sleep and take care of yourself.",
                "Your voice indicates extreme tiredness. Please stop and rest now.",
            ]
        elif fatigue == "Mild fatigue":
            responses = [
                "You sound a little tired. Consider taking a short break and drinking some water.",
                "Your voice shows mild fatigue. A quick rest could help you recharge.",
                "Sounds like you've been working hard. Take a breather when you can!",
            ]
        else:
            responses = [
                "You sound great! Keep up the good work.",
                "Your voice sounds clear and energetic. Nice job!",
                "All good! You sound well-rested and ready to go.",
                "Your voice is in great shape today. Keep it up!",
                "Sounding healthy and strong. Have a wonderful day!",
            ]
        return random.choice(responses)

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
