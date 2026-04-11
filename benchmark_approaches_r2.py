"""benchmark_approaches_r2.py — Round 2 : cpu_threads, beam=2, turbo.

Usage :
    python benchmark_approaches_r2.py

Teste des variantes supplémentaires sur le WAV existant et sauvegarde :
- reports/benchmark_approaches_r2_<timestamp>.md
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
        "id": "r2_ref",
        "name": "Référence (small beam=1)",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
        "cpu_threads": 0,  # 0 = laisser faster-whisper décider
    },
    {
        "id": "r2_threads4",
        "name": "small beam=1 threads=4",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
        "cpu_threads": 4,
    },
    {
        "id": "r2_threads8",
        "name": "small beam=1 threads=8",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
        "cpu_threads": 8,
    },
    {
        "id": "r2_threads12",
        "name": "small beam=1 threads=12",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
        "cpu_threads": 12,
    },
    {
        "id": "r2_beam2",
        "name": "small beam=2",
        "model": "small",
        "beam_size": 2,
        "vad_filter": True,
        "cpu_threads": 0,
    },
    {
        "id": "r2_turbo",
        "name": "turbo (large-v3-turbo)",
        "model": "turbo",
        "beam_size": 1,
        "vad_filter": True,
        "cpu_threads": 0,
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
    cpu_threads = approach["cpu_threads"]

    print(f"   Modèle      : {model_name}")
    print(f"   beam_size   : {beam_size}")
    print(f"   vad_filter  : {vad_filter}")
    print(f"   cpu_threads : {cpu_threads if cpu_threads > 0 else 'auto'}")
    print(f"   Chargement du modèle...")

    kwargs = dict(device="cpu", compute_type="int8")
    if cpu_threads > 0:
        kwargs["cpu_threads"] = cpu_threads

    t_load_start = time.time()
    model = WhisperModel(model_name, **kwargs)
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
    report_path = os.path.join(report_dir, f"benchmark_approaches_r2_{ts}.md")

    print("=" * 60)
    print("   BENCHMARK APPROCHES — ROUND 2")
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

    # Speedup par rapport à la référence r2_ref
    ref_infer = next(
        (r["infer_time"] for r in results if r["id"] == "r2_ref" and not r["failed"]),
        None,
    )
    # Speedup par rapport au baseline original (25.73s)
    baseline_original = 25.73

    print("=" * 60)
    print("   RESULTATS")
    print("=" * 60)
    print()

    header = f"{'Approche':<22} {'Inférence':>10} {'vs ref':>8} {'vs baseline':>12} {'Ratio':>7}"
    print(header)
    print("-" * len(header))

    for r in results:
        if r["failed"]:
            print(f"{r['id']:<22} {'ECHEC':>10}")
        else:
            vs_ref = (
                f"{ref_infer / r['infer_time']:.2f}x"
                if ref_infer and r["infer_time"] > 0
                else "—"
            )
            vs_baseline = f"{baseline_original / r['infer_time']:.2f}x"
            ratio = r["infer_time"] / AUDIO_DURATION
            print(f"{r['id']:<22} {r['infer_time']:>9.2f}s {vs_ref:>8} {vs_baseline:>12} {ratio:>6.2f}x")

    print()

    with open(report_path, "w") as f:
        f.write(f"# Benchmark Approches Round 2 — {ts}\n\n")
        f.write("## Fichier audio\n\n")
        f.write(f"| Paramètre | Valeur |\n|-----------|--------|\n")
        f.write(f"| Fichier | `profiling/20260410_233138.wav` |\n")
        f.write(f"| Durée | {AUDIO_DURATION}s |\n\n")
        f.write("## Référence Round 1\n\n")
        f.write("| Config | Inférence |\n|--------|----------|\n")
        f.write("| baseline (small, beam=5, vad=True) | 25.73s |\n")
        f.write("| voie1 (small, beam=1, vad=True) | 18.70s |\n\n")
        f.write("## Résultats Round 2\n\n")
        f.write("| Approche | Modèle | beam | threads | Inférence | vs baseline | Ratio |\n")
        f.write("|----------|--------|------|---------|-----------|-------------|-------|\n")

        for r in results:
            if r["failed"]:
                error = r.get("error", "inconnu")[:60]
                f.write(f"| {r['id']} | `{r['model']}` | {r['beam_size']} | {r['cpu_threads']} | ECHEC | — | — |\n")
            else:
                vs_baseline = f"{baseline_original / r['infer_time']:.2f}x"
                ratio = r["infer_time"] / AUDIO_DURATION
                f.write(
                    f"| {r['id']} | `{r['model']}` | {r['beam_size']} | {r['cpu_threads'] or 'auto'}"
                    f" | {r['infer_time']:.2f}s | {vs_baseline} | {ratio:.2f}x |\n"
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
