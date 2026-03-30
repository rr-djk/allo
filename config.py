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

# Chemin absolu vers le modèle Whisper léger (format ggml, tiny.en).
# Utilisé par vad.py pour transcrire les segments de parole lors de l'écoute passive.
WHISPER_MODEL_TINY = os.path.join(_BASE, "../../whisper.cpp/models/ggml-tiny.en.bin")


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
    """Transcrit un fichier WAV via whisper-cli avec le modèle tiny.

    Vérifie l'existence du binaire et du modèle tiny avant l'appel, puis
    appelle whisper-cli en subprocess sur `wav_path`. Ne supprime pas le
    fichier WAV après l'appel (responsabilité de l'appelant).

    @param wav_path {str} Chemin absolu vers le fichier WAV à transcrire.
    @returns {str} Texte transcrit nettoyé, ou un message d'erreur
                   préfixé par « Erreur : » / « Erreur whisper-cli : »,
                   ou « (aucun texte transcrit) » si la sortie est vide.
    @note Retourne toujours une str non-None.
    """
    if not os.path.isfile(WHISPER_BINARY):
        return "Erreur : binaire whisper-cli introuvable"

    if not os.path.isfile(WHISPER_MODEL_TINY):
        return "Erreur : modèle Whisper tiny introuvable"

    result = subprocess.run(
        [WHISPER_BINARY, "-m", WHISPER_MODEL_TINY, "-f", wav_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # stderr peut être vide si whisper-cli écrit tout sur stdout
        error_msg = result.stderr.strip() or result.stdout.strip() or "erreur inconnue"
        return f"Erreur whisper-cli : {error_msg}"

    text = _parse_whisper_output(result.stdout)
    return text if text else "(aucun texte transcrit)"
