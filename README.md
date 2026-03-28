# record

Minimal local voice dictation tool for Linux. Floating microphone icon — hold to record, release to transcribe. UI wrapper around [whisper.cpp](https://github.com/ggml-org/whisper.cpp).

**Platform:** Ubuntu / Debian only.

---

## Prerequisites

### 1. System dependencies

```bash
sudo apt update && sudo apt install python3-tk cmake build-essential libportaudio2
```

### 2. whisper.cpp

Clone and build whisper.cpp **before** setting up this project.

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
sh ./models/download-ggml-model.sh base.en
cmake -B build
cmake --build build -j --config Release
```

After the build:

- Binary: `whisper.cpp/build/bin/whisper-cli`
- Model: `whisper.cpp/models/ggml-base.en.bin`

---

## Installation

### 1. Clone this project

```bash
git clone <repo-url> allo
```

### 2. Python dependencies

```bash
pip install -r requirements.txt
```

Using a virtual environment (recommended):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Configuration

#### `record.py` — Whisper paths

At the top of `record.py`, `WHISPER_BINARY` and `WHISPER_MODEL` are resolved relative to `record.py` itself via `__file__`:

```python
_BASE = os.path.dirname(os.path.abspath(__file__))

WHISPER_BINARY = os.path.join(_BASE, "../../whisper.cpp/build/bin/whisper-cli")
WHISPER_MODEL  = os.path.join(_BASE, "../../whisper.cpp/models/ggml-base.en.bin")
```

The default values (`../../whisper.cpp/...`) work without any change if `whisper.cpp` was cloned at the same level as the parent directory of this project:

```
~/
├── whisper.cpp/
└── allo/          ← this project
```

If your layout differs, update `WHISPER_BINARY` and `WHISPER_MODEL` to the correct absolute paths.

#### `record.sh` — Shell and Python interpreter

Two things to adjust before installing the wrapper:

**Shebang** — change line 1 to match your shell:

```sh
#!/bin/bash        # for bash
#!/usr/bin/env zsh # for zsh (current default)
#!/bin/sh          # for POSIX sh
```

**Python interpreter** — line 3 must point to the Python that has the dependencies installed:

```sh
# System Python (if dependencies installed globally)
python3 /absolute/path/to/allo/record.py "$@"

# Virtual environment (if dependencies installed in .venv)
/absolute/path/to/allo/.venv/bin/python3 /absolute/path/to/allo/record.py "$@"
```

### 4. Install the `record` command

```bash
sudo cp record.sh /usr/local/bin/record
sudo chmod +x /usr/local/bin/record
```

---

## Usage

Launch in the background:

```bash
record &
```

A floating microphone icon appears on screen.

| Action | Effect |
|---|---|
| Hold left click | Start recording |
| Release left click | Stop recording, run transcription, show text bubble |
| Click "Copy" | Copy transcribed text to clipboard |
| Click "X" | Close the text bubble (app keeps running) |
| Right click on icon | Show "Quit" option, exit the application |

The icon is draggable. A visual animation plays on the icon while Whisper is processing.

---

## Project structure

```
allo/
├── record.py   # Configuration constants, audio capture, transcription, main loop
├── record.sh   # Shell wrapper for the record command
├── ui.py       # tkinter UI: MicIcon, TextBubble
└── requirements.txt
```
