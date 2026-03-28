---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase4_textbubble_skeleton_20260328-0015.md"]
files_touched: ["ui.py"]
related_to: null
---

# TextBubble — Widgets (label + boutons)

Ajouter le label texte et les boutons Copier/Fermer dans `TextBubble`.

## Comportement attendu
- `tk.Label` : `wraplength=_BUBBLE_MAX_WIDTH`, `justify="left"`, couleurs BG/FG, padding
- `tk.Frame` avec bouton "Copier" → méthode `_copy()` → `pyperclip.copy(text)`
- Bouton "Fermer" (libellé "X") → méthode `_close()` → `self.destroy()`
- `.pack()` pour label puis frame
- Docstrings JSDoc sur `_copy` et `_close`
