# Voice Sentinel

A voice health monitoring application that records audio, analyzes speech rate and pitch stability, and generates AI-powered recommendations using Google Gemini.

---

## Installation

**Requirements:** Python 3.8+, Windows/macOS/Linux

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

If `sounddevice` fails on Windows:

```powershell
pip install pipwin
pipwin install sounddevice
```

### 3. Configure API key (optional)

Create or edit the `.env` file in the project root:

```
GOOGLE_API_KEY=your_api_key_here
```

An API key is only required for AI-generated recommendations. All acoustic analysis works without one.

---

## Running the Application

### Test mode (no microphone or API key required)

```powershell
python voice_sentinel.py --test
```

Runs a full pipeline using a synthetic audio signal. Completes in approximately 5-10 seconds. Recommended for verifying your installation.

### Live mode

```powershell
python voice_sentinel.py
```

Records 5 seconds of speech from your microphone, analyzes it, and plays back an AI-generated response. Requires a microphone, a valid API key, and an internet connection.

### Analyze an existing audio file

```powershell
# Acoustic analysis only
python analyze_audio.py recordings/your_voice.wav

# With AI recommendation
python analyze_audio.py recordings/your_voice.wav --ai

# With a rested-state baseline for Vc comparison
python analyze_audio.py recordings/test.wav --baseline recordings/rested.wav
```

Supported formats: `.wav`, `.mp3`, `.flac`, `.ogg`

### Web interface

```powershell
python app.py
```

Starts a Flask server. Open `index.html` in a browser to use the web frontend.

---

## How It Works

### Acoustic feature extraction

The application extracts two primary features from each recording:

- **Speech rate (`rate`)** — the number of voiced segments per second, estimated by detecting energy onsets in the audio signal. A higher value indicates faster, more energetic speech.
- **Pitch standard deviation (`pitch_std`)** — the standard deviation of the fundamental frequency (F0) across voiced frames, measured in Hz. A higher value indicates greater pitch variation, which correlates with vocal expressiveness and alertness.

### Anomaly detection

A recording is flagged as abnormal when either of the following conditions is met:

| Condition | Threshold | Interpretation |
|-----------|-----------|----------------|
| `rate` below baseline | < 70% of baseline | Possible fatigue or reduced alertness |
| `pitch_std` below floor | < 10 Hz | Flat, monotone delivery; low vocal energy |

Default baseline values are `rate = 3.0` and `pitch = 120 Hz`. These can be personalized by running several recordings during a well-rested state and computing the average.

### AI recommendation

When a Google Gemini API key is configured, the analysis result is sent to the model along with a structured prompt. The model returns a short, context-aware recommendation based on the detected speech pattern. The response is then converted to speech via text-to-speech and played back.

### Output format

```json
{
  "rate": 3.5,
  "pitch_std": 45.3,
  "abnormal": false,
  "msg": "Normal"
}
```