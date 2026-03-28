---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase5_animation-micicon_20260328-0020.md"]
files_touched: ["record.py"]
related_to: null
---

# main() — Brancher l'animation sur le cycle de transcription

Modifier `main()` dans `record.py` pour démarrer/stopper l'animation.

## Comportement attendu
- Dans `_on_stop()`, si `success is True`, ajouter `app.after(0, app.start_animation)` avant `run_transcription`
- Dans le callback `on_result`, modifier le lambda pour appeler `stop_animation()` avant `show_bubble(text)` :
  `lambda text: app.after(0, lambda: (app.stop_animation(), app.show_bubble(text)))`
- Si `success is False` : aucune animation démarrée

## Livrable testable
Animation démarre à la relâche du clic, s'arrête quand la bulle apparaît.
