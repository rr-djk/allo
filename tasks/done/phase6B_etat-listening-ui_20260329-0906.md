---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_extraction-module-vad_20260329-0902.md"]
files_touched: ["ui.py"]
related_to: null
---

# phase6B — État visuel "listening" sur MicIcon

Ajouter dans `ui.py` la constante `_MIC_COLOR_LISTENING` (couleur distincte, ex. `#d4a017`) et la méthode `set_listening_state(active: bool)` sur `MicIcon`. Change la couleur en `_MIC_COLOR_LISTENING` si `active=True`, sinon `_MIC_COLOR_IDLE`. Thread-safe via `app.after(0, ...)`.
