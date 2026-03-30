---
status: todo
type: feature
priority: medium
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6C_pipeline-complet_20260329-0911.md"]
files_touched: ["record.py", "vad.py", "ui.py"]
related_to: null
---

# phase6D — Gestion conflit clic maintenu / écoute vocale

Garantir qu'un clic maintenu pendant que le stream VAD est actif ferme d'abord le stream VAD avant d'ouvrir le stream d'enregistrement. Après la transcription, rouvrir le stream VAD si le mode écoute est encore actif. Si un enregistrement clic est en cours, le trigger VAD est ignoré.
