# 🎤 Projet : record (outil minimal de dictée locale avec Whisper)

## 🎯 Objectif

Construire une application minimaliste qui permet :

1. Lancer `record` depuis le terminal (en arrière-plan)
2. Afficher une icône micro flottante à l’écran
3. Enregistrer la voix uniquement pendant un clic maintenu
4. À la relâche :
   - arrêter l’enregistrement
   - envoyer l’audio à Whisper
   - afficher le texte dans une bulle
5. Copier facilement le texte
6. Fermer la bulle
7. Quitter l’application via clic droit

⚠️ Important :
- Whisper est utilisé tel quel (pas modifié)
- L’application est uniquement un wrapper UX autour de Whisper

---

## ⚙️ Stack technique (imposée)

- Python 3 (Linux Ubuntu/Debian uniquement)
- tkinter (UI)
- sounddevice (audio)
- scipy.io.wavfile (écriture WAV)
- pyperclip (clipboard)
- subprocess (appel whisper-cli)

---

## 🏗️ Architecture

### Structure de fichiers

```
record/
├── record.py   # Config + logique métier (audio, whisper) + main loop
└── ui.py       # Toute l'UI tkinter (MicIcon + TextBubble)
```

### Composants

| Module | Responsabilité |
|--------|----------------|
| `record.py` | Constantes de config, `start_recording()`, `stop_recording()`, `transcribe()` (subprocess whisper-cli), `main()` |
| `ui.py` | Classe `MicIcon` (fenêtre flottante, drag, animation, clic droit), classe `TextBubble` (texte, bouton Copier, bouton Fermer) |

> Règle : si un fichier dépasse 150 lignes, on extrait à ce moment-là — pas avant.

### Flux

```
MicIcon (clic gauche) → start_recording()
MicIcon (relâche) → stop_recording() → transcribe() → TextBubble.show()
```

### Notes

- Utiliser `threading` pour ne pas bloquer l'UI pendant Whisper (obligatoire)
- Animation via `tkinter.after()` pour le cercle pulsant

---

## 📦 Dépendances Python

```bash
pip install sounddevice scipy pyperclip
```

---

## 🔧 Installation (Linux Ubuntu/Debian)

### Étape 1 — Dépendances système

```bash
sudo apt update && sudo apt install python3-tk cmake build-essential
pip install sounddevice scipy pyperclip
```

### Étape 2 — Installer whisper.cpp (pré-requis, non géré par ce projet)

Voir : https://github.com/ggml-org/whisper.cpp?tab=readme-ov-file

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
sh ./models/download-ggml-model.sh base.en
cmake -B build
cmake --build build -j --config Release
```

Le binaire sera disponible à : `whisper.cpp/build/bin/whisper-cli`
Le modèle sera disponible à : `whisper.cpp/models/ggml-base.en.bin`

### Étape 3 — Récupérer les fichiers du projet

Cloner ou copier `record.py` et `ui.py` dans un répertoire de son choix (ex: `~/record/`).

### Étape 4 — Configurer les chemins

Ouvrir `record.py` et éditer les constantes en haut du fichier :

```python
WHISPER_BINARY = "/chemin/absolu/vers/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL  = "/chemin/absolu/vers/whisper.cpp/models/ggml-base.en.bin"
TEMP_WAV       = "/tmp/record_temp.wav"
MAX_DURATION   = 90    # secondes
MIN_DURATION   = 0.5   # secondes
```

### Étape 5 — Créer le wrapper shell

```bash
sudo tee /usr/local/bin/record > /dev/null <<EOF
#!/bin/bash
python3 /chemin/absolu/vers/record/record.py "\$@"
EOF
sudo chmod +x /usr/local/bin/record
```

### Étape 6 — Lancer

```bash
record &
```

---

> **Amélioration future :** un script `install.sh` pourra automatiser les étapes 3 à 5 (copie des fichiers, édition des chemins, création du wrapper).

---

## 🧠 Comportement global

### Lancement

Commande :

```bash
record &
```

Effet :
- L’application démarre en arrière-plan
- Une icône micro apparaît à l’écran

**Installation de la commande `record` :**

Un wrapper shell est fourni pour rendre `record` accessible en commande terminal :

```bash
#!/bin/bash
# /usr/local/bin/record
python3 /chemin/vers/record/record.py "$@"
```

```bash
chmod +x /usr/local/bin/record
```

---

## 🖥️ UI — Icône micro

Caractéristiques :
- Petite fenêtre (~50x50)
- Toujours visible (always on top)
- Sans bordure
- Déplaçable (drag & drop)

### Interactions :

#### Clic gauche maintenu
→ DÉBUT enregistrement audio

#### Relâche clic gauche
→ FIN enregistrement
→ Whisper traite l'audio (animation autour de l'icône)
→ Bulle affichée avec le texte

#### Clic droit
→ afficher option "Quitter"
→ fermer application

### Animation pendant transcription

Pendant que Whisper traite l'audio :
- L'icône micro affiche une animation visuelle (ex: cercle pulsant, changement de couleur)
- Une fois le texte reçu, l'animation s'arrête et la bulle apparaît

---

## 🎧 Enregistrement audio

### Début (mouse down)
- démarrer capture micro
- fréquence : 16000 Hz
- mono
- durée minimale : 0.5 secondes
- durée maximale : 90 secondes (arrêt automatique si dépassé)

### Fin (mouse up ou durée max atteinte)
- arrêter capture
- sauvegarder dans `/tmp/record_temp.wav`

---

## 🔁 Traitement après enregistrement

Pipeline strict :

1. Audio enregistré (si durée >= 0.5s)
2. Sauvegarde dans `/tmp/record_temp.wav`
3. Appel whisper-cli via subprocess :

```bash
whisper-cli -m ggml-base.en.bin -f /tmp/record_temp.wav
```

4. Récupération du texte depuis stdout (horodatages et balises nettoyés)
5. Si erreur ou texte vide : afficher le message retourné par whisper-cli dans la bulle
6. Suppression automatique de `/tmp/record_temp.wav` après transcription

---

## 💬 UI — Bulle de texte

Après transcription :

- Une seule bulle par session (la bulle existante est remplacée si un nouvel enregistrement est effectué)
- Position : juste en dessous de l’icône micro (repositionnée si débordement en bas d’écran)

### Contenu :

- Texte transcrit (ou message d’erreur Whisper)
- Bouton “Copier”
- Bouton “Fermer” (X)

---

## 📋 Clipboard

Le texte transcrit est affiché dans la bulle. Le bouton "Copier" permet de copier le texte dans le presse-papier :

```python
pyperclip.copy(text)
```


---

## ❌ Fermeture de la bulle

- Bouton X
- Ferme uniquement la bulle
- L’application continue de tourner

---

## 🛑 Fermeture de l’application

- Clic droit sur l’icône micro
- Option “Quitter”
- Arrêt complet du processus

---

## 🔄 Flux complet

1. Lancer `record`
2. Icône micro visible
3. Maintenir clic gauche
4. Parler
5. Relâcher clic
6. Audio sauvegardé
7. Whisper exécuté
8. Texte généré
9. Bulle affichée avec bouton Copier
10. Fermer bulle
11. Continuer ou quitter

---

## ⚠️ Contraintes

- Pas de streaming
- Pas de hotkeys clavier
- Pas d’optimisation performance
- Pas d’UI avancée

---

## ✅ Definition of Done

Le projet est terminé si :

- L’icône micro apparaît
- L’enregistrement fonctionne au clic maintenu
- La transcription fonctionne
- La bulle affiche le texte avec bouton Copier
- La bulle se ferme
- L’application se ferme via clic droit

---

## 🚫 Hors scope

- Améliorations UX
- Support GPU
- Interface avancée
- Packaging
- Historique

---

## 🧠 Note finale

Ce projet est volontairement minimal.

Objectif :
→ obtenir un outil fonctionnel rapidement
→ sans complexité inutile
→ basé sur Whisper existant
