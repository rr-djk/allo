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

import audio
import vad
from ui import MicIcon

# Répertoire contenant ce fichier ; sert de base pour les chemins relatifs
# afin que l'application fonctionne quel que soit le répertoire de travail courant.
_BASE = os.path.dirname(os.path.abspath(__file__))

# Chemin absolu vers le binaire whisper-cli compilé depuis whisper.cpp
WHISPER_BINARY = os.path.join(_BASE, "../../whisper.cpp/build/bin/whisper-cli")
# Chemin absolu vers le fichier modèle Whisper (format ggml)
WHISPER_MODEL  = os.path.join(_BASE, "../../whisper.cpp/models/ggml-small.en.bin")
# Chemin absolu vers le modèle Whisper léger (inutilisé — small.en utilisé partout)
WHISPER_MODEL_TINY = os.path.join(_BASE, "../../whisper.cpp/models/ggml-tiny.en.bin")
# Mot de réveil attendu pour déclencher un enregistrement
WAKE_WORD          = "allo record"
# Variantes proches du wake word produites par Whisper (transcriptions erronées connues)
_WAKE_WORD_VARIANTS = [
    "alo record",
    "hello record",
    "allow record",
]
# Durée de silence (en secondes) marquant la fin d'une prise de parole
SILENCE_DURATION   = 1.5   # secondes
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
# Timer d'arrêt automatique, None quand aucun enregistrement en cours
_auto_stop_timer = None
# Verrou protégeant stop_recording() contre un double appel simultané
# (timer + relâchement du bouton au même instant)
_stop_lock = threading.Lock()
# Callable invoqué après un arrêt automatique pour notifier l'interface
_on_auto_stop_callback = None
# Vrai quand un thread de transcription est en cours d'exécution ;
# protège contre un double déclenchement (ex. : arrêt manuel + timer simultanés)
_transcription_running = False
# Verrou protégeant la lecture/écriture de _transcription_running
_transcription_lock = threading.Lock()


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

    Réinitialise le tampon interne puis ouvre un stream via
    `audio.open_stream()`. Chaque bloc reçu est ajouté à `_audio_frames`.
    Un timer d'arrêt automatique est armé pour interrompre l'enregistrement
    après `MAX_DURATION` secondes.

    @returns {None}
    """
    global _audio_frames, _auto_stop_timer

    _audio_frames = []

    def _callback(indata, frames, time, status):  # noqa: ARG001
        _audio_frames.append(indata.copy())

    audio.open_stream(_callback)

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
    ferme le stream via `audio.close_stream()`.
    Calcule la durée réelle et écrit `TEMP_WAV` via `audio.frames_to_wav()`
    si la durée est suffisante.

    @returns {bool} True si le fichier WAV a été écrit, False sinon
                    (tampon vide ou durée inférieure à MIN_DURATION).
    """
    global _auto_stop_timer

    with _stop_lock:
        # Annuler le timer avant toute autre opération pour éviter un double appel
        if _auto_stop_timer is not None:
            _auto_stop_timer.cancel()
            _auto_stop_timer = None

        # Ferme le stream ; le callback ne s'exécutera plus jamais après cela.
        # On peut lire _audio_frames en toute sécurité à partir d'ici.
        audio.close_stream()

        if not _audio_frames:
            return False

        duration = len(np.concatenate(_audio_frames, axis=0)) / SAMPLE_RATE

        if duration < MIN_DURATION:
            return False

        audio.frames_to_wav(_audio_frames, TEMP_WAV)
        return True


def cancel_recording():
    """Annule un enregistrement en cours sans produire de fichier WAV.

    Ferme le stream via `audio.close_stream()`, vide `_audio_frames` et
    annule le timer d'arrêt automatique. Ne crée pas de fichier WAV et
    ne déclenche pas de transcription. Utilisé quand l'utilisateur glisse
    la fenêtre au lieu de cliquer pour enregistrer.

    @returns {None}
    """
    global _auto_stop_timer, _audio_frames

    with _stop_lock:
        if _auto_stop_timer is not None:
            _auto_stop_timer.cancel()
            _auto_stop_timer = None

        audio.close_stream()

        # Vider le tampon : l'audio capturé pendant le drag est abandonné
        _audio_frames = []


def cleanup():
    """Annule le timer et ferme le stream si un enregistrement est en cours.

    Arrête également l'écoute VAD si elle est active, afin qu'aucun thread
    non-daemon ni stream sounddevice ne bloque la fin du processus.

    @returns {None}
    """
    global _auto_stop_timer

    # Arrêter l'écoute VAD en premier : elle possède son propre stream
    if vad.is_listening():
        vad.stop_listening()

    with _stop_lock:
        if _auto_stop_timer is not None:
            _auto_stop_timer.cancel()
            _auto_stop_timer = None

        audio.close_stream()


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


def _strip_wake_word(text: str) -> str:
    """Supprime le wake word du texte transcrit (insensible à la casse).

    Retire toute occurrence de WAKE_WORD et ses variantes proches
    (ex. "Alo", "Hello") du début du texte, puis nettoie les espaces
    et la ponctuation résiduels.

    Utilisé uniquement pour les transcriptions déclenchées par le mode
    écoute vocale — pas pour le mode clic maintenu.

    @param text {str} Texte transcrit par Whisper.
    @returns {str} Texte nettoyé, sans le wake word en tête.
    """
    # Construire la liste complète des termes à supprimer : wake word principal + variantes
    terms = [WAKE_WORD] + _WAKE_WORD_VARIANTS

    result = text
    for term in terms:
        # Suppression insensible à la casse, n'importe où dans le texte
        result = re.sub(re.escape(term), "", result, flags=re.IGNORECASE)

    # Nettoyer les virgules, points et espaces résiduels en début de texte
    result = re.sub(r"^[\s,\.]+", "", result)
    # Normaliser les espaces multiples internes
    result = re.sub(r" {2,}", " ", result)
    result = result.strip()

    return result if result else "(aucun texte transcrit)"


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


def transcribe_tiny(wav_path: str) -> str:
    """Transcrit un fichier WAV via whisper-cli avec le modèle tiny.

    Vérifie l'existence du binaire et du modèle tiny avant l'appel, puis
    appelle whisper-cli en subprocess sur `wav_path`. Contrairement à
    `transcribe()`, ne supprime pas le fichier WAV après l'appel.

    @param wav_path {str} Chemin absolu vers le fichier WAV à transcrire.
    @returns {str} Texte transcrit nettoyé, ou un message d'erreur
                   préfixé par « Erreur : » / « Erreur whisper-cli : »,
                   ou « (aucun texte transcrit) » si la sortie est vide.
    @note Retourne toujours une str non-None.
    """
    if not os.path.isfile(WHISPER_BINARY):
        return "Erreur : binaire whisper-cli introuvable"

    if not os.path.isfile(WHISPER_MODEL):
        return "Erreur : modèle Whisper introuvable"

    result = subprocess.run(
        [WHISPER_BINARY, "-m", WHISPER_MODEL, "-f", wav_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # stderr peut être vide si whisper-cli écrit tout sur stdout
        error_msg = result.stderr.strip() or result.stdout.strip() or "erreur inconnue"
        return f"Erreur whisper-cli : {error_msg}"

    text = _parse_whisper_output(result.stdout)
    return text if text else "(aucun texte transcrit)"


def run_transcription(on_result):
    """Lance la transcription dans un thread daemon sans bloquer l'appelant.

    Démarre `transcribe()` dans un `threading.Thread(daemon=True)` puis
    appelle `on_result` avec le texte retourné, depuis ce même thread.
    L'appelant reçoit le contrôle immédiatement.

    Si une transcription est déjà en cours, l'appel est ignoré silencieusement
    (protection contre un double déclenchement par ex. arrêt manuel + timer).

    @param on_result {callable} Fonction appelée avec le texte transcrit
                    (str) une fois la transcription terminée. Elle est
                    invoquée depuis le thread de transcription — ne pas
                    y manipuler de widgets tkinter directement.
    @returns {None}
    """
    global _transcription_running

    with _transcription_lock:
        if _transcription_running:
            # Une transcription tourne déjà ; on abandonne silencieusement.
            return
        _transcription_running = True

    def _worker():
        global _transcription_running
        try:
            text = transcribe()
            on_result(text)
        finally:
            with _transcription_lock:
                _transcription_running = False

    threading.Thread(target=_worker, daemon=True).start()


def main():
    """Point d'entrée de l'application.

    Instancie la fenêtre icône micro et démarre la boucle principale tkinter.

    @returns {None}
    """
    def _on_stop():
        # Arrête l'enregistrement ; si un WAV valide a été produit, lance
        # la transcription en arrière-plan et affiche la bulle de résultat
        # dans le thread tkinter via app.after(0, ...).
        success = stop_recording()
        if success:
            run_transcription(on_result=lambda text: app.after(0, lambda: app.show_bubble(text)))

    def on_wake_word():
        """Stub de déclenchement post-wake-word (complété en Phase 6-C).

        Appelé hors thread tkinter par vad._process_segment(). Toutes les
        mises à jour UI sont donc planifiées via app.after(0, ...).
        Si un enregistrement clic est déjà en cours, l'appel est ignoré
        silencieusement pour éviter un conflit de stream audio.
        """
        # Vérifier si un enregistrement clic est déjà actif
        with _transcription_lock:
            if _transcription_running:
                return

        print("Wake word détecté — enregistrement à venir (Phase 6-C)")
        # Remettre l'icône en état idle : l'écoute VAD s'est arrêtée
        # d'elle-même dans vad._process_segment() avant cet appel.
        app.after(0, lambda: app.set_listening_state(False))

    def on_voice_listen_toggle(active: bool):
        """Démarre ou arrête l'écoute VAD selon le toggle du menu contextuel.

        Appelé dans le thread tkinter par MicIcon._toggle_voice_listening().

        @param active {bool} True = activer l'écoute, False = la désactiver.
        """
        if active:
            vad.start_listening(on_wake_word)
        else:
            vad.stop_listening()
        app.set_listening_state(active)

    app = MicIcon(
        on_record_start=start_recording,
        on_record_stop=_on_stop,
        on_record_cancel=cancel_recording,
        on_quit=cleanup,
        on_voice_listen_toggle=on_voice_listen_toggle,
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
