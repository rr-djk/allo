---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase3_transcribe_subprocess_20260328-0009.md"]
files_touched: ["record.py"]
related_to: null
---

# _parse_whisper_output() — Nettoyage du texte

Ajouter `_parse_whisper_output(raw: str) -> str` dans `record.py`.

## Comportement attendu
- Supprime les horodatages `[HH:MM:SS.mmm --> HH:MM:SS.mmm]` via regex
- Supprime les balises `<...>` via regex
- Retourne le texte stripped
- Retourne une chaîne vide si rien ne reste
- Utilise uniquement `re`
- Docstring JSDoc
