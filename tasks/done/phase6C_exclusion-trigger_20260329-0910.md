---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_integration-main_20260329-0908.md"]
files_touched: ["record.py"]
related_to: null
---

# phase6C — Exclusion du wake word du transcript

Ajouter dans `record.py` la fonction `_strip_wake_word(text: str) -> str` qui supprime toute occurrence de `WAKE_WORD` du texte (insensible à la casse, espaces nettoyés). Appliquer uniquement sur les transcriptions déclenchées par le mode écoute vocale. Le mode clic maintenu n'est pas affecté.
