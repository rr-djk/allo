---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_detection-trigger_20260329-0905.md"]
files_touched: ["vad.py"]
related_to: null
---

# phase6B — Fuzzy matching pour la détection du wake word

Remplacer la comparaison exacte `WAKE_WORD.lower() in text.lower()` dans `_process_segment()` par une correspondance floue.

Avec un accent français, Whisper transcrit parfois "allo record" en "Alo record", "Hello record", "Allow record", etc. La détection exacte échoue dans ces cas.

## Approche

Utiliser `difflib.SequenceMatcher` pour calculer un ratio de similarité entre le texte transcrit et `WAKE_WORD`. Déclencher le wake word si le ratio dépasse un seuil (ex. 0.6).

La comparaison doit être insensible à la casse et ne comparer que la portion du texte la plus proche du wake word (pas tout le transcript).

## Contraintes

- Aucune dépendance externe supplémentaire (`difflib` est dans la stdlib)
- Le seuil de similarité doit être une constante nommée dans `vad.py`
- Conserver la comparaison exacte comme premier test (rapide) avant le fuzzy
- Rester sur la branche `feature/voice-reco`
