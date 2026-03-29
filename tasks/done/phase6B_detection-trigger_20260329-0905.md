---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_creation-module-vad_20260329-0903.md", "phase6B_transcription-tiny_20260329-0904.md"]
files_touched: ["vad.py"]
related_to: null
---

# phase6B — Détection du trigger dans vad.py

Ajouter dans `vad.py` la logique de détection : écrire le segment audio dans `/tmp/allo_trigger.wav`, appeler `transcribe_tiny()`, et si `WAKE_WORD` est trouvé (insensible à la casse) invoquer le callback `on_trigger_detected`. Supprimer `/tmp/allo_trigger.wav` après chaque appel.
