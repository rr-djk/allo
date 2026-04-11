"""benchmark_transcription.py — Mesure le délai de transcription.

Usage :
    python benchmark_transcription.py

Enregistre 2 minutes d'audio, transcrit, et sauvegarde :
- <timestamp>.wav       — audio enregistré
- <timestamp>_report.md — rapport de benchmark
"""
import os
import sys
import time
import wave
from datetime import datetime

import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE, FASTER_WHISPER_MAIN, LANGUAGE
from record import transcribe


def run():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = f"{ts}.wav"
    report_path = f"{ts}_report.md"

    DURATION = 120  # 2 minutes

    print("=" * 50)
    print("   BENCHMARK TRANSCRIPTION")
    print("=" * 50)
    print()
    print(f"🎙️  Enregistrement de {DURATION}s...")
    print("   Parle maintenant ! (Ctrl+C pour annuler)")
    print()

    audio_int16 = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
    )

    for i in range(DURATION, 0, -1):
        if i % 10 == 0:
            print(f"   ⏱  {i}s restantes...")
        time.sleep(1)
    sd.wait()

    print("   ✅ Enregistrement terminé")
    print()

    with wave.open(wav_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
    print(f"   💾 Audio : {wav_path}")
    print()

    audio_float32 = audio_int16.flatten().astype(np.float32) / 32768.0

    print(f"🔄 Transcription...")
    print(f"   Modèle : {FASTER_WHISPER_MAIN}")
    print(f"   Langue : {LANGUAGE}")
    print()

    start_time = time.time()
    result = transcribe(audio_float32)
    elapsed = time.time() - start_time

    ratio = elapsed / DURATION

    print()
    print("=" * 50)
    print("   RÉSULTATS")
    print("=" * 50)
    print(f"   Audio          : {DURATION}s")
    print(f"   Transcription   : {elapsed:.2f}s")
    print(f"   Ratio          : {ratio:.2f}x")
    print()
    print("   Texte transcrit :")
    print(f"   " + "─" * 20)
    for line in result.split('\n'):
        print(f"   {line}")
    print(f"   " + "─" * 20)
    print()

    with open(report_path, "w") as f:
        f.write(f"# Benchmark Transcription — {ts}\n\n")
        f.write("## Paramètres\n\n")
        f.write(f"| Paramètre | Valeur |\n")
        f.write(f"|-----------|--------|\n")
        f.write(f"| Modèle | `{FASTER_WHISPER_MAIN}` |\n")
        f.write(f"| Langue | `{LANGUAGE}` |\n")
        f.write(f"| Durée audio | {DURATION}s |\n")
        f.write(f"| Temps transcription | {elapsed:.2f}s |\n")
        f.write(f"| Ratio | {ratio:.2f}x |\n\n")
        f.write("## Transcription\n\n")
        f.write(f"```\n{result}\n```\n\n")
        f.write(f"_Généré le {datetime.now().isoformat()}_")

    print(f"   💾 Rapport : {report_path}")
    print()
    print("=" * 50)
    print("   TERMINÉ")
    print("=" * 50)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n   ❌ Annulé")
        sys.exit(1)
