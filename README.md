# 🎤 record

Minimal local voice dictation tool for Linux.
Floating microphone icon — hold to record, release to transcribe.

Built as a lightweight UI wrapper around [**whisper.cpp**](https://github.com/ggml-org/whisper.cpp?tab=readme-ov-file).

**Platform:** Ubuntu / Debian

---

## 🚀 Quick Start

```bash
git clone https://github.com/rr-djk/allo allo
cd allo
make setup   # installs everything (whisper.cpp, models, Python dependencies, record command)
record &
```

> The first transcription automatically downloads the faster-whisper models (~150 MB).
> Requirements: Ubuntu / Debian, internet connection for the first run.

---

## 🔧 Detailed installation

`make setup` runs `install.sh` which automates the following steps:

1. System dependencies (`python3-tk`, `cmake`, `build-essential`, `libportaudio2`)
2. Clone and build **whisper.cpp** into `third_party/whisper.cpp/`
3. Download the `ggml-tiny.bin` model (wake word detection)
4. Create a Python venv and install dependencies (`pip install -r requirements.txt`)
5. Install the `record` command into `/usr/local/bin/`

For a manual installation or a custom layout, see the **Prerequisites** and **Configuration** sections below.

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
sudo apt install python3-tk cmake build-essential libportaudio2
```

---

### 2. whisper.cpp (required)

Clone and build whisper.cpp:

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

sh ./models/download-ggml-model.sh base.en

cmake -B build
cmake --build build -j --config Release
```

After build:

- Binary: `whisper.cpp/build/bin/whisper-cli`
- Model: `whisper.cpp/models/ggml-base.en.bin`

**Model recommendations:**

- `base.en` is sufficient for click-to-record mode.
- For voice wake word detection, **`small.en` is the minimum recommended model** for a tolerable experience:

  ```bash
  sh ./models/download-ggml-model.sh small.en
  ```

  Then update `WHISPER_MODEL` in `record.py` to point to `ggml-small.en.bin`.

- Better wake word accuracy with `medium.en` or higher, at the cost of speed.

---

### 3. PyTorch (voice mode only)

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

### Whisper paths

By default, `record.py` resolves whisper.cpp paths relative to its own location via `__file__`. The default values (`../../whisper.cpp/...`) expect this directory structure:

```
<parent>/
├── whisper.cpp/
└── <any>/
    └── allo/        ← this project (2 levels above whisper.cpp)
```

Example that works out of the box:

```
~/Documents/
├── whisper.cpp/
└── projets/
    └── allo/
```

If your layout is different, you have two options:

**Option A — environment variables (recommended):**

```bash
export WHISPER_BINARY=/absolute/path/to/whisper.cpp/build/bin/whisper-cli
export WHISPER_MODEL=/absolute/path/to/whisper.cpp/models/ggml-small.en.bin
```

Add these to your `~/.zshrc` or `~/.bashrc` to make them permanent.

**Option B — edit `record.py` directly:**

```python
WHISPER_BINARY = "/absolute/path/to/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL  = "/absolute/path/to/whisper.cpp/models/ggml-small.en.bin"
```

---

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
└── third_party/       ← whisper.cpp (generated by install.sh, ignored by git)
```

---

## 🧠 Notes

- Fully local (no API calls)
- Uses whisper.cpp for transcription
- Voice mode uses Silero VAD for wake word detection and Whisper for transcription — fully local, no network calls
- Simple MVP — no streaming, no advanced features
