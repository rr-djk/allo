"""audio.py — Propriétaire exclusif du stream sounddevice.

Exporte :
- open_stream(callback)  : ouvre un InputStream 16kHz mono int16
- close_stream()         : ferme le stream courant (idempotent)
- is_stream_open()       : indique si un stream est actif
- frames_to_wav(frames, path) : concatène des blocs numpy et écrit un WAV
"""

import threading

import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd

# Stream sounddevice actif, None quand aucun stream n'est ouvert
_stream = None
# Verrou protégeant les accès concurrents à _stream depuis le thread tkinter
# et les threads workers
_stream_lock = threading.Lock()


def open_stream(callback, blocksize: int = None) -> None:
    """Ouvre un sd.InputStream 16kHz mono int16.

    Démarre un stream non-bloquant ; chaque bloc audio reçu est transmis
    à `callback(indata, frames, time, status)`.

    Les constantes SAMPLE_RATE et CHANNELS sont lues depuis record.py via
    un import différé pour éviter l'import circulaire au chargement des modules.

    @param callback  {callable} Fonction de callback sounddevice.
    @param blocksize {int}      Taille des blocs audio en samples. None = défaut
                                sounddevice. Silero VAD requiert >= 512 à 16kHz.
    @raises RuntimeError si un stream est déjà ouvert.
    @returns {None}
    """
    global _stream

    # Import différé : record importe audio, donc l'import au niveau module
    # serait circulaire. À ce point d'exécution, record est complètement chargé.
    from record import SAMPLE_RATE, CHANNELS  # noqa: PLC0415

    with _stream_lock:
        if _stream is not None:
            raise RuntimeError("Un stream audio est déjà ouvert.")

        _stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=blocksize,
            callback=callback,
        )
        _stream.start()


def close_stream() -> None:
    """Ferme le stream courant. Idempotent.

    Stoppe et ferme le stream si un stream est ouvert.
    Ne fait rien si aucun stream n'est actif.

    @returns {None}
    """
    global _stream

    with _stream_lock:
        stream = _stream
        _stream = None
    if stream is not None:
        stream.stop()
        stream.close()


def is_stream_open() -> bool:
    """Retourne True si un stream est actuellement ouvert.

    @returns {bool}
    """
    with _stream_lock:
        return _stream is not None


def frames_to_wav(frames: list, path: str) -> None:
    """Concatène des blocs numpy int16 et écrit un fichier WAV 16kHz mono.

    Les constantes SAMPLE_RATE sont lues depuis record.py via un import
    différé pour éviter l'import circulaire au chargement des modules.

    @param frames {list[np.ndarray]} Liste de blocs audio int16 accumulés
                  par le callback du stream.
    @param path   {str} Chemin absolu du fichier WAV à écrire.
    @returns {None}
    """
    from record import SAMPLE_RATE  # noqa: PLC0415

    data = np.concatenate(frames, axis=0)
    wavfile.write(path, SAMPLE_RATE, data)
