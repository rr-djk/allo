---
status: todo
type: feature
priority: medium
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6C_pipeline-complet_20260329-0911.md"]
files_touched: ["record.py", "vad.py"]
related_to: null
---

# phase6D — Quit propre pendant écoute vocale active

S'assurer que `cleanup()` appelle `stop_listening()` de manière non-bloquante et sans exception si le stream est déjà fermé. `stop_listening()` doit être idempotent. Quitter l'application via clic droit pendant le mode écoute ne laisse ni exception ni thread bloquant.
