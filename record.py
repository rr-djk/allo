"""record.py — Configuration et point d'entrée de l'application record.

Contient :
- Les constantes de configuration (chemins Whisper, fichier temporaire, durées)
- La fonction main() qui instancie l'interface graphique et lance la boucle tkinter
"""

import os
import re
import subprocess
import threading

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile

from ui import MicIcon


# Chemin absolu vers le binaire whisper-cli compilé depuis whisper.cpp
WHISPER_BINARY = "../../whisper.cpp/build/bin/whisper-cli"
# Chemin absolu vers le fichier modèle Whisper (format ggml)
WHISPER_MODEL  = "../../whisper.cpp/models/ggml-base.en.bin"
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
        # Ne pas appeler stop_recording() ici : _on_stop (via
        # _on_auto_stop_callback) est le seul point d'appel, qu'il
        # s'agisse d'un arrêt manuel ou automatique. Cela évite un
        # double appel à stop_recording() et une double transcription.
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
            # Le stream est fermé : le callback ne s'exécutera plus jamais.
            # On peut lire _audio_frames en toute sécurité à partir d'ici.
            _stream = None

        if not _audio_frames:
            return False

        frames = np.concatenate(_audio_frames, axis=0)
        duration = len(frames) / SAMPLE_RATE

        if duration < MIN_DURATION:
            return False

        wavfile.write(TEMP_WAV, SAMPLE_RATE, frames)
        return True


def cancel_recording():
    """Annule un enregistrement en cours sans produire de fichier WAV.

    Arrête et ferme `_stream`, vide `_audio_frames` et annule le timer
    d'arrêt automatique. Ne crée pas de fichier WAV et ne déclenche pas
    de transcription. Utilisé quand l'utilisateur glisse la fenêtre au
    lieu de cliquer pour enregistrer.

    @returns {None}
    """
    global _stream, _auto_stop_timer, _audio_frames

    with _stop_lock:
        if _auto_stop_timer is not None:
            _auto_stop_timer.cancel()
            _auto_stop_timer = None

        if _stream is not None:
            _stream.stop()
            _stream.close()
            _stream = None

        # Vider le tampon : l'audio capturé pendant le drag est abandonné
        _audio_frames = []


def cleanup():
    """Annule le timer et ferme le stream si un enregistrement est en cours.

    Doit être appelé avant de quitter l'application pour s'assurer qu'aucun
    thread non-daemon ne bloque la fin du processus.

    @returns {None}
    """
    global _stream, _auto_stop_timer

    with _stop_lock:
        if _auto_stop_timer is not None:
            _auto_stop_timer.cancel()
            _auto_stop_timer = None

        if _stream is not None:
            _stream.stop()
            _stream.close()
            _stream = None


def _parse_whisper_output(raw: str) -> str:
    """Nettoie la sortie brute de whisper-cli.

    Supprime les horodatages au format `[HH:MM:SS.mmm --> HH:MM:SS.mmm]`
    ainsi que les balises `<...>` (tokens de timestamp intra-segment).

    @param raw {str} Stdout brut retourné par whisper-cli.
    @returns {str} Texte nettoyé et stripé ; chaîne vide si rien ne reste.
    """
    # Supprime les horodatages de segment : [00:00:00.000 --> 00:00:05.000]
    text = re.sub(r"\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]", "", raw)
    # Supprime les balises intra-segment : <00:00:00.000>
    text = re.sub(r"<[^>]*>", "", text)
    return text.strip()


def transcribe() -> str:
    """Transcrit le fichier WAV temporaire via whisper-cli.

    Vérifie l'existence du binaire et du modèle avant l'appel, puis
    appelle whisper-cli en subprocess. Supprime `TEMP_WAV` dans tous
    les cas (bloc `finally`).

    @returns {str} Texte transcrit nettoyé, ou un message d'erreur
                   préfixé par « Erreur : » / « Erreur whisper-cli : »,
                   ou « (aucun texte transcrit) » si la sortie est vide.
    @note Retourne toujours une str non-None.
    """
    # Les vérifications préalables sont hors du try/finally : si elles
    # échouent, TEMP_WAV n'a pas encore été consommé et ne doit pas être
    # supprimé ici (il n'existe pas ou appartient à un autre cycle).
    if not os.path.isfile(WHISPER_BINARY):
        return "Erreur : binaire whisper-cli introuvable"

    if not os.path.isfile(WHISPER_MODEL):
        return "Erreur : modèle Whisper introuvable"

    try:
        result = subprocess.run(
            [WHISPER_BINARY, "-m", WHISPER_MODEL, "-f", TEMP_WAV],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # stderr peut être vide si whisper-cli écrit tout sur stdout
            error_msg = result.stderr.strip() or result.stdout.strip() or "erreur inconnue"
            return f"Erreur whisper-cli : {error_msg}"

        text = _parse_whisper_output(result.stdout)
        return text if text else "(aucun texte transcrit)"

    finally:
        try:
            os.remove(TEMP_WAV)
        except OSError:
            pass


def run_transcription(on_result):
    """Lance la transcription dans un thread daemon sans bloquer l'appelant.

    Démarre `transcribe()` dans un `threading.Thread(daemon=True)` puis
    appelle `on_result` avec le texte retourné, depuis ce même thread.
    L'appelant reçoit le contrôle immédiatement.

    @param on_result {callable} Fonction appelée avec le texte transcrit
                    (str) une fois la transcription terminée. Elle est
                    invoquée depuis le thread de transcription — ne pas
                    y manipuler de widgets tkinter directement.
    @returns {None}
    """
    def _worker():
        text = transcribe()
        on_result(text)

    threading.Thread(target=_worker, daemon=True).start()


def main():
    """Point d'entrée de l'application.

    Instancie la fenêtre icône micro et démarre la boucle principale tkinter.

    @returns {None}
    """
    def _on_stop():
        # Arrête l'enregistrement ; si un WAV valide a été produit, lance
        # la transcription en arrière-plan et affiche le résultat dans le
        # terminal. Aucun widget tkinter n'est touché depuis ce callback.
        success = stop_recording()
        if success:
            run_transcription(on_result=lambda text: print(text))

    app = MicIcon(
        on_record_start=start_recording,
        on_record_stop=_on_stop,
        on_record_cancel=cancel_recording,
        on_auto_stop=None,  # remplacé ci-dessous après création de l'app
        on_quit=cleanup,
    )

    def _handle_auto_stop():
        # Appelé depuis le thread du timer : planifier _on_stop dans le
        # thread tkinter pour que MicIcon mette à jour son état visuel
        # sans manipulation de widget hors-fil.
        app.after(0, _on_stop)

    set_auto_stop_callback(_handle_auto_stop)
    app.mainloop()


if __name__ == "__main__":
    main()
