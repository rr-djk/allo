---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase4_textbubble_position_20260328-0017.md"]
files_touched: ["ui.py"]
related_to: null
---

# MicIcon — show_bubble() : une seule bulle par session

Garantir qu'une seule `TextBubble` existe à la fois.

## Comportement attendu
- Attribut `self._bubble = None` dans `MicIcon.__init__`
- Méthode `show_bubble(self, text)` : si `_bubble` existe et `winfo_exists()`, la détruire ; créer `self._bubble = TextBubble(self, text)`
- Docstring JSDoc sur `show_bubble`
