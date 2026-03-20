"""
Voice Sentinel - 結果解釋演示腳本
這個腳本展示如何理解和解釋分析結果
"""

import json
from datetime import datetime

class AnalysisResultInterpreter:
    """Analysis result interpreter"""
    
    def __init__(self):
        self.baseline_rate = 3.0  # Baseline speech rate
        self.baseline_pitch_std = 50  # Baseline pitch stability
    
    def interpret_results(self, analysis_results):
        """Interpret analysis results"""
        rate = analysis_results.get('rate', 0)
        pitch_std = analysis_results.get('pitch_std', 0)
        abnormal = analysis_results.get('abnormal', False)
        msg = analysis_results.get('msg', '')
        
        print("\n" + "="*60)
        print("VOICE ANALYSIS RESULT INTERPRETATION")
        print("="*60)
        
        # Speech rate analysis
        print(f"\nSpeech Rate Analysis")
        print(f"  Current: {rate:.2f} intervals/sec")
        print(f"  Baseline: {self.baseline_rate:.2f} intervals/sec")
        
        rate_percentage = (rate / self.baseline_rate) * 100 if self.baseline_rate > 0 else 0
        print(f"  Relative to baseline: {rate_percentage:.1f}%")
        
        if rate >= self.baseline_rate * 0.7:
            print(f"  Status: NORMAL (reached {rate_percentage:.1f}% of baseline)")
        else:
            print(f"  Status: ABNORMAL (below baseline by {100-rate_percentage:.1f}%)")
            print(f"  Possible reasons: Fatigue, confusion, relaxation")
        
        # Pitch stability analysis
        print(f"\nPitch Stability Analysis")
        print(f"  Current: {pitch_std:.2f}")
        print(f"  Baseline: > 10 (recommended)")
        
        if pitch_std >= 10:
            print(f"  Status: NORMAL (voice has variation, rich expression)")
        else:
            print(f"  Status: ABNORMAL (flat tone)")
            print(f"  Possible reasons: Low energy, depressed mood, poor mental state")
        
        # Overall assessment
        print(f"\nOVERALL ASSESSMENT")
        print(f"  Abnormal flag: {'YES' if abnormal else 'NO'}")
        print(f"  Message: {msg}")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS")
        if abnormal:
            if rate < self.baseline_rate * 0.7 and pitch_std < 10:
                print("  - You sound very tired. Consider resting or eating to restore energy")
                print("  - Try some light, relaxing activities")
            elif rate < self.baseline_rate * 0.7:
                print("  - Your speech rate is slow, may need rest")
                print("  - Drink water, stretch, recover energy")
            elif pitch_std < 10:
                print("  - Your tone is flat, may indicate poor mental state")
                print("  - Try singing or reading aloud to activate your voice")
        else:
            print("  - Your voice is in great shape!")
            print("  - Keep up this state")
        
        print("\n" + "="*60 + "\n")
        
        return {
            'rate_status': 'normal' if rate >= self.baseline_rate * 0.7 else 'abnormal',
            'pitch_status': 'normal' if pitch_std >= 10 else 'abnormal',
            'overall_status': 'normal' if not abnormal else 'abnormal'
        }
    
    def save_results(self, analysis_results, filename="analysis_log.json"):
        """Save analysis results to log"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_results
        }
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            print(f"[INFO] Results saved to {filename}")
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")
    
    def compare_results(self, results_list):
        """Compare multiple test results"""
        if not results_list:
            print("[ERROR] No results to compare")
            return
        
        print("\n" + "="*60)
        print("MULTIPLE TEST RESULTS COMPARISON")
        print("="*60 + "\n")
        
        rates = [r.get('rate', 0) for r in results_list]
        pitch_stds = [r.get('pitch_std', 0) for r in results_list]
        
        print(f"Average speech rate: {sum(rates)/len(rates):.2f} intervals/sec")
        print(f"Speech rate range: {min(rates):.2f} - {max(rates):.2f}")
        print(f"\nAverage pitch stability: {sum(pitch_stds)/len(pitch_stds):.2f}")
        print(f"Pitch stability range: {min(pitch_stds):.2f} - {max(pitch_stds):.2f}")
        print("\n" + "="*60 + "\n")


# Demo usage
if __name__ == "__main__":
    interpreter = AnalysisResultInterpreter()
    
    # Example 1: Normal state
    print("\n[Example 1] Normal State")
    result_normal = {
        'rate': 3.5,
        'pitch_std': 45.3,
        'abnormal': False,
        'msg': 'Normal'
    }
    interpreter.interpret_results(result_normal)
    
    # Example 2: Fatigue state
    print("[Example 2] Fatigue State")
    result_tired = {
        'rate': 1.8,
        'pitch_std': 8.5,
        'abnormal': True,
        'msg': 'Speech rate too slow - possible fatigue or confusion'
    }
    interpreter.interpret_results(result_tired)
    
    # Example 3: Flat tone
    print("[Example 3] Flat Tone")
    result_flat = {
        'rate': 3.2,
        'pitch_std': 5.2,
        'abnormal': True,
        'msg': 'Flat tone - low energy'
    }
    interpreter.interpret_results(result_flat)
    
    # Compare results
    print("[Example 4] Compare Multiple Tests")
    results_comparison = [result_normal, result_tired, result_flat]
    interpreter.compare_results(results_comparison)
