---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase1_micicon_window_20260328-0000.md"]
files_touched: ["ui.py"]
related_to: null
---

# MicIcon — Drag & drop

Ajouter le drag & drop dans la classe `MicIcon` de `ui.py`.

## Comportement attendu
- Événement `<ButtonPress-1>` : stocker la position initiale du clic
- Événement `<B1-Motion>` : recalculer et mettre à jour la position de la fenêtre
- Ne pas toucher au reste de la classe

## Livrable testable
L'icône micro peut être déplacée par clic maintenu + glisser.
