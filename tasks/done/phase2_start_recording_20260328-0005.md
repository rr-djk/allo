---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase2_audio_constants_20260328-0004.md"]
files_touched: ["record.py"]
related_to: null
---

# record.py — Implémenter start_recording()

Ajouter la fonction `start_recording()` dans `record.py`.

## Comportement attendu
- Démarre un `sounddevice.InputStream` avec `samplerate=SAMPLE_RATE`, `channels=CHANNELS`, `dtype='int16'`
- Accumule les blocs audio reçus dans une liste module-level `_audio_frames`
- Réinitialise `_audio_frames` à chaque appel
- Ne bloque pas l'appelant
- Docstring JSDoc

## Livrable testable
Appeler `start_recording()` puis `time.sleep(1)` : `_audio_frames` contient des blocs numpy non vides.
