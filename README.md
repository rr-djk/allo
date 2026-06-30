![Project cover](images/couverture.png)

# 🎤 record

Minimal local voice dictation tool for Linux.
Floating microphone icon — hold to record, release to transcribe.
Built as a lightweight UI wrapper around [**faster-whisper**](https://github.com/SYSTRAN/faster-whisper).

**Platform:** Ubuntu / Debian

---

## 🚀 Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/rr-djk/allo/main/install.sh | bash
record &
```

> The first transcription automatically downloads the faster-whisper models (~225 MB).
> Requirements: Ubuntu / Debian, internet connection for the first run.

---

## 🤖 What's installed by default

| Model | Engine | Purpose | Size | When downloaded |
|-------|--------|---------|------|----------------|
| `tiny` (multilingual) | faster-whisper | Wake word detection | ~75 MB | First launch |
| `small` (multilingual) | faster-whisper | Main transcription | ~150 MB | First launch |

Models are downloaded automatically from HuggingFace on first launch.

To customize models or language, see [Customization](#customization) below.

---

## 🧠 How it works

**Click mode (default):**

1. Hold left click → icon turns **blue**, recording starts
2. Release → icon turns **green** (pulsing), transcription starts
3. Text appears in a bubble
4. Click "Copy" → paste anywhere

**Voice mode (wake word):**

1. Right-click the icon → "Voice listening: ON"
2. Icon turns **amber** — waiting for the wake word
3. Say "nadia" → icon turns **blue**, recording starts automatically
4. Speak your dictation
5. After ~1.5s of silence → icon turns **green** (pulsing), transcription starts automatically
6. Text appears in the bubble, copied to clipboard

---

## 🎮 Usage

| Action | Effect |
|--------|--------|
| `record &` | Start the application in the background |
| `record --update` | Update to the latest version |
| Hold left click | Start recording (auto-stops after 90s) |
| Release | Stop + transcribe |
| Click "copy" | Copy text |
| Click "close" | Close bubble |
| Right-click → "Voice listening: ON/OFF" | Toggle voice listening mode |
| _(voice mode)_ Icon turns amber | Waiting for wake word |
| _(voice mode)_ Say "nadia" | Icon turns blue, recording starts |
| _(voice mode)_ Silence detected | Icon turns green (pulsing), transcription starts |
| Right click | Quit app |

---

## 🎨 Icon states

| State | Icon |
|-------|------|
| Idle | grey |
| Voice listening active (waiting for wake word) | amber |
| Recording | blue |
| Transcribing (Whisper processing) | green (pulsing) |

---

## 📁 Project structure

```
allo/
├── record.py
├── audio.py
├── vad.py
├── config.py
├── ui.py
├── install.sh
├── Makefile
├── requirements.txt
├── benchmarks/
```

---

## 🎛️ Customization

This section covers optional configuration. The app works out of the box without any of this.

### Language

By default the app is configured for **French** — both wake word detection and transcription run with `language="fr"`.

To switch to English:

```bash
export ALLO_LANGUAGE=en
```

Add to `~/.zshrc` or `~/.bashrc` to make permanent.

> In English mode, the main transcription model switches automatically to `small.en` (English-only, slightly faster). The wake word remains "nadia" — say it with an English accent.

### Models

Set environment variables before launching:

```bash
export FASTER_WHISPER_TINY=base    # wake word detection (default: tiny)
export FASTER_WHISPER_MAIN=medium  # main transcription (default: small)
```

Add to `~/.zshrc` or `~/.bashrc` to make permanent.

Available models: `tiny`, `base`, `small`, `medium`, `large-v3`, and their `.en` variants.

### Wake word detection accuracy

The `tiny` model keeps latency low but detection can be imperfect:
- You may need to say "nadia" once or twice
- Background noise can reduce reliability

For better accuracy at the cost of speed:

```bash
export FASTER_WHISPER_TINY=base
```

---

## 🎙️ Voice mode (optional)

Voice mode uses the wake word "nadia" and requires **PyTorch** (~200 MB). By default, voice mode is disabled and the app works in click-and-hold mode.

To enable voice mode:

```bash
~/.local/share/allo/.venv/bin/pip install -r ~/.local/share/allo/requirements-voice.txt
```

Then relaunch the app and activate **"Voice listening"** via the right-click context menu.

---

## 🔧 Manual installation

```bash
git clone https://github.com/rr-djk/allo.git ~/.local/share/allo
cd ~/.local/share/allo && ./install.sh
```

---

## 🛟 Troubleshooting

| Problem | Solution |
|---------|----------|
| `record: command not found` | Add `export PATH="$HOME/.local/bin:$PATH"` to your shell rc (`~/.bashrc` or `~/.zshrc`) |
| Missing system dependencies | `sudo apt-get install python3-tk python3-venv libportaudio2` |
| Voice mode unavailable | Install PyTorch using the command in the [Voice mode](#voice-mode-optional) section |
