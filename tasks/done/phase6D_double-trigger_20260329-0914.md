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

# phase6D — Ignorer double trigger

Dans le callback `on_trigger_detected`, vérifier `_transcription_running` avant de démarrer le pipeline. Si une transcription est déjà en cours, ignorer silencieusement. Utiliser `_transcription_lock` existant. Aucune exception, aucun stream supplémentaire, aucune bulle dupliquée.
