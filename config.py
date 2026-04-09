"""config.py — Constantes partagées et utilitaires de transcription minimaux.

Ce module centralise les symboles utilisés à la fois par record.py et vad.py,
afin d'éviter l'import circulaire que provoquerait une référence directe entre
ces deux modules.

Contient :
- Les constantes audio et de configuration (SAMPLE_RATE, CHANNELS, SILENCE_DURATION,
  WAKE_WORD, FASTER_WHISPER_TINY, FASTER_WHISPER_MAIN)
- La fonction transcribe_tiny(), utilisée par vad.py pour transcrire les segments
  de parole avec le modèle faster-whisper tiny

Les constantes propres à record.py (TEMP_WAV, MAX_DURATION, MIN_DURATION,
FASTER_WHISPER_MAIN, WAKE_WORD_VARIANTS…) restent dans record.py et ne sont pas
exposées ici.
"""

import os
import threading

import numpy as np


def _get_device_and_compute_type():
    """Detect best device for faster-whisper.

    Checks for CUDA availability via torch and returns the optimal
    device/compute_type pair for inference performance.

    @returns {tuple} (device: str, compute_type: str)
                    - ("cuda", "float16") if GPU available
                    - ("cpu", "int8") otherwise
    """
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda", "float16"
    except ImportError:
        pass
    return "cpu", "int8"

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
WAKE_WORD = "nadia"

# Modèle faster-whisper pour la détection du wake word.
# Accepte un nom HuggingFace (ex. "tiny") ou un chemin local absolu vers un
# répertoire CTranslate2. faster-whisper télécharge automatiquement depuis
# Systran/faster-whisper-<nom> si c'est un nom de modèle.
# La variable d'environnement FASTER_WHISPER_TINY prend le dessus si définie.
FASTER_WHISPER_TINY = os.getenv("FASTER_WHISPER_TINY", "tiny")
# Modèle faster-whisper pour la transcription principale.
# La variable d'environnement FASTER_WHISPER_MAIN prend le dessus si définie.
# En mode anglais (ALLO_LANGUAGE=en), bascule automatiquement sur "base.en".
_default_main = "small.en" if os.getenv("ALLO_LANGUAGE", "fr") == "en" else "small"
FASTER_WHISPER_MAIN = os.getenv("FASTER_WHISPER_MAIN", _default_main)

# Langue de transcription : "fr" par défaut, surchargeable via ALLO_LANGUAGE.
LANGUAGE = os.getenv("ALLO_LANGUAGE", "fr")

# Singleton du modèle faster-whisper tiny (chargé une fois, réutilisé)
_fw_tiny_model = None
_fw_tiny_lock = threading.Lock()


def transcribe_tiny(audio: "np.ndarray | str") -> str:
    """Transcrit de l'audio via faster-whisper avec le modèle tiny.

    Charge WhisperModel en mémoire de façon paresseuse et thread-safe
    (un seul chargement pour toute la durée de vie du processus).
    Langue forcée à "fr" pour améliorer la transcription de "allo".

    Le verrou _fw_tiny_lock protège uniquement le chargement du modèle ;
    l'inférence s'exécute hors du verrou pour maximiser le débit.

    @param audio {np.ndarray | str} Tableau float32 normalisé (-1.0–1.0) ou
                 chemin absolu vers un fichier WAV.
    @returns {str} Texte transcrit nettoyé, message d'erreur préfixé
                   "Erreur : " si le modèle est absent ou si faster-whisper
                   lève une exception, ou "(aucun texte transcrit)" si vide.
    @note Retourne toujours une str non-None.
    """
    global _fw_tiny_model

    with _fw_tiny_lock:
        if _fw_tiny_model is None:
            from faster_whisper import WhisperModel
            device, compute_type = _get_device_and_compute_type()
            _fw_tiny_model = WhisperModel(
                FASTER_WHISPER_TINY,
                device=device,
                compute_type=compute_type,
            )

    # Inference outside lock - allows concurrent transcriptions
    try:
        segments, _ = _fw_tiny_model.transcribe(audio, language=LANGUAGE)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text if text else "(aucun texte transcrit)"
    except Exception as e:  # noqa: BLE001
        return f"Erreur : {e}"
