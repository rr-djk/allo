---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: []
files_touched: ["record.py"]
related_to: null
---

# transcribe() — Appel subprocess whisper-cli

Ajouter `transcribe()` dans `record.py` qui appelle whisper-cli via subprocess et retourne le stdout brut.

## Comportement attendu
- `subprocess.run([WHISPER_BINARY, "-m", WHISPER_MODEL, "-f", TEMP_WAV], capture_output=True, text=True)`
- Retourne le stdout brut (str)
- Docstring JSDoc

## Livrable testable
Après `start_recording()` + relâche + `transcribe()` : le stdout de whisper-cli s'affiche.
