---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase3_error_handling_20260328-0011.md"]
files_touched: ["record.py"]
related_to: null
---

# transcribe() — Suppression de TEMP_WAV

Ajouter la suppression de TEMP_WAV après transcription dans `transcribe()`.

## Comportement attendu
- Bloc `finally` : `os.remove(TEMP_WAV)` dans un `try/except OSError`
- `import os` en tête de fichier
- Aucune exception ne se propage depuis le nettoyage

## Livrable testable
Après transcription, `/tmp/record_temp.wav` n'existe plus.
