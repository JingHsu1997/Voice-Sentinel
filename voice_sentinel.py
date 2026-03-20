import os
import asyncio
import platform
import argparse
import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv

# Gemini SDK
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Load env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if genai and API_KEY:
    genai.configure(api_key=API_KEY)
    print(f"[INFO] Gemini API Ready (Key prefix: {API_KEY[:4]}...)")
else:
    print("[WARNING] Gemini not initialized")

FS = 16000
DURATION = 5
FILENAME = "input.wav"


class VoiceSentinel:
    def __init__(self, baseline_rate=3.0, test=False):
        self.baseline_rate = baseline_rate
        self.test = test

        if genai and API_KEY and not test:
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

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
    # 🧠 Analyze Voice
    # -------------------------
    def analyze_health(self, file_path):
        y, sr = librosa.load(file_path)

        intervals = librosa.effects.split(y, top_db=25)
        speech_duration = sum([i[1] - i[0] for i in intervals]) / sr
        speech_rate = len(intervals) / (speech_duration + 1e-6)

        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[pitches > 0]
        pitch_std = np.std(pitch_values) if len(pitch_values) > 0 else 0

        is_abnormal = False
        msg = "Normal state detected"

        if speech_rate < self.baseline_rate * 0.6:
            is_abnormal = True
            msg = "Speech rate is slow, possible fatigue"
        elif pitch_std < 15:
            is_abnormal = True
            msg = "Flat tone, low energy"

        return {
            "rate": speech_rate,
            "pitch_std": pitch_std,
            "abnormal": is_abnormal,
            "msg": msg
        }

    # -------------------------
    # 🤖 Gemini AI
    # -------------------------
    async def get_ai_response(self, analysis):
        if self.test:
            return "Test Mode: You sound a bit tired. Maybe take a break."

        if not self.model:
            return "AI not available"

        prompt = f"""
You are a caring home assistant robot.

User voice condition:
- {analysis['msg']}
- Speech rate: {analysis['rate']:.2f}

Respond warmly in under 50 words.
If tired → suggest rest or water.
"""

        try:
            response = await self.model.generate_content_async(
                contents=prompt
            )

            return response.text if response.text else "No response"

        except Exception as e:
            print(f"[ERROR] Gemini failed: {e}")
            return self.fallback_response(analysis)

    # -------------------------
    # 🧯 Fallback AI（超重要）
    # -------------------------
    def fallback_response(self, analysis):
        if analysis["abnormal"]:
            return "You sound a bit tired. Please take a break and drink some water."
        return "You sound good! Keep going!"

    # -------------------------
    # 🔊 TTS
    # -------------------------
    async def speak(self, text):
        print(f"\n[AI Reply]: {text}")

        if self.test:
            return

        try:
            import edge_tts

            tts = edge_tts.Communicate(text, "en-US-AriaNeural")
            await tts.save("output.mp3")

            if platform.system() == "Windows":
                os.startfile("output.mp3")
            else:
                print("[INFO] Saved to output.mp3")

        except Exception as e:
            print(f"[TTS ERROR]: {e}")


# -------------------------
# 🚀 Main Flow
# -------------------------
async def main(test_mode=False):
    sentinel = VoiceSentinel(test=test_mode)

    audio = sentinel.record_audio()

    print("[INFO] Analyzing...")
    features = sentinel.analyze_health(audio)
    print(f"[Result] {features}")

    reply = await sentinel.get_ai_response(features)

    await sentinel.speak(reply)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    asyncio.run(main(test_mode=args.test))