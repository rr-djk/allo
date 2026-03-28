---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase2_auto_stop_20260328-0007.md"]
files_touched: ["ui.py", "record.py"]
related_to: null
---

# MicIcon — Brancher start_recording / stop_recording sur les événements souris

Connecter `start_recording()` et `stop_recording()` aux événements souris de `MicIcon`.

## Comportement attendu dans ui.py
- Ajouter `on_record_start=None` et `on_record_stop=None` à `MicIcon.__init__`
- `<ButtonPress-1>` : conserver le drag, puis appeler `on_record_start()` si non `None`
- `<ButtonRelease-1>` : appeler `on_record_stop()` si non `None`
- Docstring JSDoc mise à jour sur `__init__`

## Comportement attendu dans record.py
- Dans `main()` : instancier `MicIcon(on_record_start=start_recording, on_record_stop=stop_recording)`

## Contraintes
- Ne pas importer `record.py` depuis `ui.py`
- Le drag doit continuer à fonctionner
- Signaler si `ui.py` dépasse 150 lignes

## Livrable testable
`python3 record.py` : clic maintenu 1s + relâche → `/tmp/record_temp.wav` créé. Drag toujours fonctionnel.
