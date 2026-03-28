---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: []
files_touched: ["record.py"]
related_to: null
---

# Audio — Constantes SAMPLE_RATE et CHANNELS

Ajouter les constantes nommées `SAMPLE_RATE` et `CHANNELS` dans `record.py`.

## Comportement attendu
- `SAMPLE_RATE = 16000` (fréquence d'échantillonnage en Hz)
- `CHANNELS = 1` (mono)
- Positionnées dans le bloc de constantes existant, après `TEMP_WAV`
- Chaque constante accompagnée d'un commentaire inline

## Livrable testable
`python3 -c "import record; assert record.SAMPLE_RATE == 16000; assert record.CHANNELS == 1"` ne lève aucune erreur.
