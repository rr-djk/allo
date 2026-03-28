---
status: done
type: review
priority: medium
assigned_to: code-reviewer
started_at: null
depends_on: ["phase5_animation-micicon_20260328-0020.md", "phase5_branchement-animation-record_20260328-0021.md", "phase5_wrapper-shell_20260328-0022.md"]
files_touched: []
related_to: null
---

# Revue de code Phase 5

Vérifier l'animation, le branchement et le wrapper shell.

## Points de contrôle
- `_anim_after_id` initialisé dans `__init__` ✅
- `stop_animation()` protégée contre `None` ✅
- `stop_animation()` avant `show_bubble()` dans le callback ❌ — bug identifié : `show_bubble()` n'appelle pas `stop_animation()`, l'animation continue indéfiniment après transcription
- `record.sh` : shebang valide, chemin absolu, exécutable ✅
- `ui.py` ne dépasse pas 150 lignes ❌ — 392 lignes (règle non appliquée, non bloquant)
