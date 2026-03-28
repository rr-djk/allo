---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase3_cleanup_temp_wav_20260328-0012.md"]
files_touched: ["record.py"]
related_to: null
---

# run_transcription() — Thread de transcription

Ajouter `run_transcription(on_result)` dans `record.py`.

## Comportement attendu
- Lance `transcribe()` dans un `threading.Thread(daemon=True)`
- Une fois terminé, appelle `on_result(texte)`
- Retourne immédiatement sans bloquer
- Docstring JSDoc avec @param on_result
