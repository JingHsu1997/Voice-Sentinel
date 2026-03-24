#!/usr/bin/env python
"""
Voice Sentinel - Custom Audio Analysis Tool
Analyze your own audio files for voice health monitoring
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Import from main module
sys.path.insert(0, str(Path(__file__).parent))
from voice_sentinel import VoiceSentinel


def analyze_custom_audio(file_path: str, baseline_path: str = None):
    """
    Analyze a custom audio file (Greeley et al., 2007 Voice Correlation method)
    """
    audio_file = Path(file_path)
    if not audio_file.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False
    if audio_file.suffix.lower() not in ['.wav', '.mp3', '.flac', '.ogg']:
        print(f"[ERROR] Unsupported audio format: {audio_file.suffix}")
        return False

    print(f"\n{'='*60}")
    print("🎤 Voice Sentinel - Custom Audio Analysis (Vc Method)")
    print(f"{'='*60}\n")
    print(f"📁 Analyzing file: {audio_file.name}\n")

    sentinel = VoiceSentinel(test=False)
    if baseline_path:
        sentinel.set_baseline(baseline_path)
    try:
        print("🔍 Analyzing voice features (36-D MFCC+Δ+ΔΔ vector)...\n")
        features = sentinel.analyze_health(str(audio_file))

        print(f"{'='*60}")
        print("📈 Analysis Results (Greeley et al., 2007)")
        print(f"{'='*60}\n")

        vc = features['vc']
        print(f"Voice Correlation (Vc): {vc:.4f}")
        print(f"  1.0 = fully rested  |  ~0.82 = ~27h sleep deprived  |  ~0.19 = ~66h sleep deprived")

        if features['baseline_set']:
            print(f"  ℹ️  This recording has been set as baseline (Vc = 1.0)")
        else:
            bar = int(vc * 20)
            print(f"  [{'█' * bar}{'░' * (20 - bar)}] {vc:.2%}")

        print(f"\nFatigue Level: {features['fatigue_level']}")

        # --- Dysphonia parameters (reference only, not used for classification) ---
        def _fmt(v, unit=""):
            return f"{v}{unit}" if v is not None else "N/A"

        print(f"\n--- Acoustic Perturbation Parameters (reference only, not applicable for natural speech) ---")
        print(f"  Jitter  (local): {_fmt(features['jitter_local'], '%'):>10}")
        print(f"  Shimmer (local): {_fmt(features['shimmer_local'], '%'):>10}")
        print(f"  HNR:             {_fmt(features['hnr_db'], ' dB'):>10}")

        status_icon = "🟢" if not features['abnormal'] else "🔴"
        print(f"\nResult: {status_icon} {features['msg']}")
        print(f"\n{'='*60}\n")
        return True
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)}")
        return False


async def analyze_with_ai(file_path: str, baseline_path: str = None):
    """Analyze a custom audio file and generate an AI response (Vc method)"""
    audio_file = Path(file_path)
    if not audio_file.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False
    if audio_file.suffix.lower() not in ['.wav', '.mp3', '.flac', '.ogg']:
        print(f"[ERROR] Unsupported audio format: {audio_file.suffix}")
        return False

    print(f"\n{'='*60}")
    print("🎤 Voice Sentinel - Custom Audio Analysis (with AI Response)")
    print(f"{'='*60}\n")
    print(f"📁 Analyzing file: {audio_file.name}\n")

    sentinel = VoiceSentinel(test=False)
    if baseline_path:
        sentinel.set_baseline(baseline_path)
    try:
        print("🔍 Analyzing voice features (36-D MFCC+Δ+ΔΔ vector)...\n")
        features = sentinel.analyze_health(str(audio_file))

        print(f"Vc = {features['vc']:.4f}  |  {features['fatigue_level']}")
        print(f"Status: {features['msg']}\n")

        print(f"{'='*60}")
        print("🤖 Generating AI Response")
        print(f"{'='*60}\n")
        reply = await sentinel.get_ai_response(features)
        print(f"AI Response: {reply}\n")
        print(f"{'='*60}\n")
        return True
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Voice Sentinel - Custom Audio Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python analyze_audio.py path/to/your/audio.wav
  
  # Analysis with AI response
  python analyze_audio.py path/to/your/audio.wav --ai
  
  # Custom baseline values
  python analyze_audio.py path/to/your/audio.wav --rate 4.0 --pitch 150
        """
    )
    
    parser.add_argument(
        "file",
        help="Audio file path (supports .wav, .mp3, .flac, .ogg)"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate AI response (requires API key)"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Baseline audio file path, e.g.: recordings/rested.wav"
    )
    
    args = parser.parse_args()
    
    # Run analysis
    if args.ai:
        success = asyncio.run(analyze_with_ai(args.file, args.baseline))
    else:
        success = analyze_custom_audio(args.file, args.baseline)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
