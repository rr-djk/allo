---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_extraction-module-vad_20260329-0902.md"]
files_touched: ["audio.py", "record.py"]
related_to: null
---

# phase6B — Création du module audio.py

Extraire la gestion du stream sounddevice de `record.py` vers un nouveau module `audio.py`.

`audio.py` doit exporter :
- `open_stream(callback)` — ouvre un `sd.InputStream` 16kHz mono int16. Lève `RuntimeError` si un stream est déjà ouvert.
- `close_stream()` — ferme le stream courant. Idempotent.
- `is_stream_open()` — retourne `True` si un stream est ouvert.
- `frames_to_wav(frames, path)` — concatène des blocs numpy et écrit un fichier WAV.

Mettre à jour `record.py` pour que `start_recording()`, `stop_recording()` et `cancel_recording()` utilisent `audio.open_stream()` / `audio.close_stream()` / `audio.frames_to_wav()` au lieu de manipuler `sd.InputStream` directement.

`audio.py` n'importe ni `record.py`, ni `vad.py`, ni `ui.py`.
