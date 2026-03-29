---
status: done
type: feature
priority: high
assigned_to: system-architect
started_at: 2026-03-29
depends_on: ["phase6A_ajout-constantes_20260329-0900.md"]
files_touched: []
related_to: null
---

# phase6B — Spécification du module vad.py

## 1. Résumé

Le module `vad.py` encapsule la boucle d'écoute passive : détection d'activité vocale via Silero VAD, capture de segments courts, envoi à Whisper tiny pour identifier le mot déclencheur "allo record", et notification vers le main via callback. Il ne touche jamais à tkinter, ne gère pas l'enregistrement principal, et n'importe rien depuis `ui.py`.

Pour respecter la règle des 150 lignes, `record.py` doit être scindé : ses fonctions audio (capture, stream, WAV) migrent vers un nouveau module `audio.py`, et ses fonctions de transcription restent dans `record.py`.

---

## 2. Découpage nécessaire : extraction de `audio.py`

### 2.1 Problème

`record.py` fait 363 lignes. Ajouter la logique VAD dedans ou laisser `vad.py` réimplémenter la gestion de stream créerait de la duplication. De plus, la contrainte "un seul stream sounddevice à la fois" impose un point de contrôle unique.

### 2.2 Module `audio.py` — ce qui migre depuis `record.py`

Le module `audio.py` devient le propriétaire exclusif du stream `sounddevice`. Il exporte :

| Élément | Type | Rôle |
|---------|------|------|
| `open_stream(callback)` | fonction | Ouvre un `sd.InputStream` 16kHz mono int16. Lève une exception si un stream est déjà ouvert. |
| `close_stream()` | fonction | Stoppe et ferme le stream courant. Idempotent. |
| `is_stream_open()` | fonction | Retourne `True` si un stream est actuellement ouvert. |
| `frames_to_wav(frames, path)` | fonction | Concatène une liste de blocs numpy et écrit un fichier WAV. |

### 2.3 Ce qui reste dans `record.py`

- Toutes les constantes de configuration
- `start_recording()`, `stop_recording()`, `cancel_recording()`, `cleanup()` — deviennent des orchestrateurs qui appellent `audio.open_stream()` / `audio.close_stream()`
- `transcribe()`, `transcribe_tiny()`, `_parse_whisper_output()`, `run_transcription()`
- `main()`, `set_auto_stop_callback()`

Estimation après extraction : `record.py` ~180-200 lignes, `audio.py` ~60-80 lignes.

---

## 3. Module `vad.py` — interface publique

### 3.1 Responsabilités

`vad.py` fait :
- Charger le modèle Silero VAD (une seule fois, au premier appel)
- Ouvrir un stream audio via `audio.open_stream()` en mode écoute passive
- Analyser chaque bloc audio avec Silero VAD
- Accumuler les segments de parole dans un buffer court (~2s max)
- Quand un segment se termine : sauvegarder en WAV, appeler `transcribe_tiny()`, notifier si wake word détecté

`vad.py` ne fait pas :
- Manipuler tkinter
- Importer depuis `ui.py`
- Gérer l'enregistrement principal
- Ouvrir un stream `sounddevice` directement

### 3.2 Fonctions exportées

```python
def start_listening(on_wake_word: callable) -> None:
    """Démarre l'écoute passive en arrière-plan.

    Charge Silero VAD si nécessaire, ouvre un stream audio via
    audio.open_stream(). Quand le wake word est détecté, ferme le
    stream et appelle on_wake_word() depuis un thread worker.

    @param on_wake_word {callable} Appelé sans argument quand le wake
                        word est détecté. Appelé hors thread UI.
    @throws RuntimeError si un stream audio est déjà ouvert.
    """
    ...

def stop_listening() -> None:
    """Arrête l'écoute passive et ferme le stream audio. Idempotent.

    @returns {None}
    """
    ...

def is_listening() -> bool:
    """Retourne True si l'écoute passive est active.

    @returns {bool}
    """
    ...

def cleanup() -> None:
    """Libère toutes les ressources (stream, modèle VAD).

    @returns {None}
    """
    ...
```

### 3.3 État interne (privé)

| Variable | Type | Rôle |
|----------|------|------|
| `_vad_model` | objet Silero | Modèle chargé une seule fois via `torch.hub.load()` |
| `_listening` | `bool` | Flag d'état de la boucle |
| `_speech_buffer` | `list[np.ndarray]` | Blocs audio accumulés pendant la parole |
| `_is_speaking` | `bool` | Silero VAD détecte de la parole dans le bloc courant |
| `_lock` | `threading.Lock` | Protège les transitions d'état |
| `_on_wake_word` | `callable` | Callback stocké lors de `start_listening()` |

### 3.4 Fichier WAV temporaire

```
/tmp/vad_trigger_temp.wav
```

Distinct de `TEMP_WAV`. Créé par `audio.frames_to_wav()`, supprimé après chaque appel à `transcribe_tiny()`.

---

## 4. Dépendances

### 4.1 Imports internes

```
vad.py  -->  audio.py    (open_stream, close_stream, frames_to_wav)
vad.py  -->  record.py   (transcribe_tiny, WAKE_WORD, SAMPLE_RATE, SILENCE_DURATION)
```

`record.py` importe `vad.py` uniquement dans `main()`.

Si l'import circulaire `vad.py` <-> `record.py` se matérialise : extraire les constantes partagées vers `config.py`.

### 4.2 Librairies externes

| Librairie | Usage |
|-----------|-------|
| `torch` | Chargement Silero VAD via `torch.hub.load()` |
| `numpy` | Conversion int16 -> float32 pour Silero |
| `threading` | Lock, coordination |

`sounddevice` : importé uniquement par `audio.py`.

---

## 5. Points d'intégration

### 5.1 Démarrage depuis `main()`

1. `main()` appelle `vad.start_listening(on_wake_word=callback)`
2. Le callback est une closure qui utilise `app.after(0, ...)` pour les actions UI

### 5.2 Conflit stream : VAD vs enregistrement principal

Protocole obligatoire :
1. `on_record_start` appelle `vad.stop_listening()` → ferme le stream VAD
2. Puis `start_recording()` ouvre un nouveau stream via `audio.open_stream()`
3. Après transcription, `main()` relance `vad.start_listening()` si le toggle est actif

### 5.3 Flux séquentiel (Phase 6B)

```
[Thread worker vad.py]
  --> on_wake_word()
    --> app.after(0, lambda: ...)   # planifié dans le thread tkinter
      --> record.start_recording()
      --> [arrêt manuel ou MAX_DURATION en 6B]
```

---

## 6. Estimation de taille des fichiers

| Module | Lignes estimées |
|--------|----------------|
| `audio.py` | ~60-80 |
| `vad.py` | ~100-130 |
| `record.py` (après extraction) | ~180-200 |
| `ui.py` | ~393 (inchangé) |

`record.py` restera > 150 lignes. Une seconde extraction (`transcribe.py`) est possible en Phase 6C/6D si nécessaire. Reporter pour l'instant.

---

## 7. Risques

| Risque | Mitigation |
|--------|------------|
| Import circulaire `vad.py` <-> `record.py` | Extraire constantes vers `config.py` si nécessaire |
| Conflit stream clic/voix | `audio.py` lève une exception si stream déjà ouvert — force le protocole stop_listening avant start_recording |
| Latence `transcribe_tiny()` | Modèle tiny rapide (~200ms pour 2s audio). Acceptable. |
| PyTorch absent | Phase 6D : désactiver le toggle et afficher erreur |
