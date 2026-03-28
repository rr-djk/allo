---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase4_textbubble_widgets_20260328-0016.md"]
files_touched: ["ui.py"]
related_to: null
---

# TextBubble — Positionnement sous l'icône micro

Calculer et appliquer la position de la bulle dans une méthode `_place(self, parent)`.

## Comportement attendu
- `self.update_idletasks()` avant calcul
- `x = parent.winfo_x()`, `y = parent.winfo_y() + parent.winfo_height() + 4`
- Si `y + self.winfo_reqheight() > self.winfo_screenheight()` : repositionner au-dessus `y = parent.winfo_y() - self.winfo_reqheight() - 4`
- `self.geometry(f"+{x}+{y}")`
- Appeler `_place(parent)` depuis `__init__`
