"""record.py — Configuration et point d'entrée de l'application record.

Contient :
- Les constantes de configuration (chemins Whisper, fichier temporaire, durées)
- La fonction main() qui instancie l'interface graphique et lance la boucle tkinter
"""

import re
import threading
import time

import numpy as np

import audio
import vad
from config import CHANNELS, FASTER_WHISPER_MAIN, LANGUAGE, SAMPLE_RATE, SILENCE_DURATION, WAKE_WORD
from ui import MicIcon

# Variantes proches du wake word produites par Whisper (transcriptions erronées connues)
# WAKE_WORD lui-même est défini dans config.py et importé en haut de ce fichier.
_WAKE_WORD_VARIANTS = []
# Singleton du modèle faster-whisper principal (chargé une fois, réutilisé)
_fw_main_model = None
_fw_main_lock = threading.Lock()

# Durée minimale d'un enregistrement en secondes (en dessous, l'audio est ignoré)
MIN_DURATION = 0.5  # secondes
# SAMPLE_RATE, CHANNELS, SILENCE_DURATION importés depuis config.py


# Blocs audio bruts accumulés par le callback du stream d'entrée
_audio_frames = []
# Verrou protégeant stop_recording() contre un double appel simultané
# (relâchement du bouton au même instant)
_stop_lock = threading.Lock()
# Vrai quand un thread de transcription est en cours d'exécution ;
# protège contre un double déclenchement (ex. : arrêt manuel simultané)
_transcription_running = False
# Verrou protégeant la lecture/écriture de _transcription_running
_transcription_lock = threading.Lock()


def start_recording():
    """Démarre la capture audio depuis le microphone par défaut.

    Réinitialise le tampon interne puis ouvre un stream via
    `audio.open_stream()`. Chaque bloc reçu est ajouté à `_audio_frames`.

    @returns {None}
    """
    global _audio_frames

    _audio_frames = []

    def _callback(indata, frames, time, status):  # noqa: ARG001
        _audio_frames.append(indata.copy())

    audio.open_stream(_callback)


def stop_recording():
    """Arrête la capture audio et retourne les données audio sous forme de ndarray.

    Ferme le stream via `audio.close_stream()`.
    Calcule la durée réelle et retourne un ndarray float32 normalisé
    (valeurs entre -1.0 et 1.0) si la durée est suffisante, None sinon.

    Phase 1 : plus d'aller-retour par /tmp/record_temp.wav — faster-whisper
    accepte un ndarray float32 directement.

    @returns {np.ndarray|None} Audio float32 normalisé, ou None si le tampon
                               est vide ou la durée inférieure à MIN_DURATION.
    """
    with _stop_lock:
        # Ferme le stream ; le callback ne s'exécutera plus jamais après cela.
        # On peut lire _audio_frames en toute sécurité à partir d'ici.
        audio.close_stream()

        if not _audio_frames:
            return None

        # Concaténer une seule fois : ce tableau sert à la fois au calcul de
        # durée et à la conversion float32 (évite un second np.concatenate).
        data_int16 = np.concatenate(_audio_frames, axis=0)
        duration = len(data_int16) / SAMPLE_RATE

        if duration < MIN_DURATION:
            return None

        # Normalisation int16 → float32 [-1.0, 1.0], identique au pattern de vad.py
        return (data_int16.astype(np.float32) / 32768.0).flatten()


def cancel_recording():
    """Annule un enregistrement en cours sans produire de fichier WAV.

    Ferme le stream via `audio.close_stream()` et vide `_audio_frames`.
    Ne crée pas de fichier WAV et ne déclenche pas de transcription.
    Utilisé quand l'utilisateur glisse la fenêtre au lieu de cliquer pour enregistrer.

    @returns {None}
    """
    global _audio_frames

    with _stop_lock:
        audio.close_stream()

        # Vider le tampon : l'audio capturé pendant le drag est abandonné
        _audio_frames = []


def cleanup():
    """Ferme le stream si un enregistrement est en cours.

    Arrête également l'écoute VAD si elle est active, afin qu'aucun thread
    non-daemon ni stream sounddevice ne bloque la fin du processus.

    @returns {None}
    """
    # Arrêter l'écoute VAD en premier : elle possède son propre stream.
    # Les deux appels sont idempotents ; on absorbe toute exception résiduelle
    # (ex. stream sounddevice déjà fermé si une transcription était en cours).
    try:
        vad.stop_listening()
        vad.stop_silence_detection()
    except Exception:  # noqa: BLE001
        pass

    with _stop_lock:
        audio.close_stream()


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


def transcribe(audio: np.ndarray) -> str:
    """Transcrit un ndarray audio float32 via faster-whisper.

    Charge WhisperModel en mémoire de façon paresseuse et thread-safe.
    Phase 1 : accepte directement un ndarray float32 normalisé [-1.0, 1.0]
    au lieu d'un chemin de fichier WAV — aucun aller-retour disque.

    Le verrou _fw_main_lock protège uniquement le chargement du modèle ;
    l'inférence s'exécute hors du verrou pour maximiser le débit.

    @param audio {np.ndarray} Audio float32 normalisé produit par stop_recording().
    @returns {str} Texte transcrit nettoyé, ou un message d'erreur
                   préfixé par « Erreur : », ou « (aucun texte transcrit) »
                   si la sortie est vide.
    @note Retourne toujours une str non-None.
    """
    global _fw_main_model

    with _fw_main_lock:
        if _fw_main_model is None:
            from faster_whisper import WhisperModel, BatchedInferencePipeline
            from config import _get_device_and_compute_type, _get_cpu_threads
            device, compute_type = _get_device_and_compute_type()
            cpu_threads = _get_cpu_threads()
            base_model = WhisperModel(
                FASTER_WHISPER_MAIN,
                device=device,
                compute_type=compute_type,
                cpu_threads=cpu_threads,
            )
            _fw_main_model = BatchedInferencePipeline(model=base_model)

    # Inference outside lock - allows concurrent transcriptions
    try:
        segments, _ = _fw_main_model.transcribe(
            audio,
            language=LANGUAGE,
            beam_size=1,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        return segments
    except Exception as e:  # noqa: BLE001
        return f"Erreur : {e}"


def run_transcription(audio: np.ndarray, on_segment, on_complete):
    """Lance la transcription dans un thread daemon sans bloquer l'appelant.

    Démarre `transcribe()` dans un `threading.Thread(daemon=True)` puis
    appelle `on_segment` pour chaque segment produit par Whisper, et enfin
    `on_complete` avec le texte final une fois terminé.
    L'appelant reçoit le contrôle immédiatement.

    Si une transcription est déjà en cours, l'appel est ignoré silencieusement.

    @param audio      {np.ndarray} Audio float32 normalisé produit par stop_recording().
    @param on_segment {callable}   Fonction appelée avec le texte cumulé (str)
                       à chaque nouveau segment produit. Invoquée hors thread UI.
    @param on_complete {callable}   Fonction appelée avec le texte final (str)
                       une fois terminé. Invoquée hors thread UI.
    @returns {None}
    """
    global _transcription_running

    with _transcription_lock:
        if _transcription_running:
            return
        _transcription_running = True

    def _worker():
        global _transcription_running
        try:
            result = transcribe(audio)
            if isinstance(result, str):
                # Cas d'erreur (message préfixé "Erreur :")
                on_complete(result)
            else:
                # C'est un générateur de segments
                full_text = []
                for segment in result:
                    text = segment.text.strip()
                    if text:
                        full_text.append(text)
                        on_segment(" ".join(full_text))
                
                final = " ".join(full_text)
                on_complete(final if final else "(aucun texte transcrit)")
        finally:
            with _transcription_lock:
                _transcription_running = False

    threading.Thread(target=_worker, daemon=True).start()


def main():
    """Point d'entrée de l'application.

    Instancie la fenêtre icône micro et démarre la boucle principale tkinter.

    @returns {None}
    """
    def _restart_vad_if_active():
        """Relance le stream VAD si l'écoute vocale est encore activée.

        Appelé dans le thread tkinter après chaque enregistrement clic
        (avec ou sans WAV valide). Notifie l'utilisateur via show_bubble()
        si start_listening() signale une erreur (binaire ou modèle absent).
        """
        if not app._voice_listening:
            return
        erreur = vad.start_listening(on_wake_word)
        if erreur is not None:
            # Modèle ou binaire absent : désactiver le toggle et informer
            app._voice_listening = False
            app.set_listening_state(False)
            app.show_bubble(erreur)
        else:
            app.set_listening_state(True)

    def _on_record_start_safe():
        # Ferme le stream VAD avant d'ouvrir le stream d'enregistrement pour
        # éviter le conflit "Un stream audio est déjà ouvert." dans audio.py.
        if vad.is_listening():
            vad.stop_listening()
        start_recording()

    def _on_stop():
        # Arrête l'enregistrement ; si un ndarray valide a été produit, lance
        # la transcription en arrière-plan et affiche la bulle de résultat
        # dans le thread tkinter via app.after(0, ...).
        audio_data = stop_recording()
        if audio_data is not None:
            app.set_transcribing_state(True)

            def _on_segment(text):
                # Supprimé l'affichage progressif - affichage du résultat final uniquement
                pass

            def _on_complete(text):
                # Relancer le stream VAD dans le thread tkinter une fois la
                # transcription terminée, puis afficher la bulle de résultat.
                app.after(0, lambda: app.set_transcribing_state(False))
                app.after(0, _restart_vad_if_active)
                app.after(0, lambda: app.show_bubble(text))

            run_transcription(audio=audio_data, on_segment=_on_segment, on_complete=_on_complete)
        else:
            # Enregistrement trop court ou tampon vide : relancer quand même
            # le stream VAD si l'écoute vocale est encore active.
            _restart_vad_if_active()

    def on_wake_word():
        """Déclenche le pipeline d'enregistrement après détection du wake word.

        Appelé hors thread tkinter par vad._process_segment(). Toutes les
        mises à jour UI sont donc planifiées via app.after(0, ...).
        Si un enregistrement clic est déjà en cours (transcription active),
        l'appel est ignoré silencieusement pour éviter un conflit de stream.
        """
        with _transcription_lock:
            if _transcription_running:
                return  # enregistrement clic en cours — ignorer

        # Démarrer l'enregistrement principal et passer l'icône en bleu
        app.after(0, start_recording)
        app.after(0, lambda: app.set_recording_state(True))

        # Démarrer la détection de silence pour l'arrêt automatique
        def on_silence():
            # Appelé hors thread tkinter par vad._fire_silence()
            app.after(0, _on_wake_stop)

        vad.start_silence_detection(on_silence)

    def _on_wake_stop():
        # Exécuté dans le thread tkinter (planifié via app.after(0, ...))
        audio_data = stop_recording()
        if audio_data is not None:
            app.set_transcribing_state(True)

            def _on_segment(text):
                # Supprimé l'affichage progressif - affichage du résultat final uniquement
                pass

            def _on_complete(text):
                # Remettre l'icône et relancer le VAD depuis le thread tkinter,
                # une fois la transcription terminée. set_transcribing_state(False)
                # doit précéder set_listening_state pour éviter que le vert soit
                # immédiatement écrasé par l'ambre.
                app.after(0, lambda: app.set_transcribing_state(False))
                if app._voice_listening:
                    app.after(0, lambda: vad.start_listening(on_wake_word))
                    app.after(0, lambda: app.set_listening_state(True))
                app.after(0, lambda: app.show_bubble(_strip_wake_word(text)))

            run_transcription(audio=audio_data, on_segment=_on_segment, on_complete=_on_complete)
        else:
            # Enregistrement trop court ou tampon vide : relancer le VAD
            # immédiatement sans passer par la transcription.
            if app._voice_listening:
                vad.start_listening(on_wake_word)
                app.set_listening_state(True)
            else:
                app.set_recording_state(False)

    def on_voice_listen_toggle(active: bool):
        """Démarre ou arrête l'écoute VAD selon le toggle du menu contextuel.

        Appelé dans le thread tkinter par MicIcon._toggle_voice_listening().

        Si start_listening() retourne un message d'erreur (str), l'écoute
        n'est pas démarrée : l'erreur est affichée via show_bubble() et le
        toggle est remis en état OFF.

        @param active {bool} True = activer l'écoute, False = la désactiver.
        """
        if active:
            erreur = vad.start_listening(on_wake_word)
            if erreur is not None:
                # Modèle ou binaire absent : annuler le toggle et informer l'utilisateur
                app._voice_listening = False
                app.set_listening_state(False)
                app.after(0, lambda: app.show_bubble(erreur))
                return
        else:
            vad.stop_listening()
        app.set_listening_state(active)

    app = MicIcon(
        on_record_start=_on_record_start_safe,
        on_record_stop=_on_stop,
        on_record_cancel=cancel_recording,
        on_quit=cleanup,
        on_voice_listen_toggle=on_voice_listen_toggle,
    )

    def _warmup():
        silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
        from config import transcribe_tiny
        transcribe_tiny(silence)
        transcribe(silence)

    threading.Thread(target=_warmup, daemon=True).start()

    app.mainloop()


if __name__ == "__main__":
    main()
