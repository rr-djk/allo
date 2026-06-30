---
status: done
type: feature
priority: high
assigned_to: implementation-specialist
started_at: 2025-06-29T20:00:00
completed_at: 2025-06-29T20:35:00
depends_on: []
files_touched:
  - vad.py
  - record.py
  - requirements.txt
  - requirements-voice.txt
  - install.sh
  - Makefile
  - record.sh
  - README.md
related_to: null
---

# Simplifier l'installation

## Objectif
Rendre l'installation de l'application plus simple pour les utilisateurs techniques.

## Changements effectués
1. Rend torch optionnel dans vad.py (imports différés)
2. Ajoute is_voice_mode_available() pour détecter torch
3. Vérifie la disponibilité du voice mode dans record.py
4. Sépare les dépendances : requirements.txt (core) et requirements-voice.txt (optional)
5. Réécrit install.sh : installation utilisateur sans sudo, one-liner curl | bash
6. Met à jour Makefile avec target update
7. Supprime record.sh (remplacé par wrapper dynamique)
8. Simplifie README.md : one-liner, voice mode optional, troubleshooting

## Tests
- ✅ import record.py sans torch : succès
- ✅ vad.is_voice_mode_available() sans torch : False
- ✅ vad.start_listening() sans torch : échec gracieux
- ✅ Mode clic maintenu fonctionne sans torch
- ✅ Voice mode affiche message explicite quand torch absent
