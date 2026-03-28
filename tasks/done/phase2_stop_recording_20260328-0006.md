---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase2_start_recording_20260328-0005.md"]
files_touched: ["record.py"]
related_to: null
---

# record.py — Implémenter stop_recording()

Ajouter la fonction `stop_recording()` dans `record.py`.

## Comportement attendu
- Arrête et ferme le `sounddevice.InputStream` ouvert par `start_recording()`
- Concatène les blocs de `_audio_frames` en un seul tableau numpy
- Calcule la durée réelle : `len(frames) / SAMPLE_RATE`
- Si durée < `MIN_DURATION` : ne pas écrire le fichier, retourner `False`
- Si durée >= `MIN_DURATION` : écrire dans `TEMP_WAV` via `scipy.io.wavfile.write`, retourner `True`
- Gérer le cas où `_audio_frames` est vide (retourner `False` sans exception)
- Docstring JSDoc avec @returns {bool}

## Livrable testable
Après `start_recording()` + 1s + `stop_recording()` : `/tmp/record_temp.wav` existe et est lisible.
