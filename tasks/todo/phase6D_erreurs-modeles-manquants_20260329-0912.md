---
status: todo
type: feature
priority: medium
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6C_pipeline-complet_20260329-0911.md"]
files_touched: ["vad.py", "record.py"]
related_to: null
---

# phase6D — Gestion erreur modèles manquants

Dans `start_listening()`, vérifier l'existence de `WHISPER_BINARY` et `WHISPER_MODEL_TINY` avant d'ouvrir le stream. Si absent, retourner un message d'erreur. Dans `main()`, afficher via `show_bubble()` et remettre le toggle en état OFF. Aucun stream laissé ouvert.
