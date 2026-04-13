

# Voice Sentinel

**Voice Sentinel** helps you monitor your vocal health and fatigue using your own voice. Record or upload speech, get instant analysis, and receive AI-powered recommendations. Perfect for teachers, broadcasters, call center staff, singers, or anyone who relies on their voice.

---

## Features

- **Fatigue detection** from your voice
- **Jitter, Shimmer, HNR** acoustic analysis
- **AI recommendations** (Google Gemini integration)
- **Easy-to-use**: microphone, audio file, or web interface

---

## Quickstart

1. **Install dependencies**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
2. *(Optional)* Add your Google API key to `.env` for AI recommendations:
  ```env
  GOOGLE_API_KEY=your_api_key_here
  ```
3. **Run a test analysis** (no mic or API key needed):
  ```powershell
  python voice_sentinel.py --test
  ```
4. **Live analysis** (microphone required):
  ```powershell
  python voice_sentinel.py
  ```
5. **Analyze an audio file**:
  ```powershell
  python analyze_audio.py recordings/your_voice.wav
  ```
6. **Web interface**:
  ```powershell
  python app.py
  ```

---

## How It Works

Voice Sentinel analyzes your speech for signs of fatigue using the Voice Correlation (Vc) metric, and provides additional acoustic parameters (Jitter, Shimmer, HNR) for reference. With a Google Gemini API key, you also get a short, empathetic AI recommendation based on your results.

For technical details and algorithm references, see [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

---

## License

MIT

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

### Fatigue detection — Voice Correlation (Vc)

The primary fatigue metric is **Voice Correlation (Vc)**, based on the method proposed by Greeley et al. in *"Fatigue Estimation Using Voice Analysis"* (2007).

A 36-dimensional characteristic voice vector is extracted from each recording: 12 MFCCs + 12 delta-MFCCs + 12 delta-delta-MFCCs, mean-pooled over frames using a 25 ms Hamming window at 16 kHz. Vc is then computed as the Pearson correlation between the current recording's vector and a rested-state baseline.

| Vc value | Interpretation |
|----------|----------------|
| ≥ 0.90 | Rested |
| 0.60 – 0.89 | Mild fatigue (~27 h awake) |
| < 0.60 | Severe fatigue (~66 h awake) |

The first recording automatically becomes the baseline. A dedicated rested-state baseline can be set via `--baseline`.

### Dysphonia parameters — Jitter, Shimmer, HNR

Three acoustic perturbation parameters are computed as supplementary reference metrics, based on the formulas and pathological thresholds defined in Teixeira et al., *"Vocal Acoustic Analysis — Jitter, Shimmer and HNR Parameters"* (2013), and the speaker recognition application described in Farrús et al., *"Jitter and Shimmer Measurements for Speaker Recognition"* (2007).

| Parameter | Formula | Pathological threshold |
|-----------|---------|------------------------|
| **Jitter (local)** | `mean(|T_i − T_{i+1}|) / mean(T) × 100` | > 1.04% |
| **Shimmer (local)** | `mean(|A_i − A_{i+1}|) / mean(A) × 100` | > 3.81% |
| **HNR** | `10 · log₁₀(AC(T) / (AC(0) − AC(T)))` | < 7 dB |

> These parameters are displayed for reference only. Because they are designed for sustained vowel phonation rather than natural continuous speech, they are not used in the abnormality classification.

### AI recommendation

When a Google Gemini API key is configured, the Vc score and fatigue level are sent to the model with a structured prompt. The model returns a short, empathetic recommendation in under 60 words. The response is converted to speech via Edge TTS and played back.

### Output format

```json
{
  "vc": 0.87,
  "fatigue_level": "Mild fatigue",
  "jitter_local": 0.8321,
  "shimmer_local": 2.1045,
  "hnr_db": 12.4,
  "abnormal": true,
  "msg": "Mild fatigue detected (Vc ≈ 0.82 at ~27 h awake)"
}
```

## References

- Greeley, H. P., et al. (2007). *Fatigue Estimation Using Voice Analysis*.
- Teixeira, J. P., et al. (2013). *Vocal Acoustic Analysis — Jitter, Shimmer and HNR Parameters*.
- Farrús, M., et al. (2007). *Jitter and Shimmer Measurements for Speaker Recognition*.