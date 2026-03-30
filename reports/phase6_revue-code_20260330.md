# Rapport de revue de code — Phase 6

**Date :** 2026-03-30
**Fichiers révisés :** `record.py`, `ui.py`, `vad.py`
**Réviseur :** code-reviewer (agent)

---

## Synthèse

| Priorité | Problème | Fichier:Ligne | Statut |
|----------|----------|---------------|--------|
| CRITIQUE | Import circulaire `record` ↔ `vad` | `vad.py:25`, `record.py:16` | Non-conforme |
| HAUTE | Annotation de retour incorrecte `start_listening` | `vad.py:133` | Non-conforme |
| HAUTE | Règle 150 lignes dépassée (3 fichiers) | tous | Non-conforme |
| MOYENNE | Détection de thread non fiable (`winfo_id`) | `ui.py:297-300` | Risque |
| MOYENNE | Double stream sounddevice non garanti | `vad.py:388-395` | À vérifier |
| OK | Thread-safety UI (`app.after(0, ...)`) | tous | Conforme |
| OK | Docstrings fonctions publiques | tous | Conforme |

---

## Détails

### CRITIQUE — Import circulaire `record.py` ↔ `vad.py`

`record.py:16` importe `vad`, et `vad.py:25` importe des constantes directement depuis `record` :

```python
# vad.py:25
from record import SAMPLE_RATE, SILENCE_DURATION, WAKE_WORD, WHISPER_BINARY, WHISPER_MODEL_TINY

# vad.py:250
from record import transcribe_tiny  # import différé

# vad.py:381
from record import CHANNELS  # import différé
```

Fonctionne accidentellement parce que les constantes sont définies avant `import vad` dans `record.py`. Fragile : tout réordonnancement casse l'import.

L'import différé de `CHANNELS` (ligne 381) alors que `SAMPLE_RATE` est importé en top-level est une incohérence qui trahit un contournement ad hoc.

**Fix recommandé :** extraire les constantes partagées dans `config.py`, et `transcribe_tiny` dans `transcription.py`. Élimine le cycle proprement.

---

### HAUTE — Annotation de retour incorrecte

`vad.py:133` :

```python
def start_listening(on_wake_word: callable) -> None:
```

La fonction retourne en réalité `str | None` (une erreur ou `None`). L'appelant dans `record.py` teste `if erreur is not None` — correct en runtime, mais les typecheckers (mypy/pyright) signalent ce test comme toujours faux.

**Fix :** `-> str | None`

---

### HAUTE — Règle 150 lignes dépassée

| Fichier | Lignes | Dépassement |
|---------|--------|-------------|
| `record.py` | 496 | +346 |
| `ui.py` | 462 | +312 |
| `vad.py` | 447 | +297 |

`record.py` est le candidat prioritaire : il contient config, audio, transcription et `main()` avec toutes ses closures imbriquées.

**Fix recommandé :** extraire au moment voulu selon la règle du projet (extraire seulement quand le seuil est franchi sur un nouveau développement, pas rétroactivement sauf si décidé explicitement).

---

### MOYENNE — Détection de thread non fiable (`ui.py:297-300`)

La garde "suis-je dans le thread tkinter ?" repose sur `winfo_id()` qui lève `RuntimeError` hors thread UI. Ce comportement n'est pas garanti sur toutes les versions Python/tkinter.

**Fix recommandé :**

```python
import threading
if threading.main_thread() is threading.current_thread():
    # appel direct
else:
    self.after(0, lambda: ...)
```

---

### MOYENNE — Double stream sounddevice (`vad.py:388-395`)

`start_silence_detection()` ouvre un `sd.InputStream` direct en parallèle du stream géré par `audio.py`. Si le driver ALSA ne supporte pas deux streams simultanés sur le même device, le callback ne se déclenche pas (ou une exception est silencieusement avalée).

**Fix recommandé :** vérifier la compatibilité sur le device cible. Ajouter un log ou une exception remontée si `_silence_stream.start()` échoue.

---

## Points conformes

- **Thread-safety UI :** tous les appels à `set_listening_state`, `set_recording_state`, `show_bubble` passent par le thread tkinter ou `app.after(0, ...)`. Conforme.
- **Docstrings :** toutes les fonctions publiques (sans préfixe `_`) ont des docstrings. Les closures internes de `main()` n'en ont pas — acceptable.
