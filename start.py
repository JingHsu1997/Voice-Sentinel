#!/usr/bin/env python
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from voice_sentinel import VoiceSentinel

import sounddevice as sd
import soundfile as sf

FS = 16000
RECORDINGS_DIR = "recordings"

SAMPLE_GUIDE = """\
+------------------------------------------------------+
|                   VOICE SAMPLE                       |
+------------------------------------------------------+
|  Speak naturally -- just as you feel right now.      |
+------------------------------------------------------+"""


def input_path(name: str) -> Path:
    return Path(RECORDINGS_DIR) / f"{name}_input.wav"


def record_wav(path: Path, duration: int = 5):
    input(f"\nPress Enter when ready to record ({duration} seconds)...")
    print("[REC] Recording... speak now!")
    recording = sd.rec(int(duration * FS), samplerate=FS, channels=1)
    sd.wait()
    sf.write(str(path), recording, FS)
    print("[OK]  Done.\n")


async def session(name: str):
    ip = input_path(name)
    sentinel = VoiceSentinel(test=False)

    print(SAMPLE_GUIDE)
    record_wav(ip)

    print("Analyzing...")
    features = sentinel.analyze_health(str(ip))

    def _fmt(v, unit=""):
        return f"{v}{unit}" if v is not None else "N/A"

    W = 46
    print(f"\n{'='*W}")
    print(f"  {'Score':<14}: {features.get('score', 0):.1f}/100")
    print(f"  {'Vc':<14}: {features['vc']:.4f}")
    print(f"  {'Fatigue':<14}: {features['fatigue_level']}")
    print(f"  {'Jitter':<14}: {_fmt(features['jitter_local'], '%')}")
    print(f"  {'Shimmer':<14}: {_fmt(features['shimmer_local'], '%')}")
    print(f"  {'Pitch SD':<14}: {_fmt(features['pitch_sd'], ' Hz')}")
    print(f"  {'Pause Ratio':<14}: {features['pause_ratio']*100:.1f}%")
    print(f"{'='*W}\n")

    import asyncio as _asyncio
    if features.get('need_ai'):
        reply = await sentinel.get_ai_response(features)
        print(f"\n[AI Analysis]\n{reply}\n")
    else:
        reply = sentinel.fallback_response(features)
        print(f"\n[Result] {reply}\n")

    print("What's next?")
    print("  [Enter]  Record again")
    print("  [s]      Switch to another person")
    print("  [q]      Quit")
    choice = input("→ ").strip().lower()

    if choice == "s":
        return "switch"
    if choice == "q":
        return "quit"
    return "continue"


async def main():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    print("\n" + "=" * 46)
    print("  Voice Sentinel Pro -- Voice Analyzer")
    print("=" * 46)

    name = input("\nEnter your name: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty.")
        return

    print(f"\nHello, {name}! Let's get started.")

    while True:
        action = await session(name)

        if action == "switch":
            name = input("\nEnter new name: ").strip()
            if not name:
                print("[ERROR] Name cannot be empty.")
                return
            print(f"\nHello, {name}! Let's get started.")
        elif action == "quit":
            print("\nTake care. Goodbye!")
            return


if __name__ == "__main__":
    asyncio.run(main())
