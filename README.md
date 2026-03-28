# 🎤 record

Minimal local voice dictation tool for Linux.
Floating microphone icon — hold to record, release to transcribe.

Built as a lightweight UI wrapper around [**whisper.cpp**](https://github.com/ggml-org/whisper.cpp?tab=readme-ov-file).

**Platform:** Ubuntu / Debian

---

## 🚀 Quick Start

> ⚠️ For the best experience, follow the full **Prerequisites** and **Installation** sections before running the app. The steps below assume everything is already set up.

```bash
git clone https://github.com/rr-djk/allo allo
cd allo

pip install -r requirements.txt

python3 record.py
```

👉 A microphone icon should appear on your screen.

---

## 🧠 How it works

1. Hold left click → record your voice
2. Release → transcription starts
3. Text appears in a bubble
4. Click "Copy" → paste anywhere

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

If your layout is different, edit the constants at the top of `record.py` with absolute paths:

```python
WHISPER_BINARY = "/absolute/path/to/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL  = "/absolute/path/to/whisper.cpp/models/ggml-base.en.bin"
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
| Hold left click | Start recording (auto-stops after 90s) |
| Release | Stop + transcribe |
| Click "copy" | Copy text |
| Click "close" | Close bubble |
| Right click | Quit app |

---

## 📁 Project structure

```
allo/
├── record.py
├── record.sh
├── ui.py
└── requirements.txt
```

---

## 🧠 Notes

- Fully local (no API calls)
- Uses whisper.cpp for transcription
- Simple MVP — no streaming, no advanced features
