---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase1_micicon_window_20260328-0000.md"]
files_touched: ["ui.py"]
related_to: null
---

# MicIcon — Menu clic droit Quitter

Ajouter le menu contextuel clic droit dans la classe `MicIcon` de `ui.py`.

## Comportement attendu
- Événement `<Button-3>` : afficher un `tk.Menu` avec une seule entrée "Quitter"
- L'entrée "Quitter" appelle `self.destroy()` pour fermer l'application
- Ne pas toucher au drag & drop ni au reste de la classe

## Livrable testable
Clic droit sur l'icône affiche un menu "Quitter" qui ferme l'application.
