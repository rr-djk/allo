---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_detection-trigger_20260329-0905.md", "phase6B_toggle-menu_20260329-0907.md"]
files_touched: ["record.py"]
related_to: null
---

# phase6B — Intégration dans main()

Modifier `main()` dans `record.py` pour brancher le toggle sur `start_listening()` / `stop_listening()`, passer `on_trigger_detected` (stub pour l'instant), appeler `set_listening_state()` via `app.after(0, ...)`. Appeler `stop_listening()` dans `cleanup()`. Mode écoute désactivé par défaut au démarrage.
