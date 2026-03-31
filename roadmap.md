# 🎤 Projet : record (outil minimal de dictée locale avec Whisper)

## 🎯 Objectif

Construire une application minimaliste qui permet :

1. Lancer `record` depuis le terminal (en arrière-plan)
2. Afficher une icône micro flottante à l'écran
3. Enregistrer la voix uniquement pendant un clic maintenu
4. À la relâche :
   - arrêter l'enregistrement
   - envoyer l'audio à Whisper
   - afficher le texte dans une bulle
5. Copier facilement le texte
6. Fermer la bulle
7. Quitter l'application via clic droit

⚠️ Important :
- Whisper est utilisé tel quel (pas modifié)
- L'application est uniquement un wrapper UX autour de Whisper

---

## ⚙️ Stack technique (imposée)

- Python 3 (Linux Ubuntu/Debian uniquement)
- tkinter (UI)
- sounddevice (audio)
- scipy.io.wavfile (écriture WAV)
- pyperclip (clipboard)
- subprocess (appel whisper-cli)
- torch / torchaudio (Silero VAD)

---

## 🏗️ Architecture

### Structure de fichiers

```
record/
├── record.py   # Config + logique métier (audio, whisper) + main loop
├── audio.py    # Propriétaire exclusif du stream sounddevice
├── vad.py      # Écoute passive VAD + détection wake word
└── ui.py       # Toute l'UI tkinter (MicIcon + TextBubble)
```

### Composants

| Module | Responsabilité |
|--------|----------------|
| `record.py` | Constantes de config, `start_recording()`, `stop_recording()`, `cancel_recording()`, `transcribe()`, `transcribe_tiny()`, `run_transcription()`, `main()` |
| `audio.py` | Propriétaire exclusif du `sd.InputStream` : `open_stream()`, `close_stream()`, `is_stream_open()`, `frames_to_wav()` |
| `vad.py` | Chargement Silero VAD, écoute passive, détection wake word via Whisper tiny, détection de silence post-wake-word : `start_listening()`, `stop_listening()`, `start_silence_detection()`, `stop_silence_detection()` |
| `ui.py` | Classe `MicIcon` (fenêtre flottante, drag, animation, clic droit, toggle écoute vocale), classe `TextBubble` (texte, bouton Copier, bouton Fermer) |

> Règle : si un fichier dépasse 150 lignes, on extrait à ce moment-là — pas avant.

### Flux

```
MicIcon (clic gauche) → start_recording()
MicIcon (relâche) → stop_recording() → transcribe() → TextBubble.show()

MicIcon (écoute vocale ON) → vad.start_listening()
vad détecte wake word → on_wake_word() → start_recording()
vad.start_silence_detection() → silence détecté → stop_recording() → transcribe() → TextBubble.show()
```

### Notes

- Utiliser `threading` pour ne pas blocker l'UI pendant Whisper (obligatoire)
- Animation via `tkinter.after()` pour le cercle pulsant

---

## 📦 Dépendances Python

```bash
pip install sounddevice scipy pyperclip torch torchaudio
```

---

## 🔧 Installation (Linux Ubuntu/Debian)

### Étape 1 — Dépendances système

```bash
sudo apt update && sudo apt install python3-tk cmake build-essential libportaudio2
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

> **Important (à documenter dans le README) :** `WHISPER_BINARY` et `WHISPER_MODEL` doivent être mis à jour par l'utilisateur selon l'endroit où il a cloné le dépôt whisper.cpp. Des chemins relatifs sont acceptables si l'application est toujours lancée depuis le même répertoire.

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

### Étape 7 — Phase 6 : écoute vocale

Installer PyTorch (requis par Silero VAD) :

```bash
pip install torch torchaudio
```

Télécharger le modèle Whisper tiny (utilisé pour la détection du mot déclencheur) :

```bash
cd whisper.cpp
sh ./models/download-ggml-model.sh tiny.en
```

Le modèle sera disponible à : `whisper.cpp/models/ggml-tiny.en.bin`

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
- L'application démarre en arrière-plan
- Une icône micro apparaît à l'écran

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
- Position : juste en dessous de l'icône micro (repositionnée si débordement en bas d'écran)

### Contenu :

- Texte transcrit (ou message d'erreur Whisper)
- Bouton "Copier"
- Bouton "Fermer" (X)

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
- L'application continue de tourner

---

## 🛑 Fermeture de l'application

- Clic droit sur l'icône micro
- Option "Quitter"
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

## 🚀 Phases d'implémentation

### Phase 1 — Fenêtre micro visible et déplaçable ✅
- Créer `ui.py` avec la classe `MicIcon` : fenêtre 50x50, sans bordure, always on top
- Drag & drop fonctionnel
- Clic droit → menu "Quitter" → fermeture
- Créer `record.py` avec `main()` qui lance la fenêtre

**Livrable testable :** `python3 record.py` affiche une icône déplaçable qu'on peut fermer au clic droit.

---

### Phase 2 — Enregistrement audio au clic maintenu ✅
- Ajouter `start_recording()` et `stop_recording()` dans `record.py`
- Capturer le micro via `sounddevice` (16kHz, mono)
- Sauvegarder en WAV via `scipy.io.wavfile`
- Brancher sur les événements mouse down / mouse up de `MicIcon`
- Respecter durée min (0.5s) et max (90s)

**Livrable testable :** maintenir le clic produit un fichier `/tmp/record_temp.wav` lisible dans n'importe quel lecteur audio.

---

### Phase 3 — Transcription Whisper ✅
- Ajouter `transcribe()` dans `record.py` : appel subprocess à `whisper-cli`
- Parser stdout, nettoyer horodatages
- Gérer les erreurs (binaire absent, modèle absent, texte vide)
- Exécuter dans un `threading.Thread` pour ne pas bloquer tkinter
- Supprimer le WAV après transcription

**Livrable testable :** après relâche du clic, le texte transcrit s'affiche dans le terminal (`print`).

---

### Phase 4 — Bulle de texte + copie ✅
- Ajouter la classe `TextBubble` dans `ui.py`
- Positionnement sous l'icône micro (avec gestion débordement écran)
- Boutons "Copier" (`pyperclip.copy`) et "Fermer" (X)
- Remplacement de la bulle existante si nouvel enregistrement

**Livrable testable :** flux complet — clic, parler, relâcher, bulle avec texte, copier, fermer.

---

### Phase 5 — Animation + wrapper shell ✅
- Animation cercle pulsant sur l'icône pendant la transcription (`tkinter.after`)
- Arrêt de l'animation à l'apparition de la bulle
- Création du wrapper shell `/usr/local/bin/record`

**Livrable testable :** produit correspond à la Definition of Done, commande `record` disponible en terminal.

> **Important (à documenter dans le README) :** le shebang de `record.sh` (`#!/usr/bin/env zsh`) doit être ajusté selon le shell de l'utilisateur avant installation (ex. `#!/bin/bash` pour bash, `#!/bin/sh` pour POSIX).

> **Important (à documenter dans le README) :** si les dépendances Python ne sont pas installées sur le système global, mettre à jour le chemin de l'interpréteur dans `record.sh` pour pointer vers le Python du venv (ex. `/chemin/vers/allo/.venv/bin/python3`).

> **Amélioration future :** un script `install.sh` pourra automatiser la création du wrapper (étapes 3 à 5 de l'installation).

---

### Phase 6 — Mot de déclenchement ("allo record") ✅

Lancement de l'enregistrement à la voix, sans clic. L'outil écoute en permanence en arrière-plan et démarre l'enregistrement dès qu'il détecte la phrase "allo record". L'enregistrement s'arrête automatiquement après 1.5 secondes de silence, puis transcrit.

**Vision :** outil universel de dictée vocale — pas une intégration spécifique à Claude. Le texte transcrit est copié dans le presse-papier et peut être collé dans n'importe quel outil : Claude Code, OpenCode, Cursor, ou autre.

#### Architecture

```
🎤 Micro (sounddevice, 16kHz mono)
   ↓
🟢 Silero VAD  →  détecte début / fin de parole
   ↓
🟡 Buffer court (1–2s)
   ↓
🔵 Whisper tiny (whisper.cpp, ggml-tiny.en.bin)
   ↓
if "allo record" détecté :
    → enregistrement complet
    → Whisper base (ggml-base.en.bin)
    → TextBubble + clipboard
```

#### Nouveaux modules

| Module | Responsabilité |
|--------|----------------|
| `audio.py` | Propriétaire exclusif du stream sounddevice (extrait de `record.py`) |
| `vad.py` | Écoute passive Silero VAD, détection wake word, détection de silence post-wake-word |

#### Nouvelles constantes dans `record.py`

```python
WHISPER_MODEL_TINY = "/chemin/vers/whisper.cpp/models/ggml-tiny.en.bin"
WAKE_WORD          = "allo record"
SILENCE_DURATION   = 1.5   # secondes
```

#### Comportement

- Mode écoute vocale désactivé par défaut au démarrage
- Activé/désactivé via le menu clic droit : "Écoute vocale : OFF" / "Écoute vocale : ON"
- La phrase "allo record" est exclue du texte transcrit
- Le clic maintenu reste disponible en parallèle à tout moment

#### États de l'icône micro

| État | Visuel |
|---|---|
| Écoute vocale inactive | gris |
| En attente du trigger | visuel distinct (couleur ou animation) |
| Enregistrement actif | bleu |
| Transcription en cours | animation pulsante |

**Livrable testable :** dire "allo record" déclenche un enregistrement, le silence l'arrête, la bulle affiche le texte transcrit sans le wake word.

---

## ⚠️ Contraintes

- Pas de streaming
- Pas de hotkeys clavier
- Pas d'optimisation performance
- Pas d'UI avancée

---

## ✅ Definition of Done

Le projet est terminé si :

- L'icône micro apparaît
- L'enregistrement fonctionne au clic maintenu
- La transcription fonctionne
- La bulle affiche le texte avec bouton Copier
- La bulle se ferme
- L'application se ferme via clic droit

---

## 🚫 Hors scope

- Améliorations UX
- Support GPU
- Interface avancée
- Packaging
- Historique

---

## 🔍 Revue de code Phase 6

La revue de code de la Phase 6 a été effectuée le 2026-03-30. Le rapport complet est disponible dans [`reports/phase6_revue-code_20260330.md`](reports/phase6_revue-code_20260330.md).

| Priorité | Problème | Statut |
|----------|----------|--------|
| CRITIQUE | Import circulaire `record` ↔ `vad` | ✅ résolu — `config.py` extrait |
| HAUTE | Annotation de retour incorrecte `start_listening` | ✅ résolu — `-> str \| None` |
| HAUTE | Règle 150 lignes dépassée (3 fichiers) | en suspens |
| MOYENNE | Détection de thread non fiable (`winfo_id`) | ✅ résolu — `threading.main_thread()` |
| MOYENNE | Double stream sounddevice non garanti | ✅ résolu — try/except sur `start()` |

---

## 🐛 Bugs connus

### ~~Tâche résiduelle dans tasks/todo~~ ✅ résolu

`tasks/done/phase5_revue-code_20260328-0023.md` — revue de code Phase 5 effectuée et déplacée dans done.

---

### ~~Animation pulsante non arrêtée après transcription~~ ✅ résolu

Résolu par la refonte visuelle (branche `feature/visual-refactor`) : `start_animation` / `stop_animation` remplacées par `set_transcribing_state()` qui gère le cycle complet via `_schedule_pulse` / `_apply_transcribing_state`.

---

### Position initiale de l'icône micro

L'icône s'affiche correctement au centre sur écran unique. Le problème apparaît uniquement en configuration multi-écrans : l'icône ne se positionne plus au bon endroit lors de la connexion d'un second moniteur.

Cause probable : `winfo_screenwidth()` / `winfo_screenheight()` retourne les dimensions combinées ou celles du mauvais écran en multi-moniteurs.

À investiguer : détection de l'écran primaire, `winfo_x()` / `winfo_y()`, API multi-moniteurs tkinter/Wayland.

---

## 🔮 Améliorations futures

### Script d'installation automatique de whisper.cpp

Actuellement, l'utilisateur doit cloner whisper.cpp, le compiler, télécharger les modèles et configurer les chemins manuellement — c'est la partie la plus longue et la plus fragile de l'installation.

Amélioration : créer un script `install.sh` qui automatise l'ensemble du processus pour un nouvel utilisateur :

1. Clone whisper.cpp dans un répertoire cible (ex. `~/whisper.cpp`)
2. Compile le binaire (`cmake -B build && cmake --build build -j`)
3. Télécharge les modèles nécessaires (`ggml-small.en.bin`, `ggml-tiny.en.bin`)
4. Écrit automatiquement les variables d'environnement `WHISPER_BINARY`, `WHISPER_MODEL`, `WHISPER_MODEL_TINY` dans `~/.zshrc` (ou `~/.bashrc`) avec les chemins exacts issus de l'installation
5. Installe les dépendances Python dans le venv
6. Installe le wrapper shell `/usr/local/bin/record`

Bénéfice : l'utilisateur n'a jamais à chercher les chemins ni à éditer `record.py` ou son shell rc. Une seule commande suffit à passer de zéro à une installation fonctionnelle.

---

### Fuzzy matching pour la détection du wake word

~~Actuellement, la détection compare `WAKE_WORD.lower()` avec le texte retourné par Whisper (correspondance exacte). Avec un accent français, Whisper transcrit parfois "allo record" en "Alo record" ou "Hello record", ce qui échoue la vérification.~~

### ~~Fuzzy matching~~ ✅ implémenté

Algorithme `_matches_wake_word()` refondu en 4 étapes :

1. **Normalisation phonétique** — `hello/hallo/allow/aloe → allo` avant tout matching
2. **Correspondance exacte** sur le texte normalisé
3. **Matching bigramme mot à mot** — chaque paire de mots consécutifs testée individuellement (seuil 0.75 par mot), robuste si le texte contient du bruit additionnel
4. **Fallback global** `SequenceMatcher` (seuil 0.6) comme filet de sécurité

Modèle de détection passé de `ggml-tiny.en` à `ggml-tiny` (multilingue) avec `-l fr` forcé — "allo" est désormais transcrit correctement sans approximation anglophone.

### ~~Refonte visuelle~~ ✅ implémentée

Les primitives canvas tkinter ont été remplacées par des images PNG neon-glow via Pillow.

| Fichier | État |
|---------|------|
| `micro_gris.png` | Idle |
| `micro_ambre.png` | Écoute vocale ON |
| `micro_bleu.png` | Enregistrement actif |
| `micro_vert.png` | Transcription en cours (pulsing 400ms) |

Dépendance ajoutée : `Pillow`. Animation pulsante : alternance opacité 100% / 35% toutes les 400ms, sans calcul par frame.

---

### Bug : `~` non expandé dans les variables d'environnement

`os.getenv()` retourne la valeur brute de la variable d'environnement. Si l'utilisateur définit un chemin avec `~` (ex. `export WHISPER_MODEL=~/whisper.cpp/...`), Python ne l'expand pas — `os.path.isfile()` retourne `False` et la transcription échoue silencieusement.

Fix : wrapper `os.path.expanduser()` autour des trois variables `WHISPER_BINARY`, `WHISPER_MODEL`, `WHISPER_MODEL_WAKE` dans `record.py` :

```python
WHISPER_MODEL = os.path.expanduser(os.getenv("WHISPER_MODEL", ...))
```

---

### ~~Améliorer la vitesse de détection du wake word~~ ✅ implémenté

Trois optimisations appliquées (branche `feature/latency-improvements`) :

| Optim | Description | Gain estimé |
|-------|-------------|-------------|
| **P2** | `_SILENCE_CHUNKS_MIN_WAKE = 6` (192ms) séparé de `_SILENCE_CHUNKS_MIN_POST = 10` (320ms) | −128ms sur détection |
| **P4** | Préchauffage du page cache OS au démarrage de l'écoute VAD (`_warmup_page_cache`, Popen daemon) | −200-400ms sur 1re détection |
| **P1** | `faster-whisper` remplace subprocess whisper-cli — modèle chargé une fois en mémoire via singletons thread-safe | −200-800ms par transcription |

Modèles utilisés : `tiny` (wake word, langue fr) et `small.en` (transcription principale), téléchargés automatiquement depuis HuggingFace au premier lancement.

---

### Wake word personnalisable

Permettre à l'utilisateur de définir son propre mot de déclenchement sans modifier le code source.

Options envisagées :
- Variable d'environnement : `export WAKE_WORD="hey record"`
- Argument CLI : `record --wake-word "hey record"`

Le mécanisme de détection (Silero VAD + Whisper + fuzzy matching) est déjà générique — seule la constante `WAKE_WORD` dans `record.py` serait exposée.

---

### ~~Animation pendant la transcription vocale~~ ✅ résolu

Résolu par la refonte visuelle : `set_transcribing_state(True)` est appelé dans `_on_stop` et `_on_wake_stop` dès que le WAV est produit, dans les deux modes (clic et wake word).

---

## 🧠 Note finale

Ce projet est volontairement minimal.

Objectif :
→ obtenir un outil fonctionnel rapidement
→ sans complexité inutile
→ basé sur Whisper existant
