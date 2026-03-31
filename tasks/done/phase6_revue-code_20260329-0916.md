---
status: todo
type: review
priority: high
assigned_to: code-reviewer
started_at: null
depends_on: ["phase6D_erreurs-modeles-manquants_20260329-0912.md", "phase6D_quit-en-cours-ecoute_20260329-0913.md", "phase6D_double-trigger_20260329-0914.md", "phase6D_conflit-clic-voix_20260329-0915.md"]
files_touched: ["record.py", "ui.py", "vad.py"]
related_to: null
---

# phase6 — Revue de code globale

Vérifier la cohérence globale de la Phase 6 : thread-safety (tous appels UI via `app.after(0, ...)`), absence de stream sounddevice simultané, règle 150 lignes par fichier, docstrings présentes, aucun import circulaire entre `record.py` et `vad.py`. Produire un rapport listant les non-conformités ou confirmer explicitement la conformité.
