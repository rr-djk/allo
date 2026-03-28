---
status: todo
type: feature
priority: high
assigned_to: implementation-specialist
started_at: null
depends_on: ["phase3_thread_transcription_20260328-0013.md"]
files_touched: ["record.py"]
related_to: null
---

# main() — Brancher run_transcription sur stop_recording

Modifier `main()` pour enchaîner stop_recording → run_transcription.

## Comportement attendu
- Le callback `on_record_stop` passé à `MicIcon` : appelle `stop_recording()`, si `True` appelle `run_transcription(on_result=lambda text: print(text))`
- `_handle_auto_stop` conservé et branché de la même façon
- Aucun widget tkinter manipulé depuis le thread de transcription

## Livrable testable
Après relâche du clic, le texte transcrit s'affiche dans le terminal via `print`.
