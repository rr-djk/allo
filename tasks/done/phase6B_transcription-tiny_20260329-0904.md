---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6A_ajout-constantes_20260329-0900.md"]
files_touched: ["record.py"]
related_to: null
---

# phase6B — Fonction transcribe_tiny()

Ajouter dans `record.py` la fonction `transcribe_tiny(wav_path: str) -> str` qui appelle `whisper-cli` avec `WHISPER_MODEL_TINY` sur un fichier WAV fourni et retourne le texte nettoyé. Réutilise `_parse_whisper_output()`. Ne supprime pas `TEMP_WAV`. Gère les erreurs binaire/modèle manquant.
