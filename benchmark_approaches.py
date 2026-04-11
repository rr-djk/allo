"""benchmark_approaches.py — Compare 6 approches de transcription faster-whisper.

Usage :
    python benchmark_approaches.py

Charge un fichier WAV existant, teste chaque configuration indépendamment
(chargement modèle + inférence), puis sauvegarde :
- reports/benchmark_approaches_<timestamp>.md — rapport de comparaison
"""
import os
import sys
import time
import wave
from datetime import datetime

import numpy as np

from faster_whisper import WhisperModel


WAV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiling", "20260410_233138.wav")
AUDIO_DURATION = 120  # secondes

APPROACHES = [
    {
        "id": "baseline",
        "name": "Baseline (actuel)",
        "model": "small",
        "beam_size": 5,
        "vad_filter": True,
    },
    {
        "id": "voie1",
        "name": "beam_size=1",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
    },
    {
        "id": "voie2",
        "name": "model base",
        "model": "base",
        "beam_size": 5,
        "vad_filter": True,
    },
    {
        "id": "voie3",
        "name": "vad_filter=False",
        "model": "small",
        "beam_size": 5,
        "vad_filter": False,
    },
    {
        "id": "voie4",
        "name": "base+beam1",
        "model": "base",
        "beam_size": 1,
        "vad_filter": False,
    },
    {
        "id": "voie5",
        "name": "distil-small.fr",
        "model": "Systran/faster-distil-whisper-small.fr",
        "beam_size": 5,
        "vad_filter": True,
    },
]


def load_wav_as_float32(path):
    with wave.open(path, 'r') as wf:
        raw = wf.readframes(wf.getnframes())
    audio_int16 = np.frombuffer(raw, dtype=np.int16)
    return audio_int16.astype(np.float32) / 32768.0


def run_approach(approach, audio):
    model_name = approach["model"]
    beam_size = approach["beam_size"]
    vad_filter = approach["vad_filter"]

    print(f"   Modèle      : {model_name}")
    print(f"   beam_size   : {beam_size}")
    print(f"   vad_filter  : {vad_filter}")
    print(f"   Chargement du modèle...")

    t_load_start = time.time()
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    t_load_end = time.time()
    load_time = t_load_end - t_load_start
    print(f"   Modèle chargé en {load_time:.2f}s")

    print(f"   Transcription en cours...")
    t_infer_start = time.time()

    if vad_filter:
        segments, _ = model.transcribe(
            audio,
            language="fr",
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
    else:
        segments, _ = model.transcribe(
            audio,
            language="fr",
            beam_size=beam_size,
            vad_filter=False,
        )

    # Consume the generator to complete inference
    text = " ".join(seg.text.strip() for seg in segments).strip()

    t_infer_end = time.time()
    infer_time = t_infer_end - t_infer_start
    total_time = t_infer_end - t_load_start

    print(f"   Inférence   : {infer_time:.2f}s")
    print(f"   Total       : {total_time:.2f}s")

    return {
        "load_time": load_time,
        "infer_time": infer_time,
        "total_time": total_time,
        "text": text,
        "failed": False,
    }


def run():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"benchmark_approaches_{ts}.md")

    print("=" * 60)
    print("   BENCHMARK APPROCHES DE TRANSCRIPTION")
    print("=" * 60)
    print()
    print(f"   Fichier audio : {WAV_PATH}")
    print(f"   Durée audio   : {AUDIO_DURATION}s")
    print()

    print("   Chargement du fichier WAV...")
    audio = load_wav_as_float32(WAV_PATH)
    print(f"   {len(audio)} échantillons chargés")
    print()

    results = []

    for i, approach in enumerate(APPROACHES, 1):
        print(f"[{i}/{len(APPROACHES)}] {approach['id']} — {approach['name']}")
        print("-" * 40)

        try:
            result = run_approach(approach, audio)
        except Exception as e:
            print(f"   ECHEC : {e}")
            result = {
                "load_time": 0.0,
                "infer_time": 0.0,
                "total_time": 0.0,
                "text": "",
                "failed": True,
                "error": str(e),
            }

        results.append({**approach, **result})
        print()

    # Compute speedup relative to baseline inference time
    baseline_infer = next(
        (r["infer_time"] for r in results if r["id"] == "baseline" and not r["failed"]),
        None,
    )

    print("=" * 60)
    print("   RESULTATS")
    print("=" * 60)
    print()

    header = f"{'Approche':<20} {'Temps total':>12} {'Inférence':>10} {'Speedup':>9} {'Ratio':>7}"
    separator = "-" * len(header)
    print(header)
    print(separator)

    for r in results:
        if r["failed"]:
            print(f"{r['id']:<20} {'ECHEC':>12} {'':>10} {'':>9} {'':>7}")
        else:
            speedup = (
                f"{baseline_infer / r['infer_time']:.2f}x"
                if baseline_infer and r["infer_time"] > 0
                else "—"
            )
            ratio = r["infer_time"] / AUDIO_DURATION
            print(
                f"{r['id']:<20} {r['total_time']:>11.2f}s {r['infer_time']:>9.2f}s"
                f" {speedup:>9} {ratio:>6.2f}x"
            )

    print()

    # Save markdown report
    with open(report_path, "w") as f:
        f.write(f"# Benchmark Approches — {ts}\n\n")
        f.write("## Fichier audio\n\n")
        f.write(f"| Paramètre | Valeur |\n")
        f.write(f"|-----------|--------|\n")
        f.write(f"| Fichier | `{WAV_PATH}` |\n")
        f.write(f"| Durée | {AUDIO_DURATION}s |\n\n")
        f.write("## Résultats\n\n")
        f.write("| Approche | Nom | Modèle | beam_size | vad_filter | Temps total | Temps inférence | Speedup | Ratio |\n")
        f.write("|----------|-----|--------|-----------|------------|-------------|-----------------|---------|-------|\n")

        for r in results:
            if r["failed"]:
                error = r.get("error", "inconnu")
                f.write(
                    f"| {r['id']} | {r['name']} | `{r['model']}` | {r['beam_size']}"
                    f" | {r['vad_filter']} | ECHEC | ECHEC | — | — |\n"
                )
            else:
                speedup = (
                    f"{baseline_infer / r['infer_time']:.2f}x"
                    if baseline_infer and r["infer_time"] > 0
                    else "—"
                )
                ratio = r["infer_time"] / AUDIO_DURATION
                f.write(
                    f"| {r['id']} | {r['name']} | `{r['model']}` | {r['beam_size']}"
                    f" | {r['vad_filter']} | {r['total_time']:.2f}s"
                    f" | {r['infer_time']:.2f}s | {speedup} | {ratio:.2f}x |\n"
                )

        f.write("\n## Transcriptions\n\n")
        for r in results:
            f.write(f"### {r['id']} — {r['name']}\n\n")
            if r["failed"]:
                f.write(f"**ECHEC** : {r.get('error', 'inconnu')}\n\n")
            else:
                f.write(f"```\n{r['text']}\n```\n\n")

        f.write(f"_Généré le {datetime.now().isoformat()}_\n")

    print(f"   Rapport sauvegardé : {report_path}")
    print()
    print("=" * 60)
    print("   TERMINE")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n   Annulé")
        sys.exit(1)
