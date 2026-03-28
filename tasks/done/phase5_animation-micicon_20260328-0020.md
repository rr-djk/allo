---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: []
files_touched: ["ui.py"]
related_to: null
---

# MicIcon — Animation pulsante pendant la transcription

Ajouter `start_animation()` et `stop_animation()` à `MicIcon`.

## Comportement attendu
- Attribut `self._anim_after_id = None` dans `__init__`
- `start_animation()` : dessine un ovale pulsant (tag "pulse") via `tkinter.after` (~120ms), stocke l'id dans `_anim_after_id`
- `stop_animation()` : annule le rappel si `_anim_after_id is not None`, supprime le tag "pulse" du canvas, remet `_anim_after_id = None`
- Pas d'exception si `stop_animation()` appelée sans animation active
- Docstrings JSDoc sur les deux méthodes

## Livrable testable
Animation visible à l'oeil nu sur l'icône pendant `start_animation()`.
