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

# MicIcon — Fenêtre de base

Créer `ui.py` avec la classe `MicIcon` héritant de `tk.Tk`.

## Comportement attendu
- Fenêtre 50x50 pixels
- Sans bordure (`overrideredirect(True)`)
- Always on top (`wm_attributes("-topmost", True)`)
- Canvas 50x50 avec un ovale représentant l'icône micro

## Livrable testable
`python3 ui.py` affiche une petite fenêtre ronde, sans bordure, toujours au premier plan.
