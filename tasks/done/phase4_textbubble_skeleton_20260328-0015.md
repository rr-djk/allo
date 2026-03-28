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

# TextBubble — Squelette de la classe

Ajouter la classe `TextBubble(tk.Toplevel)` dans `ui.py` avec les constantes de style.

## Comportement attendu
- Constantes : `_BUBBLE_BG = "#2b2b2b"`, `_BUBBLE_FG = "#f0f0f0"`, `_BUBBLE_PADDING = 8`, `_BUBBLE_MAX_WIDTH = 320`
- Classe `TextBubble(tk.Toplevel)` après `MicIcon`
- `__init__(self, parent, text)` : sans bordure, always on top, fond `_BUBBLE_BG`
- `import pyperclip` si absent
- Docstrings JSDoc

## Livrable testable
`TextBubble(app, "test")` ne lève pas d'exception.
