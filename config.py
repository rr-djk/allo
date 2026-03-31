"""config.py — Constantes partagées et utilitaires de transcription minimaux.

Ce module centralise les symboles utilisés à la fois par record.py et vad.py,
afin d'éviter l'import circulaire que provoquerait une référence directe entre
ces deux modules.

Contient :
- Les constantes audio et de configuration (SAMPLE_RATE, CHANNELS, SILENCE_DURATION,
  WAKE_WORD, WHISPER_BINARY, WHISPER_MODEL_TINY)
- La fonction transcribe_tiny(), utilisée par vad.py pour transcrire les segments
  de parole avec le modèle Whisper léger

Les constantes propres à record.py (TEMP_WAV, MAX_DURATION, MIN_DURATION,
WHISPER_MODEL, WAKE_WORD_VARIANTS…) restent dans record.py et ne sont pas
exposées ici.
"""

import os
import re
import subprocess
import threading

# Répertoire contenant ce fichier ; sert de base pour les chemins relatifs
# afin que l'application fonctionne quel que soit le répertoire de travail courant.
_BASE = os.path.dirname(os.path.abspath(__file__))

# Fréquence d'échantillonnage en Hz
SAMPLE_RATE = 16000  # Hz

# Nombre de canaux audio (1 = mono)
CHANNELS = 1  # mono

# Durée de silence (en secondes) marquant la fin d'une prise de parole
SILENCE_DURATION = 1.5  # secondes

# Mot de réveil attendu pour déclencher un enregistrement
WAKE_WORD = "allo record"

# Chemin absolu vers le binaire whisper-cli compilé depuis whisper.cpp.
# La variable d'environnement WHISPER_BINARY prend le dessus si définie.
WHISPER_BINARY = os.getenv(
    "WHISPER_BINARY",
    os.path.join(_BASE, "../../whisper.cpp/build/bin/whisper-cli"),
)

# Chemin absolu vers le modèle Whisper léger (format ggml, tiny multilingue).
# Utilisé par vad.py pour transcrire les segments de parole lors de l'écoute passive.
# Le modèle multilingue (tiny.bin) transcrit mieux "allo" que tiny.en qui le rend
# en "Hello"/"Allow" à cause de son entraînement uniquement anglophone.
# La variable d'environnement WHISPER_MODEL_TINY prend le dessus si définie.
WHISPER_MODEL_TINY = os.getenv(
    "WHISPER_MODEL_TINY",
    os.path.join(_BASE, "../../whisper.cpp/models/ggml-tiny.bin"),
)

# Chemin du fichier WAV silence utilisé pour préchauffer le page cache OS
# avant la première détection de wake word. Généré automatiquement si absent.
# La variable d'environnement WHISPER_WARMUP_WAV prend le dessus si définie.
WHISPER_WARMUP_WAV = os.getenv("WHISPER_WARMUP_WAV", "/tmp/allo_warmup_silence.wav")

# Modèle faster-whisper pour la détection du wake word.
# Accepte un nom HuggingFace (ex. "tiny") ou un chemin local absolu vers un
# répertoire CTranslate2. faster-whisper télécharge automatiquement depuis
# Systran/faster-whisper-<nom> si c'est un nom de modèle.
# La variable d'environnement FASTER_WHISPER_TINY prend le dessus si définie.
FASTER_WHISPER_TINY = os.getenv("FASTER_WHISPER_TINY", "tiny")
# Modèle faster-whisper pour la transcription principale.
# La variable d'environnement FASTER_WHISPER_MAIN prend le dessus si définie.
FASTER_WHISPER_MAIN = os.getenv("FASTER_WHISPER_MAIN", "small.en")

# Singleton du modèle faster-whisper tiny (chargé une fois, réutilisé)
_fw_tiny_model = None
_fw_tiny_lock = threading.Lock()


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


def transcribe_tiny(wav_path: str) -> str:
    """Transcrit un fichier WAV via faster-whisper avec le modèle tiny.

    Charge WhisperModel en mémoire de façon paresseuse et thread-safe
    (un seul chargement pour toute la durée de vie du processus).
    Langue forcée à "fr" pour améliorer la transcription de "allo".

    @param wav_path {str} Chemin absolu vers le fichier WAV à transcrire.
    @returns {str} Texte transcrit nettoyé, message d'erreur préfixé
                   "Erreur : " si le modèle est absent ou si faster-whisper
                   lève une exception, ou "(aucun texte transcrit)" si vide.
    @note Retourne toujours une str non-None.
    """
    global _fw_tiny_model

    with _fw_tiny_lock:
        if _fw_tiny_model is None:
            from faster_whisper import WhisperModel
            _fw_tiny_model = WhisperModel(
                FASTER_WHISPER_TINY,
                device="cpu",
                compute_type="int8",
            )

    try:
        segments, _ = _fw_tiny_model.transcribe(wav_path, language="fr")
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text if text else "(aucun texte transcrit)"
    except Exception as e:  # noqa: BLE001
        return f"Erreur : {e}"
