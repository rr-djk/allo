---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_integration-main_20260329-0908.md"]
files_touched: ["vad.py"]
related_to: null
---

# phase6C — Arrêt automatique par détection de silence

Modifier `vad.py` pour que, après détection du trigger, Silero VAD surveille la fin de parole et déclenche `on_silence_detected` après `SILENCE_DURATION` secondes de silence consécutif. Le stream VAD est fermé avant l'ouverture du stream d'enregistrement. `MAX_DURATION` reste le filet de sécurité.
