---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase6B_etat-listening-ui_20260329-0906.md"]
files_touched: ["ui.py"]
related_to: null
---

# phase6B — Toggle écoute vocale dans le menu clic droit

Modifier `_show_context_menu` dans `MicIcon` pour ajouter l'entrée "Écoute vocale : OFF" / "Écoute vocale : ON". `MicIcon.__init__` accepte un paramètre optionnel `on_voice_listen_toggle(active: bool)`. Le callback est invoqué avec la nouvelle valeur à chaque basculement, dans le thread tkinter.
