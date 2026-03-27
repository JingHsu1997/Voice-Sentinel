# Voice Sentinel — API Documentation

## System Overview

**Project:** Voice Sentinel  
**Description:** Voice health monitoring app that detects fatigue via Voice Correlation (Vc) and dysphonia parameters, with optional Google Gemini AI recommendations.  
**Stack:** Python + Flask REST API + HTML/JS frontend

---

## Core Module

### `VoiceSentinel` class (`voice_sentinel.py`)

```python
VoiceSentinel(
    baseline_rate: float = 3.0,   # legacy param, kept for compatibility
    baseline_pitch: float = 120.0, # legacy param, kept for compatibility
    test: bool = False             # test mode — uses synthetic audio, no mic/API needed
)
```

#### `set_baseline(file_path: str)`
Loads a rested-state WAV file and stores its 36-D MFCC vector as the Vc baseline.

#### `analyze_health(file_path: str) -> dict`
Main analysis method. Returns:
```json
{
  "vc": 0.87,
  "fatigue_level": "Mild fatigue",
  "jitter_local": 0.8321,
  "shimmer_local": 2.1045,
  "hnr_db": 12.4,
  "pitch_sd": 34.5,
  "pause_ratio": 0.12,
  "score": 45.0,
  "need_ai": true,
  "bio_summary": "Composite score: 45.0/100 (Moderate fatigue)\nAlerts: Weak amplitude control",
  "abnormal": true,
  "msg": "Mild fatigue detected (Vc ≈ 0.82 at ~27 h awake)",
  "baseline_set": false
}
```

Fatigue classification (Vc thresholds, Greeley et al. 2007):

| Vc | Level |
|----|-------|
| ≥ 0.90 | Rested |
| 0.60 – 0.89 | Mild fatigue |
| < 0.60 | Severe fatigue |

#### `async get_ai_response(analysis: dict) -> str`
Calls Gemini 2.5 Flash with the Vc result. Returns a short empathetic recommendation (≤ 60 words). Falls back to a local string if API is unavailable or `need_ai` is False.

#### `async speak(text: str)`
Converts text to speech via Edge TTS (`en-US-AriaNeural`) and plays it back with pygame.

#### `record_audio() -> str`
Records 5 seconds from the microphone (or generates synthetic audio in test mode). Returns the saved WAV path.

---

## REST API Endpoints (`app.py`)

### `GET /api/baseline/status`
Returns whether a baseline file exists.
```json
{ "exists": true }
```

### `POST /api/baseline/record`
Upload a rested-state audio recording to set as baseline.
- Body: `multipart/form-data`, field `audio` (webm/wav/ogg)
- Response: `{ "status": "success", "message": "Baseline saved" }`

### `POST /api/analyze`
Upload an audio file for full analysis + AI response.
- Body: `multipart/form-data`, field `audio`
- Response: all fields from `analyze_health()` plus `"ai_response": "..."`

### `POST /api/record-and-analyze`
Accepts base64-encoded WAV audio for analysis.
```json
{
  "audio_data": "<base64 WAV>",
  "baseline_rate": 3.0,
  "include_ai": true
}
```
Response: all fields from `analyze_health()` plus `"ai_response": "..."`

### `GET /api/test`
Returns mock analysis data for frontend testing (no audio required).

### `GET /api/health`
Health check. Returns `{ "status": "ok" }`.

---

## Configuration

### `.env`
```
GOOGLE_API_KEY=your_api_key_here
```

### Constants (`voice_sentinel.py`)
```python
FS = 16000       # sample rate (Hz)
DURATION = 5     # recording length (seconds)
```

---

## File Structure

```
├── voice_sentinel.py      # Core VoiceSentinel class
├── analyze_audio.py       # CLI tool for analyzing existing audio files
├── start.py               # Interactive CLI session runner
├── app.py                 # Flask REST API server
├── index.html             # Web frontend
├── requirements.txt       # Python dependencies
├── .env                   # API key
└── docs/
    └── API_DOCUMENTATION.md
```

---

## Dependencies

```
numpy, librosa, sounddevice, soundfile
praat-parselmouth          # Jitter / Shimmer / Pitch via Praat
google-genai               # Gemini API
edge-tts, pygame           # TTS playback
flask, flask-cors          # REST API
static_ffmpeg              # Audio format conversion
python-dotenv
```

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Gemini not initialized` | Missing API key | Add `GOOGLE_API_KEY` to `.env` |
| `sounddevice failed` | No microphone | Use `--test` mode or upload a file |
| `Audio conversion failed` | ffmpeg error | Check input file format |

Fallback chain: Gemini timeout → `fallback_response()` → local string based on `abnormal` flag.
