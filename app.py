#!/usr/bin/env python
"""Voice Sentinel - Flask API Server"""

import subprocess
from static_ffmpeg import add_paths
add_paths()

def convert_to_wav(input_path):
    output_path = input_path.rsplit('.', 1)[0] + ".wav"
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        print("[FFMPEG ERROR]")
        print(result.stderr.decode())
        raise Exception("Audio conversion failed")

    return output_path

import os
import tempfile
from google import genai as _genai_module
from flask import Flask, request, jsonify
from flask_cors import CORS
from voice_sentinel import VoiceSentinel
from dotenv import load_dotenv

# Flask App Configuration
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Allowed audio formats
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'webm'}
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

sentinel = VoiceSentinel()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

load_dotenv()
_api_key = os.getenv("GOOGLE_API_KEY")
_genai_client = _genai_module.Client(api_key=_api_key) if _api_key else None


def _generate_ai(prompt: str) -> str:
    if not _genai_client:
        raise RuntimeError("No API key")
    return _genai_client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    ).text.strip()


BASELINE_PATH = os.path.join(RECORDINGS_DIR, "baseline.wav")

# Local engine instance
sentinel = VoiceSentinel(baseline_rate=3.0)


@app.route('/api/baseline/status', methods=['GET'])
def baseline_status():
    exists = os.path.exists(BASELINE_PATH)
    return jsonify({"exists": exists})


@app.route('/api/baseline/record', methods=['POST'])
def baseline_record():
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No audio file"}), 400
    audio_file = request.files['audio']
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name
    try:
        wav_path = convert_to_wav(temp_path)
        import shutil
        shutil.move(wav_path, BASELINE_PATH)
        sentinel.set_baseline(BASELINE_PATH)
        return jsonify({"status": "success", "message": "Baseline saved"})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Complete endpoint: Receives audio -> Local Analysis -> AI Response -> JSON
    """
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No audio file"}), 400

    audio_file = request.files['audio']
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        temp_path = temp_audio.name

    wav_path = None
    try:
        wav_path = convert_to_wav(temp_path)
        # Load baseline if available
        if os.path.exists(BASELINE_PATH) and sentinel._baseline_vector is None:
            sentinel.set_baseline(BASELINE_PATH)
        # 1. Run scientific local analysis
        metrics = sentinel.analyze_health(wav_path)

        # 2. Build AI Prompt based on metrics
        # We pass the data to Gemini to get a natural response
        rate = metrics.get('rate', 0)
        jitter = metrics.get('jitter', 0)
        hnr = metrics.get('hnr', 0)

        status_str = "fatigued/strained" if metrics["abnormal"] else "healthy"
        prompt = (
            f"As a health guardian AI, analyze these voice metrics: "
            f"Speech Rate: {rate}, Jitter: {jitter}, HNR: {hnr}. "
            f"The user sounds {status_str}. Provide a short (20 words), supportive response "
            f"encouraging them based on these findings."
        )
        
        # Generate AI response (fallback to static text if fails)
        try:
            ai_reply = _generate_ai(prompt)
        except:
            ai_reply = "Analysis complete. You seem a bit tired, please rest." if metrics["abnormal"] else "You sound great!"

        return jsonify({
            "status": "success",
            **metrics,
            "ai_response": ai_reply
        })

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


@app.route('/api/record-and-analyze', methods=['POST'])
def record_and_analyze():
    """
    Record audio from microphone and analyze (requires audio data)
    
    JSON Body:
      {
        "audio_data": Base64 encoded WAV data,
        "baseline_rate": 3.0,
        "baseline_pitch": 120,
        "include_ai": true
      }
    
    Returns: Same as /api/analyze
    """
    
    try:
        data = request.get_json()
        
        if 'audio_data' not in data:
            return jsonify({
                "status": "error",
                "message": "No audio_data provided"
            }), 400
        
        import base64
        audio_bytes = base64.b64decode(data['audio_data'])
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            filepath = tmp.name
        
        # Get parameters
        baseline_rate = float(data.get('baseline_rate', 3.0))
        baseline_pitch = float(data.get('baseline_pitch', 120))
        include_ai = data.get('include_ai', True)
        
        # Create sentinel and analyze
        local_sentinel = VoiceSentinel(
            baseline_rate=baseline_rate,
            test=False
        )
        
        analysis_result = local_sentinel.analyze_health(filepath)
        
        # Get AI response
        ai_response = ""
        if include_ai:
            try:
                ai_response = asyncio.run(
                    local_sentinel.get_ai_response(analysis_result)
                )
            except Exception as e:
                print(f"[WARNING] AI generation failed: {e}")
                ai_response = local_sentinel.fallback_response(analysis_result)
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
    "status": "success",
    "rate": round(float(analysis_result['rate']), 2),
    "pitch_std": round(float(analysis_result['pitch_std']), 2),
    "abnormal": bool(analysis_result['abnormal']),
    "msg": analysis_result['msg'],
    "ai_response": ai_response or ""
}), 200
        
    except Exception as e:
        print(f"[ERROR] Record and analyze failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """
    Test endpoint - returns mock analysis data
    Useful for testing frontend without real audio
    """
    
    import random
    
    rate = round(random.uniform(1.5, 4.0), 2)
    pitch_std = round(random.uniform(5, 80), 2)
    
    slow = rate < 2.0
    flat = pitch_std < 12
    abnormal = slow or flat
    
    if not abnormal:
        msg = "Normal state detected"
    elif slow:
        msg = "Speech rate too slow - possible fatigue"
    else:
        msg = "Flat tone, low energy"
    
    return jsonify({
        "status": "success",
        "rate": rate,
        "pitch_std": pitch_std,
        "abnormal": abnormal,
        "msg": msg,
        "ai_response": "You sound great! Keep up the good work." if not abnormal else "Why not take a break and have some water?"
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Voice Sentinel API is running",
        "version": "1.0"
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎤 Voice Sentinel - REST API Server")
    print("="*60)
    print("\n📍 Starting on http://localhost:5000")
    print("\n📚 API Endpoints:")
    print("   POST  /api/analyze           - Analyze uploaded audio")
    print("   POST  /api/record-and-analyze - Record and analyze")
    print("   GET   /api/test              - Test with mock data")
    print("   GET   /api/health            - Health check")
    print("\n💡 Frontend available at: file://./index.html")
    print("   Or serve with: python -m http.server 8000")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
