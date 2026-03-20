#!/usr/bin/env python
"""
Voice Sentinel - 自訂音檔分析工具
使用自己的音檔進行語音健康檢查
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Import from main module
sys.path.insert(0, str(Path(__file__).parent))
from voice_sentinel import VoiceSentinel


def analyze_custom_audio(file_path: str, baseline_rate: float = 3.0, baseline_pitch: float = 120):
    """
    分析自訂音檔
    
    Args:
        file_path: 音檔路徑
        baseline_rate: 基準語速
        baseline_pitch: 基準音高
    """
    
    # 驗證檔案
    audio_file = Path(file_path)
    if not audio_file.exists():
        print(f"[ERROR] 檔案不存在：{file_path}")
        return False
    
    if audio_file.suffix.lower() not in ['.wav', '.mp3', '.flac', '.ogg']:
        print(f"[ERROR] 不支持的音檔格式：{audio_file.suffix}")
        print("       支持的格式：.wav, .mp3, .flac, .ogg")
        return False
    
    print(f"\n{'='*60}")
    print("🎤 Voice Sentinel - 自訂音檔分析")
    print(f"{'='*60}\n")
    
    print(f"📁 分析檔案：{audio_file.name}")
    print(f"📊 基準語速：{baseline_rate:.1f} 語句/秒")
    print(f"🎵 基準音高：{baseline_pitch:.1f}\n")
    
    # 建立分析器
    sentinel = VoiceSentinel(baseline_pitch=baseline_pitch, baseline_rate=baseline_rate, test=False)
    
    # 分析音檔
    try:
        print("🔍 正在分析語音特徵...\n")
        features = sentinel.analyze_health_features(str(audio_file))
        
        # 顯示結果
        print(f"{'='*60}")
        print("📈 分析結果")
        print(f"{'='*60}\n")
        
        print(f"語速 (Speech Rate):")
        print(f"  目前值：{features['rate']:.2f} 語句/秒")
        print(f"  基準值：{baseline_rate:.2f} 語句/秒")
        rate_pct = (features['rate'] / baseline_rate * 100) if baseline_rate > 0 else 0
        print(f"  相對基準：{rate_pct:.1f}%")
        if features['rate'] < baseline_rate * 0.7:
            print(f"  ⚠️ 警告：語速過慢（低於基準 {100-rate_pct:.1f}%）")
        else:
            print(f"  ✅ 正常")
        
        print(f"\n音高穩定度 (Pitch Stability):")
        print(f"  目前值：{features['pitch_std']:.2f}")
        print(f"  基準值：> 10")
        if features['pitch_std'] >= 10:
            print(f"  ✅ 正常（音高起伏豐富）")
        else:
            print(f"  ⚠️ 警告：音高平板（標準差 < 10）")
        
        print(f"\n判定結果：")
        if features['abnormal']:
            print(f"  🔴 異常狀態")
            print(f"  {features['msg']}")
        else:
            print(f"  🟢 正常狀態")
            print(f"  {features['msg']}")
        
        print(f"\n{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] 分析失敗：{str(e)}")
        return False


async def analyze_with_ai(file_path: str, baseline_rate: float = 3.0, baseline_pitch: float = 120):
    """
    分析自訂音檔並生成 AI 回應
    
    Args:
        file_path: 音檔路徑
        baseline_rate: 基準語速
        baseline_pitch: 基準音高
    """
    
    # 驗證檔案
    audio_file = Path(file_path)
    if not audio_file.exists():
        print(f"[ERROR] 檔案不存在：{file_path}")
        return False
    
    if audio_file.suffix.lower() not in ['.wav', '.mp3', '.flac', '.ogg']:
        print(f"[ERROR] 不支持的音檔格式：{audio_file.suffix}")
        return False
    
    print(f"\n{'='*60}")
    print("🎤 Voice Sentinel - 自訂音檔分析（含 AI 回應）")
    print(f"{'='*60}\n")
    
    print(f"📁 分析檔案：{audio_file.name}")
    print(f"📊 基準語速：{baseline_rate:.1f} 語句/秒")
    print(f"🎵 基準音高：{baseline_pitch:.1f}\n")
    
    # 建立分析器
    sentinel = VoiceSentinel(baseline_pitch=baseline_pitch, baseline_rate=baseline_rate, test=False)
    
    try:
        # 1. 分析音檔
        print("🔍 正在分析語音特徵...\n")
        features = sentinel.analyze_health_features(str(audio_file))
        
        # 顯示分析結果
        print(f"{'='*60}")
        print("📈 分析結果")
        print(f"{'='*60}\n")
        
        print(f"語速：{features['rate']:.2f} 語句/秒")
        print(f"音高穩定度：{features['pitch_std']:.2f}")
        print(f"判定：{'異常' if features['abnormal'] else '正常'}")
        print(f"信息：{features['msg']}\n")
        
        # 2. 生成 AI 回應
        print(f"{'='*60}")
        print("🤖 生成 AI 回應")
        print(f"{'='*60}\n")
        
        reply = await sentinel.get_ai_response(features)
        print(f"AI 回應：{reply}\n")
        
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] 分析失敗：{str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Voice Sentinel - 自訂音檔分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 基本分析
  python analyze_audio.py path/to/your/audio.wav
  
  # 帶 AI 回應的分析
  python analyze_audio.py path/to/your/audio.wav --ai
  
  # 自訂基準值
  python analyze_audio.py path/to/your/audio.wav --rate 4.0 --pitch 150
        """
    )
    
    parser.add_argument(
        "file",
        help="音檔路徑 (支持 .wav, .mp3, .flac, .ogg)"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="生成 AI 回應（需要 API Key）"
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=3.0,
        help="基準語速（默認：3.0 語句/秒）"
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=120,
        help="基準音高（默認：120）"
    )
    
    args = parser.parse_args()
    
    # 執行分析
    if args.ai:
        success = asyncio.run(analyze_with_ai(args.file, args.rate, args.pitch))
    else:
        success = analyze_custom_audio(args.file, args.rate, args.pitch)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
