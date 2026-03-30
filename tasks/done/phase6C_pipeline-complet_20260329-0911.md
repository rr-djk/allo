---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6C_arret-automatique-silence_20260329-0909.md", "phase6C_exclusion-trigger_20260329-0910.md"]
files_touched: ["record.py", "vad.py"]
related_to: null
---

# phase6C — Pipeline complet écoute vocale

Connecter le pipeline complet dans `main()` : trigger → fermer stream VAD → `start_recording()` → silence → `stop_recording()` → `run_transcription()` avec `_strip_wake_word()` → `show_bubble()`. Réactiver l'écoute VAD après affichage de la bulle si le mode est toujours actif. Animation pulsante pendant la transcription.
