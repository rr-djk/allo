"""record.py — Configuration et point d'entrée de l'application record.

Contient :
- Les constantes de configuration (chemins Whisper, fichier temporaire, durées)
- La fonction main() qui instancie l'interface graphique et lance la boucle tkinter
"""

import threading

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile

from ui import MicIcon


# Chemin absolu vers le binaire whisper-cli compilé depuis whisper.cpp
WHISPER_BINARY = "/chemin/vers/whisper.cpp/build/bin/whisper-cli"
# Chemin absolu vers le fichier modèle Whisper (format ggml)
WHISPER_MODEL  = "/chemin/vers/whisper.cpp/models/ggml-base.en.bin"
# Fichier WAV temporaire utilisé pendant l'enregistrement
TEMP_WAV       = "/tmp/record_temp.wav"
# Fréquence d'échantillonnage en Hz
SAMPLE_RATE    = 16000  # Hz
# Nombre de canaux audio (1 = mono)
CHANNELS       = 1      # mono
# Durée maximale d'un enregistrement en secondes (arrêt automatique au-delà)
MAX_DURATION   = 90    # secondes
# Durée minimale d'un enregistrement en secondes (en dessous, l'audio est ignoré)
MIN_DURATION   = 0.5   # secondes


# Blocs audio bruts accumulés par le callback du stream d'entrée
_audio_frames = []
# Stream sounddevice actif, None quand aucun enregistrement en cours
_stream = None
# Timer d'arrêt automatique, None quand aucun enregistrement en cours
_auto_stop_timer = None
# Verrou protégeant stop_recording() contre un double appel simultané
# (timer + relâchement du bouton au même instant)
_stop_lock = threading.Lock()
# Callable invoqué après un arrêt automatique pour notifier l'interface
_on_auto_stop_callback = None


def set_auto_stop_callback(callback):
    """Enregistre le callable à invoquer après un arrêt automatique.

    Ce callable est appelé depuis le thread du timer, après que
    `stop_recording()` a terminé. L'appelant est responsable de
    l'exécuter dans le bon thread si nécessaire (ex. : `root.after`).

    @param callback {callable|None} Fonction sans argument à invoquer,
                    ou None pour désactiver la notification.
    @returns {None}
    """
    global _on_auto_stop_callback
    _on_auto_stop_callback = callback


def start_recording():
    """Démarre la capture audio depuis le microphone par défaut.

    Réinitialise le tampon interne puis ouvre un `sounddevice.InputStream`
    non-bloquant. Chaque bloc reçu est ajouté à `_audio_frames`.
    Un timer d'arrêt automatique est armé pour interrompre l'enregistrement
    après `MAX_DURATION` secondes.

    @returns {None}
    """
    global _audio_frames, _stream, _auto_stop_timer

    _audio_frames = []

    def _callback(indata, frames, time, status):  # noqa: ARG001
        _audio_frames.append(indata.copy())

    _stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=_callback,
    )
    _stream.start()

    def _on_timer_fired():
        stop_recording()
        if _on_auto_stop_callback is not None:
            _on_auto_stop_callback()

    _auto_stop_timer = threading.Timer(MAX_DURATION, _on_timer_fired)
    _auto_stop_timer.start()


def stop_recording():
    """Arrête la capture audio et écrit le fichier WAV temporaire.

    Annule le timer d'arrêt automatique s'il est encore en cours, puis
    stoppe et ferme le stream ouvert par `start_recording()`.
    Concatène les blocs accumulés dans `_audio_frames`, calcule la durée
    réelle et écrit `TEMP_WAV` si la durée est suffisante.

    @returns {bool} True si le fichier WAV a été écrit, False sinon
                    (tampon vide ou durée inférieure à MIN_DURATION).
    """
    global _stream, _auto_stop_timer

    with _stop_lock:
        # Annuler le timer avant toute autre opération pour éviter un double appel
        if _auto_stop_timer is not None:
            _auto_stop_timer.cancel()
            _auto_stop_timer = None

        if _stream is not None:
            _stream.stop()
            _stream.close()
            _stream = None

        if not _audio_frames:
            return False

        frames = np.concatenate(_audio_frames, axis=0)
        duration = len(frames) / SAMPLE_RATE

        if duration < MIN_DURATION:
            return False

        wavfile.write(TEMP_WAV, SAMPLE_RATE, frames)
        return True


def main():
    """Point d'entrée de l'application.

    Instancie la fenêtre icône micro et démarre la boucle principale tkinter.

    @returns {None}
    """
    app = MicIcon(
        on_record_start=start_recording,
        on_record_stop=stop_recording,
        on_auto_stop=None,  # remplacé ci-dessous après création de l'app
    )

    def _handle_auto_stop():
        # Appelé depuis le thread du timer : planifier le callback UI dans
        # le thread tkinter pour éviter toute modification de widget hors-fil
        if app._on_record_stop is not None:
            app.after(0, app._on_record_stop)

    set_auto_stop_callback(_handle_auto_stop)
    app.mainloop()


if __name__ == "__main__":
    main()
