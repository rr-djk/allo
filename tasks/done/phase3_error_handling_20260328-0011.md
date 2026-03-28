---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase3_parse_whisper_output_20260328-0010.md"]
files_touched: ["record.py"]
related_to: null
---

# transcribe() — Gestion des erreurs

Modifier `transcribe()` pour couvrir les 4 cas d'erreur.

## Comportement attendu
1. `WHISPER_BINARY` inexistant → retourner `"Erreur : binaire whisper-cli introuvable"`
2. `WHISPER_MODEL` inexistant → retourner `"Erreur : modèle Whisper introuvable"`
3. Code de retour non-zero → retourner `"Erreur whisper-cli : <stderr>"`
4. Texte nettoyé vide → retourner `"(aucun texte transcrit)"`
- Retourne toujours une str non-None
- Docstring JSDoc mise à jour avec @returns et @note
