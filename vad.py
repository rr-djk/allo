"""vad.py — Écoute passive avec détection d'activité vocale Silero VAD.

Responsabilités :
- Charger le modèle Silero VAD une seule fois via torch.hub
- Ouvrir un stream audio via audio.open_stream() en mode écoute passive
- Analyser chaque bloc audio avec Silero VAD
- Accumuler les segments de parole dans un buffer court
- Quand un segment se termine : sauvegarder en WAV, transcrire avec le
  modèle tiny, notifier si le wake word est détecté

Ce module n'importe pas ui.py et ne gère pas l'enregistrement principal.
"""

import os
import threading

import numpy as np

import audio
from record import SAMPLE_RATE, WAKE_WORD

# Chemin du fichier WAV temporaire propre à la boucle VAD
_VAD_TEMP_WAV = "/tmp/vad_trigger_temp.wav"

# Modèle Silero VAD chargé une seule fois et mis en cache
_vad_model = None

# True quand la boucle d'écoute passive est active
_listening = False

# Blocs audio accumulés pendant un segment de parole en cours
_speech_buffer = []

# True si Silero VAD considère que de la parole est en cours dans le bloc courant
_is_speaking = False

# Protège les transitions d'état (_listening, _is_speaking, _speech_buffer)
_lock = threading.Lock()

# Callable fourni par l'appelant lors de start_listening()
_on_wake_word = None


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


def start_listening(on_wake_word: callable) -> None:
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
    @returns {None}
    """
    global _listening, _speech_buffer, _is_speaking, _on_wake_word

    with _lock:
        _listening = True
        _speech_buffer = []
        _is_speaking = False
        _on_wake_word = on_wake_word

    model = _load_vad_model()

    def _callback(indata, frames, time, status):  # noqa: ARG001
        """Callback sounddevice — reçoit des blocs int16 16kHz mono.

        Converti le bloc en float32 normalisé, interroge Silero VAD, puis
        pilote la machine d'état parole/silence. Jamais bloquant : la
        transcription et l'appel au callback on_wake_word sont délégués
        à un thread worker.
        """
        global _listening, _speech_buffer, _is_speaking

        with _lock:
            if not _listening:
                return

        import torch  # noqa: PLC0415 — import différé, torch peut être absent

        # Conversion int16 → float32 normalisé entre -1.0 et 1.0
        audio_float = indata[:, 0].astype(np.float32) / 32768.0
        tensor = torch.from_numpy(audio_float)

        # Silero VAD retourne un score de probabilité de parole (0.0–1.0)
        confidence = model(tensor, SAMPLE_RATE).item()
        speech_detected = confidence >= 0.5

        with _lock:
            if speech_detected:
                # Accumuler le bloc dans le buffer de parole
                _speech_buffer.append(indata.copy())
                _is_speaking = True
            elif _is_speaking:
                # Fin de segment : silence détecté après de la parole
                _is_speaking = False
                frames_snapshot = list(_speech_buffer)
                _speech_buffer = []

                # Déléguer la transcription et la vérification du wake word
                # à un thread worker pour ne pas bloquer le callback audio.
                threading.Thread(
                    target=_process_segment,
                    args=(frames_snapshot,),
                    daemon=True,
                ).start()

    # Silero VAD requiert exactement 512 samples par chunk à 16kHz.
    audio.open_stream(_callback, blocksize=512)


def _process_segment(frames: list) -> None:
    """Transcrit un segment de parole et déclenche on_wake_word si nécessaire.

    Écrit les blocs audio dans un fichier WAV temporaire, appelle
    transcribe_tiny(), supprime le WAV, puis vérifie si le wake word
    est présent (insensible à la casse). Si oui, ferme le stream,
    met _listening à False et appelle on_wake_word() depuis ce thread.

    Cette fonction est toujours exécutée dans un thread worker, jamais
    dans le callback audio ni dans le thread tkinter.

    @param frames {list[np.ndarray]} Blocs int16 accumulés pendant le segment.
    @returns {None}
    """
    global _listening, _on_wake_word

    # Import différé identique à audio.py pour éviter un import circulaire
    from record import transcribe_tiny  # noqa: PLC0415

    if not frames:
        return

    try:
        audio.frames_to_wav(frames, _VAD_TEMP_WAV)
        text = transcribe_tiny(_VAD_TEMP_WAV)
    finally:
        try:
            os.remove(_VAD_TEMP_WAV)
        except OSError:
            pass

    if WAKE_WORD.lower() in text.lower():
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


def cleanup() -> None:
    """Libère toutes les ressources (stream, modèle VAD).

    Arrête l'écoute si elle est active et efface la référence au modèle
    Silero VAD pour libérer la mémoire GPU/CPU si nécessaire.

    @returns {None}
    """
    global _vad_model

    stop_listening()
    _vad_model = None
