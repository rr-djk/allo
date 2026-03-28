---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase1_micicon_window_20260328-0000.md", "phase1_micicon_drag_20260328-0001.md", "phase1_micicon_contextmenu_20260328-0002.md"]
files_touched: ["record.py"]
related_to: null
---

# record.py — main()

Créer `record.py` avec les constantes de configuration et la fonction `main()`.

## Comportement attendu
- Constantes en haut du fichier :
  ```python
  WHISPER_BINARY = "/chemin/vers/whisper.cpp/build/bin/whisper-cli"
  WHISPER_MODEL  = "/chemin/vers/whisper.cpp/models/ggml-base.en.bin"
  TEMP_WAV       = "/tmp/record_temp.wav"
  MAX_DURATION   = 90    # secondes
  MIN_DURATION   = 0.5   # secondes
  ```
- Fonction `main()` qui importe `MicIcon` depuis `ui.py`, l'instancie et appelle `mainloop()`
- Bloc `if __name__ == "__main__": main()`

## Livrable testable
`python3 record.py` affiche la fenêtre micro (identique à `python3 ui.py`).
