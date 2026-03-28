---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: []
files_touched: ["record.sh"]
related_to: null
---

# Créer le wrapper shell record.sh

Créer `/home/rr-djk/Documents/projets/allo/record.sh`.

## Comportement attendu
- Shebang `#!/bin/bash`
- Commentaire d'installation (sudo cp + chmod)
- Appel `python3 /home/rr-djk/Documents/projets/allo/record.py "$@"`
- Fichier rendu exécutable (`chmod +x`)

## Livrable testable
`./record.sh` lance l'application.
