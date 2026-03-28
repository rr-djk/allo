---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase4_textbubble_singleton_20260328-0018.md"]
files_touched: ["record.py"]
related_to: null
---

# main() — Brancher TextBubble via app.after

Remplacer le `print` par l'affichage de la bulle dans `record.py`.

## Comportement attendu
- Dans `_on_stop()`, remplacer `run_transcription(on_result=lambda text: print(text))` par :
  `run_transcription(on_result=lambda text: app.after(0, lambda: app.show_bubble(text)))`
- Supprimer tout `print(text)` résiduel

## Livrable testable
Flux complet : clic → parler → relâcher → bulle avec texte, bouton Copier, bouton Fermer.
