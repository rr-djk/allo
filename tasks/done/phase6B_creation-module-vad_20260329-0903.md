---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_extraction-module-vad_20260329-0902.md"]
files_touched: ["vad.py"]
related_to: null
---

# phase6B — Création du module vad.py

Créer `vad.py` avec : chargement du modèle Silero VAD via `torch.hub`, `start_listening(on_trigger_detected)` qui ouvre un `sounddevice.InputStream` en arrière-plan et accumule un buffer court, `stop_listening()` qui ferme proprement le stream. Aucun stream ouvert à l'import.
