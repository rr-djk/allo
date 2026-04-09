"""vad.py — Écoute passive avec détection d'activité vocale Silero VAD.

Responsabilités :
- Charger le modèle Silero VAD une seule fois via torch.hub
- Ouvrir un stream audio via audio.open_stream() en mode écoute passive
- Analyser chaque bloc audio avec Silero VAD
- Accumuler les segments de parole dans un buffer court
- Quand un segment se termine : sauvegarder en WAV, transcrire avec le
  modèle tiny, notifier si le wake word est détecté
- Après le wake word : surveiller la fin de parole via un stream séparé
  (sounddevice direct) pour ne pas entrer en conflit avec le stream
  d'enregistrement principal de record.py

Ce module n'importe pas ui.py et ne gère pas l'enregistrement principal.
"""

import difflib
import threading

import numpy as np
import sounddevice as sd
import torch  # noqa: PLC0415 — module-level import for Silero VAD

import audio
from config import (
    CHANNELS,
    SAMPLE_RATE,
    SILENCE_DURATION,
    WAKE_WORD,
    transcribe_tiny,
)

# Modèle Silero VAD chargé une seule fois et mis en cache
_vad_model = None

# True quand la boucle d'écoute passive est active
_listening = False

# Blocs audio accumulés pendant un segment de parole en cours
_speech_buffer = []

# Circulaire de blocs silencieux précédant la parole (pre-roll ~500ms = 16 blocs)
_pre_buffer = []
_PRE_BUFFER_SIZE = 16  # 16 * 512 / 16000 ≈ 0.5s

# True si Silero VAD considère que de la parole est en cours dans le bloc courant
_is_speaking = False

# Nombre de chunks silence consécutifs avant de clore un segment wake word (~128ms)
# Valeur volontairement basse pour réduire la latence de détection.
_SILENCE_CHUNKS_MIN_WAKE = 4
# Nombre de chunks silence consécutifs documenté pour référence (320ms)
# Non utilisé dans ce callback — le silence post-wake-word utilise _silence_threshold.
_SILENCE_CHUNKS_MIN_POST = 10

# Nombre de chunks silencieux consécutifs depuis la fin de la dernière parole.
# Le segment n'est traité qu'après _SILENCE_CHUNKS_MIN_WAKE chunks silencieux (~128ms),
# pour éviter de couper sur les pauses naturelles (ex. "allo" / "record").
_silence_chunks = 0

# Transcription périodique pendant la parole (Option B)
# Intervalle en chunks avant de tenter une transcription précoce (~768ms)
_STREAMING_INTERVAL_CHUNKS = 24
# Compteur de chunks de parole accumulés depuis la dernière transcription périodique
_speech_chunk_count = 0
# True quand une transcription périodique est en cours (empêche les doublons)
_streaming_running = False

# Seuil de similarité floue pour la détection du wake word (0.0–1.0)
# Utilisé en fallback global quand le matching bigramme ne produit pas de résultat.
_WAKE_WORD_SIMILARITY_THRESHOLD = 0.6

# Seuil de similarité par mot individuel pour le matching bigramme
_WAKE_WORD_WORD_THRESHOLD = 0.75

# Substitutions phonétiques appliquées avant le matching (clé → valeur).
_PHONETIC_SUBSTITUTIONS = {}

# Protège les transitions d'état (_listening, _is_speaking, _speech_buffer)
_lock = threading.Lock()

# Callable fourni par l'appelant lors de start_listening()
_on_wake_word = None

# --- État de la détection de silence post-wake-word ---

# sd.InputStream dédié à la surveillance du silence ; None quand inactif.
# Distinct du stream géré par audio.py pour coexister avec le stream
# d'enregistrement principal de record.py.
_silence_stream = None

# True quand start_silence_detection() est actif
_silence_detecting = False

# Callable fourni par l'appelant lors de start_silence_detection()
_on_silence = None

# True dès qu'au moins un chunk de parole a été observé dans la session
# de surveillance ; permet d'ignorer le silence initial avant la première
# prise de parole.
_sd_speech_seen = False

# Nombre de chunks silencieux consécutifs depuis la dernière parole détectée
_sd_silence_chunks = 0

# Verrou protégeant l'état de la détection de silence
_silence_lock = threading.Lock()


def _normalize_phonetic(text: str) -> str:
    """Applique les substitutions phonétiques connues avant le matching.

    Remplace les transcriptions anglophones fréquentes de "allo" par leur
    forme correcte, insensible à la casse.

    @param text {str} Texte brut transcrit par Whisper.
    @returns {str} Texte normalisé en minuscules.
    """
    result = text.lower()
    for wrong, correct in _PHONETIC_SUBSTITUTIONS.items():
        result = result.replace(wrong, correct)
    return result


def _matches_wake_word(text: str) -> bool:
    """Vérifie si le texte transcrit correspond au wake word, exactement ou approximativement.

    Applique successivement quatre stratégies, de la plus rapide à la plus
    permissive :

    1. Normalisation phonétique : substitue les variantes anglophones connues
       de "allo" (Hello, Allow…) avant tout matching.
    2. Correspondance exacte : sous-chaîne stricte sur le texte normalisé.
    3. Matching bigramme : pour chaque paire de mots consécutifs, vérifie que
       chaque mot ressemble suffisamment à "allo" et "record" séparément
       (seuil _WAKE_WORD_WORD_THRESHOLD par mot). Évite la dilution du ratio
       quand le texte est plus long que le wake word.
    4. Fallback global : ratio SequenceMatcher entre le wake word et la
       meilleure sous-séquence de même longueur dans les tokens. Filet de
       sécurité pour les cas résiduels.

    @param text {str} Texte transcrit par Whisper à analyser.
    @returns {bool} True si le wake word est détecté, False sinon.
    """
    normalized = _normalize_phonetic(text)
    wake = WAKE_WORD.lower()  # "allo record"

    # Étape 2 — correspondance exacte après normalisation
    if wake in normalized:
        return True

    # Étape 3 — matching bigramme mot à mot
    wake_tokens = wake.split()          # ["allo", "record"]
    text_tokens = normalized.split()

    for i in range(len(text_tokens) - len(wake_tokens) + 1):
        bigram = text_tokens[i : i + len(wake_tokens)]
        if all(
            difflib.SequenceMatcher(None, wake_tokens[j], bigram[j]).ratio()
            >= _WAKE_WORD_WORD_THRESHOLD
            for j in range(len(wake_tokens))
        ):
            return True

    # Étape 4 — fallback global : meilleure sous-séquence de longueur identique
    wake_len = len(wake_tokens)
    best_ratio = 0.0
    for i in range(len(text_tokens) - wake_len + 1):
        candidate = " ".join(text_tokens[i : i + wake_len])
        ratio = difflib.SequenceMatcher(None, wake, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio

    return best_ratio >= _WAKE_WORD_SIMILARITY_THRESHOLD


def _load_vad_model():
    """Charge le modèle Silero VAD si ce n'est pas encore fait.

    Utilise torch.hub.load() avec force_reload=False pour éviter un
    rechargement à chaque appel. Le modèle est mis en cache dans
    _vad_model pour toute la durée de vie du processus.

    @returns {tuple} (model, utils) retourné par torch.hub.load().
    """
    global _vad_model

    if _vad_model is None:
        import torch  # Import différé : torch est lourd et facultatif au chargement

        _vad_model, _ = torch.hub.load(
            "snakers4/silero-vad",
            "silero_vad",
            force_reload=False,
        )

    return _vad_model


def start_listening(on_wake_word: callable) -> str | None:
    """Démarre l'écoute passive en arrière-plan.

    Charge Silero VAD si nécessaire, ouvre un stream audio via
    audio.open_stream(). Chaque bloc int16 16kHz mono reçu est converti
    en float32 et analysé par Silero VAD. Les blocs de parole sont
    accumulés dans _speech_buffer. Quand le silence succède à de la parole
    (fin de segment), le buffer est sauvegardé en WAV, transcrit par le
    modèle Whisper tiny, puis supprimé. Si le wake word est présent dans
    le texte transcrit, le stream est fermé et on_wake_word() est appelé
    depuis un thread worker (jamais depuis le callback audio).

    @param on_wake_word {callable} Appelé sans argument quand le wake word
                        est détecté. Appelé hors thread UI et hors callback.
    @raises RuntimeError si un stream audio est déjà ouvert.
    @returns {str|None} None en cas de succès, message d'erreur (str) si un
                        fichier requis est absent.
    """
    global _listening, _speech_buffer, _pre_buffer, _is_speaking, _silence_chunks, _on_wake_word
    global _speech_chunk_count, _streaming_running

    with _lock:
        _listening = True
        _speech_buffer = []
        _pre_buffer = []
        _is_speaking = False
        _silence_chunks = 0
        _speech_chunk_count = 0
        _streaming_running = False
        _on_wake_word = on_wake_word

    model = _load_vad_model()

    def _callback(indata, frames, time, status):  # noqa: ARG001
        """Callback sounddevice — reçoit des blocs int16 16kHz mono.

        Converti le bloc en float32 normalisé, interroge Silero VAD, puis
        pilote la machine d'état parole/silence. Jamais bloquant : la
        transcription et l'appel au callback on_wake_word sont délégués
        à un thread worker.
        """
        global _listening, _speech_buffer, _pre_buffer, _is_speaking, _silence_chunks
        global _speech_chunk_count, _streaming_running

        with _lock:
            if not _listening:
                return

        # Conversion int16 → float32 normalisé entre -1.0 et 1.0
        audio_float = indata[:, 0].astype(np.float32) / 32768.0
        tensor = torch.from_numpy(audio_float)

        # Silero VAD retourne un score de probabilité de parole (0.0–1.0)
        confidence = model(tensor, SAMPLE_RATE).item()
        speech_detected = confidence >= 0.5

        with _lock:
            if speech_detected:
                if not _is_speaking:
                    # Début de parole : prepend le pre-buffer pour capturer
                    # les premiers phonèmes (ex. "allo" dans "allo record").
                    _speech_buffer.extend(_pre_buffer)
                    _pre_buffer = []
                    _speech_chunk_count = 0
                _speech_buffer.append(indata.copy())
                _is_speaking = True
                _silence_chunks = 0

                # Option B — transcription périodique pendant la parole.
                # Toutes les _STREAMING_INTERVAL_CHUNKS chunks (~768ms), si
                # aucune transcription périodique n'est déjà en cours, lancer
                # _process_segment_streaming sur un snapshot du buffer courant.
                _speech_chunk_count += 1
                if _speech_chunk_count >= _STREAMING_INTERVAL_CHUNKS and not _streaming_running:
                    _speech_chunk_count = 0
                    _streaming_running = True
                    frames_snapshot = list(_speech_buffer)
                    threading.Thread(
                        target=_process_segment_streaming,
                        args=(frames_snapshot,),
                        daemon=True,
                    ).start()
            elif _is_speaking:
                # Chunk silencieux après de la parole — incrémenter le compteur.
                # On inclut ce chunk dans le buffer pour ne pas tronquer l'audio.
                _speech_buffer.append(indata.copy())
                _silence_chunks += 1

                if _silence_chunks >= _SILENCE_CHUNKS_MIN_WAKE:
                    # Assez de silence consécutif : clore le segment.
                    _is_speaking = False
                    _silence_chunks = 0
                    frames_snapshot = list(_speech_buffer)
                    _speech_buffer = []

                    threading.Thread(
                        target=_process_segment,
                        args=(frames_snapshot,),
                        daemon=True,
                    ).start()
            else:
                # Silence sans parole préalable : maintenir le pre-buffer glissant
                _pre_buffer.append(indata.copy())
                if len(_pre_buffer) > _PRE_BUFFER_SIZE:
                    _pre_buffer.pop(0)

    # Silero VAD requiert exactement 512 samples par chunk à 16kHz.
    audio.open_stream(_callback, blocksize=512)


def _process_segment_streaming(frames: list) -> None:
    """Version périodique de _process_segment : ne bloque pas le déclencheur silence.

    Appelée pendant que l'utilisateur parle encore (audio partiel). Si le wake
    word est détecté sur l'audio partiel → déclenchement immédiat. Sinon →
    le déclencheur silence classique (_process_segment) prendra le relais.

    Réinitialise _streaming_running à False quand terminé.

    @param frames {list[np.ndarray]} Snapshot des frames int16 accumulés jusqu'ici.
    @returns {None}
    """
    global _streaming_running
    try:
        _process_segment(frames)
    finally:
        with _lock:
            _streaming_running = False


def _process_segment(frames: list) -> None:
    """Transcrit un segment de parole et déclenche on_wake_word si nécessaire.

    Concatène les frames int16 en un tableau float32 normalisé, appelle
    transcribe_tiny(), puis vérifie si le wake word est présent. Si oui,
    ferme le stream, met _listening à False et appelle on_wake_word() depuis
    ce thread.

    Cette fonction est toujours exécutée dans un thread worker, jamais
    dans le callback audio ni dans le thread tkinter.

    @param frames {list[np.ndarray]} Blocs int16 accumulés pendant le segment.
    @returns {None}
    """
    global _listening, _on_wake_word

    if not frames:
        return

    # Construire un tableau float32 normalisé directement depuis les frames int16.
    # Évite l'aller-retour disque WAV : faster-whisper accepte un np.ndarray float32.
    audio_array = np.concatenate(frames, axis=0)[:, 0].astype(np.float32) / 32768.0
    text = transcribe_tiny(audio_array)

    if _matches_wake_word(text):
        # Wake word détecté : couper l'écoute avant d'appeler le callback
        with _lock:
            if not _listening:
                # stop_listening() a été appelé entre-temps — ne pas renotifier
                return
            _listening = False

        audio.close_stream()

        callback = _on_wake_word
        if callback is not None:
            callback()


def stop_listening() -> None:
    """Arrête l'écoute passive et ferme le stream audio. Idempotent.

    Ne fait rien si l'écoute n'est pas active.

    @returns {None}
    """
    global _listening

    with _lock:
        _listening = False

    audio.close_stream()


def is_listening() -> bool:
    """Retourne True si l'écoute passive est active.

    @returns {bool}
    """
    with _lock:
        return _listening


def start_silence_detection(on_silence: callable) -> str | None:
    """Démarre une écoute légère pour détecter la fin de parole.

    Ouvre un sd.InputStream directement (sans passer par audio.py) afin de
    pouvoir coexister avec le stream d'enregistrement principal déjà ouvert
    par record.start_recording(). Surveille le silence via Silero VAD.

    Quand SILENCE_DURATION secondes de silence consécutif sont détectées
    après de la parole, ferme le stream et appelle on_silence() depuis un
    thread worker (jamais depuis le callback audio).

    Utilisé après le wake word : l'enregistrement principal (record.py)
    capture l'audio en parallèle pendant ce temps.

    @param on_silence {callable} Appelé sans argument quand le silence
                      prolongé est détecté.
    @returns {str|None} None en cas de succès, message d'erreur (str) si le
                        stream sounddevice n'a pas pu démarrer.
    """
    global _silence_stream, _silence_detecting, _on_silence
    global _sd_speech_seen, _sd_silence_chunks

    # Nombre de chunks silencieux consécutifs requis pour déclarer la fin
    # de parole : calculé dynamiquement à partir de SILENCE_DURATION.
    # blocksize=512, SAMPLE_RATE=16000 → 512/16000 ≈ 32ms par chunk.
    _silence_threshold = int(SILENCE_DURATION * SAMPLE_RATE / 512)

    model = _load_vad_model()

    with _silence_lock:
        _silence_detecting = True
        _on_silence = on_silence
        _sd_speech_seen = False
        _sd_silence_chunks = 0

    def _callback(indata, frames, time, status):  # noqa: ARG001
        """Callback sounddevice — analyse chaque chunk pour la fin de parole.

        Converti le bloc en float32 normalisé, interroge Silero VAD, puis
        pilote la machine d'état parole/silence. Jamais bloquant : l'appel
        à on_silence est délégué à un thread worker.
        """
        global _silence_detecting, _on_silence, _sd_speech_seen, _sd_silence_chunks

        with _silence_lock:
            if not _silence_detecting:
                return

        # Conversion int16 → float32 normalisé entre -1.0 et 1.0
        audio_float = indata[:, 0].astype(np.float32) / 32768.0
        tensor = torch.from_numpy(audio_float)

        confidence = model(tensor, SAMPLE_RATE).item()
        speech_detected = confidence >= 0.5

        with _silence_lock:
            if not _silence_detecting:
                return

            if speech_detected:
                _sd_speech_seen = True
                _sd_silence_chunks = 0
            elif _sd_speech_seen:
                # Chunk silencieux après de la parole observée
                _sd_silence_chunks += 1

                if _sd_silence_chunks >= _silence_threshold:
                    # Silence prolongé : signaler la fin de dictée
                    _silence_detecting = False
                    callback = _on_silence

                    threading.Thread(
                        target=_fire_silence,
                        args=(callback,),
                        daemon=True,
                    ).start()

    with _silence_lock:
        if not _silence_detecting:
            # stop_silence_detection() a été appelé avant l'ouverture du stream
            return

        _silence_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=512,
            callback=_callback,
        )

    # Démarrer le stream hors du verrou : start() peut bloquer brièvement
    # et ne doit pas maintenir _silence_lock pendant ce temps.
    try:
        _silence_stream.start()
    except Exception as e:  # noqa: BLE001
        # Échec au démarrage : nettoyer l'état pour rester cohérent
        with _silence_lock:
            _silence_stream = None
            _silence_detecting = False
        return f"Erreur stream silence : {e}"


def _fire_silence(callback: callable) -> None:
    """Ferme le stream de surveillance du silence et invoque le callback.

    Toujours exécuté dans un thread worker, jamais dans le callback audio.

    @param callback {callable|None} Fonction sans argument à appeler.
    @returns {None}
    """
    stop_silence_detection()
    if callback is not None:
        callback()


def stop_silence_detection() -> None:
    """Arrête la détection de silence post-wake-word et ferme le stream. Idempotent.

    Ne fait rien si la détection n'est pas active.

    @returns {None}
    """
    global _silence_stream, _silence_detecting

    with _silence_lock:
        _silence_detecting = False
        stream = _silence_stream
        _silence_stream = None

    if stream is not None:
        try:
            stream.stop()
            stream.close()
        except Exception:  # noqa: BLE001 — stream potentiellement déjà fermé
            pass


def cleanup() -> None:
    """Libère toutes les ressources (stream, modèle VAD).

    Arrête l'écoute passive et la détection de silence si elles sont actives,
    puis efface la référence au modèle Silero VAD pour libérer la mémoire
    GPU/CPU si nécessaire.

    @returns {None}
    """
    global _vad_model

    stop_listening()
    stop_silence_detection()
    _vad_model = None
