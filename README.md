# 🎤 record

Minimal local voice dictation tool for Linux.
Floating microphone icon — hold to record, release to transcribe.

Built as a lightweight UI wrapper around [**faster-whisper**](https://github.com/SYSTRAN/faster-whisper).

**Platform:** Ubuntu / Debian

---

## 🚀 Quick Start

```bash
git clone https://github.com/rr-djk/allo allo
cd allo
make setup   # installs system dependencies, Python dependencies, record command
record &
```

> The first transcription automatically downloads the faster-whisper models (~150 MB).
> Requirements: Ubuntu / Debian, internet connection for the first run.

---

## 🔧 Detailed installation

`make setup` runs `install.sh` which automates the following steps:

1. System dependencies (`python3-tk`, `python3-venv`, `libportaudio2`)
2. Create a Python venv and install dependencies (`pip install -r requirements.txt`)
3. Install the `record` command into `/usr/local/bin/`

For a manual installation or a custom layout, see the **Prerequisites** and **Configuration** sections below.

---

## 🤖 Models

`make setup` installs the following by default:

| Model | Engine | Purpose | Size | When downloaded |
|-------|--------|---------|------|----------------|
| `tiny` (multilingual) | faster-whisper | Wake word detection | ~75 MB | First launch |
| `small.en` | faster-whisper | Main transcription | ~480 MB | First launch |

Models are downloaded automatically from HuggingFace on first launch.

### Changing models

Set environment variables before launching:

```bash
export FASTER_WHISPER_TINY=base        # wake word detection (default: tiny)
export FASTER_WHISPER_MAIN=medium.en   # main transcription (default: small.en)
```

Add to `~/.zshrc` or `~/.bashrc` to make permanent.

Available models: `tiny`, `base`, `small`, `medium`, `large-v3`, and their `.en` variants.

### Wake word detection accuracy

The `tiny` model keeps latency low but detection can be imperfect:
- You may need to say "allo record" once or twice
- Background noise can reduce reliability

For better accuracy at the cost of speed:

```bash
export FASTER_WHISPER_TINY=small
```

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
3. Say "allo record" → icon turns **blue**, recording starts automatically
4. Speak your dictation
5. After ~1.5s of silence → icon turns **green** (pulsing), transcription starts automatically
6. Text appears in the bubble, copied to clipboard

---

## ⚙️ Prerequisites

### 1. System dependencies

```bash
sudo apt update
sudo apt install python3-tk python3-venv libportaudio2
```

---

### 2. PyTorch (voice mode only)

Voice mode uses Silero VAD, which requires PyTorch. It is included in `requirements.txt`, but the package is large (~200MB).

If you do not need voice mode, you can skip installing `torch` and `torchaudio`.

---

### 4. Pillow

The icon images are PNG files resized at startup via Pillow. It is included in `requirements.txt` and installs automatically.

---

## 📦 Installation

### 1. Clone project

```bash
git clone https://github.com/rr-djk/allo allo
cd allo
```

---

### 2. Python dependencies

```bash
pip install -r requirements.txt
```

Optional (recommended):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## ⚙️ Configuration

### record command (optional)

Before installing, edit `record.sh` to match your environment:

**1. Shebang** — adjust line 1 to your shell:

```sh
#!/usr/bin/env zsh   # zsh (default)
#!/bin/bash          # bash
#!/bin/sh            # POSIX sh
```

**2. Python interpreter** — adjust to point to the Python that has the dependencies installed:

```sh
# System Python (if dependencies installed globally)
python3 /absolute/path/to/allo/record.py "$@"

# Virtual environment (if dependencies installed in .venv)
/absolute/path/to/allo/.venv/bin/python3 /absolute/path/to/allo/record.py "$@"
```

If unsure, you can skip this step and run `python3 record.py` directly.

Then install:

```bash
sudo cp record.sh /usr/local/bin/record
sudo chmod +x /usr/local/bin/record
```

Then run:

```bash
record &
```

---

## 🎮 Usage

| Action | Effect |
|------|--------|
| `make run` | Start the application in the background |
| Hold left click | Start recording (auto-stops after 90s) |
| Release | Stop + transcribe |
| Click "copy" | Copy text |
| Click "close" | Close bubble |
| Right-click → "Voice listening: ON/OFF" | Toggle voice listening mode |
| _(voice mode)_ Icon turns amber | Waiting for wake word |
| _(voice mode)_ Say "allo record" | Icon turns blue, recording starts |
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
├── record.sh
├── install.sh
├── Makefile
├── requirements.txt
```

---

## 🧠 Notes

- Fully local (no API calls)
- Uses faster-whisper for transcription
- Voice mode uses Silero VAD for activity detection and faster-whisper for wake word + transcription — fully local, no network calls
- Simple MVP — no streaming, no advanced features
