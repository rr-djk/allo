"""record.py — Configuration et point d'entrée de l'application record.

Contient :
- Les constantes de configuration (chemins Whisper, fichier temporaire, durées)
- La fonction main() qui instancie l'interface graphique et lance la boucle tkinter
"""

from ui import MicIcon


# Chemin absolu vers le binaire whisper-cli compilé depuis whisper.cpp
WHISPER_BINARY = "/chemin/vers/whisper.cpp/build/bin/whisper-cli"
# Chemin absolu vers le fichier modèle Whisper (format ggml)
WHISPER_MODEL  = "/chemin/vers/whisper.cpp/models/ggml-base.en.bin"
# Fichier WAV temporaire utilisé pendant l'enregistrement
TEMP_WAV       = "/tmp/record_temp.wav"
# Durée maximale d'un enregistrement en secondes (arrêt automatique au-delà)
MAX_DURATION   = 90    # secondes
# Durée minimale d'un enregistrement en secondes (en dessous, l'audio est ignoré)
MIN_DURATION   = 0.5   # secondes


def main():
    """Point d'entrée de l'application.

    Instancie la fenêtre icône micro et démarre la boucle principale tkinter.

    @returns {None}
    """
    app = MicIcon()
    app.mainloop()


if __name__ == "__main__":
    main()
