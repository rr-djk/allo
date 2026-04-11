"""benchmark_approaches_r3.py — Round 3 : condition_on_previous_text.

Usage :
    python benchmark_approaches_r3.py

Teste l'impact de condition_on_previous_text sur la vitesse et la qualité.
"""
import os
import sys
import time
import wave
from datetime import datetime

import numpy as np
from faster_whisper import WhisperModel


WAV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiling", "20260410_233138.wav")
AUDIO_DURATION = 120

APPROACHES = [
    {
        "id": "r3_ref",
        "name": "small beam=1 (référence)",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
        "condition_on_previous_text": True,
    },
    {
        "id": "r3_no_condition",
        "name": "small beam=1 no_condition",
        "model": "small",
        "beam_size": 1,
        "vad_filter": True,
        "condition_on_previous_text": False,
    },
    {
        "id": "r3_base_no_condition",
        "name": "base beam=1 no_condition",
        "model": "base",
        "beam_size": 1,
        "vad_filter": True,
        "condition_on_previous_text": False,
    },
    {
        "id": "r3_small_beam5_no_condition",
        "name": "small beam=5 no_condition",
        "model": "small",
        "beam_size": 5,
        "vad_filter": True,
        "condition_on_previous_text": False,
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
    condition = approach["condition_on_previous_text"]

    print(f"   Modèle                    : {model_name}")
    print(f"   beam_size                 : {beam_size}")
    print(f"   condition_on_previous_text: {condition}")
    print(f"   Chargement du modèle...")

    t_load_start = time.time()
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    load_time = time.time() - t_load_start
    print(f"   Modèle chargé en {load_time:.2f}s")

    print(f"   Transcription en cours...")
    t_infer_start = time.time()

    segments, _ = model.transcribe(
        audio,
        language="fr",
        beam_size=beam_size,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        condition_on_previous_text=condition,
    )
    text = " ".join(seg.text.strip() for seg in segments).strip()

    infer_time = time.time() - t_infer_start
    print(f"   Inférence   : {infer_time:.2f}s")

    return {
        "load_time": load_time,
        "infer_time": infer_time,
        "text": text,
        "failed": False,
    }


def run():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"benchmark_approaches_r3_{ts}.md")

    print("=" * 60)
    print("   BENCHMARK APPROCHES — ROUND 3")
    print("=" * 60)
    print(f"\n   Fichier audio : {WAV_PATH}")
    print(f"   Durée audio   : {AUDIO_DURATION}s\n")

    audio = load_wav_as_float32(WAV_PATH)
    print(f"   {len(audio)} échantillons chargés\n")

    results = []

    for i, approach in enumerate(APPROACHES, 1):
        print(f"[{i}/{len(APPROACHES)}] {approach['id']} — {approach['name']}")
        print("-" * 40)

        try:
            result = run_approach(approach, audio)
        except Exception as e:
            print(f"   ECHEC : {e}")
            result = {"load_time": 0, "infer_time": 0, "text": "", "failed": True, "error": str(e)}

        results.append({**approach, **result})
        print()

    baseline_original = 25.73
    ref_infer = next((r["infer_time"] for r in results if r["id"] == "r3_ref" and not r["failed"]), None)

    print("=" * 60)
    print("   RESULTATS")
    print("=" * 60)
    print()

    header = f"{'Approche':<30} {'Inférence':>10} {'vs r3_ref':>10} {'vs original':>12}"
    print(header)
    print("-" * len(header))

    for r in results:
        if r["failed"]:
            print(f"{r['id']:<30} {'ECHEC':>10}")
        else:
            vs_ref = f"{ref_infer / r['infer_time']:.2f}x" if ref_infer and r["infer_time"] > 0 else "—"
            vs_orig = f"{baseline_original / r['infer_time']:.2f}x"
            print(f"{r['id']:<30} {r['infer_time']:>9.2f}s {vs_ref:>10} {vs_orig:>12}")

    print()

    with open(report_path, "w") as f:
        f.write(f"# Benchmark Approches Round 3 — {ts}\n\n")
        f.write("## Contexte\n\nTest de `condition_on_previous_text=False` pour casser ")
        f.write("la dépendance séquentielle entre segments.\n\n")
        f.write("## Résultats\n\n")
        f.write("| Approche | Modèle | beam | condition | Inférence | vs baseline (25.73s) |\n")
        f.write("|----------|--------|------|-----------|-----------|---------------------|\n")

        for r in results:
            if r["failed"]:
                f.write(f"| {r['id']} | `{r['model']}` | {r['beam_size']} | {r['condition_on_previous_text']} | ECHEC | — |\n")
            else:
                vs_orig = f"{baseline_original / r['infer_time']:.2f}x"
                f.write(
                    f"| {r['id']} | `{r['model']}` | {r['beam_size']}"
                    f" | {r['condition_on_previous_text']} | {r['infer_time']:.2f}s | {vs_orig} |\n"
                )

        f.write("\n## Transcriptions\n\n")
        for r in results:
            f.write(f"### {r['id']} — {r['name']}\n\n```\n{r.get('text', 'ECHEC')}\n```\n\n")

        f.write(f"_Généré le {datetime.now().isoformat()}_\n")

    print(f"   Rapport sauvegardé : {report_path}")
    print("\n" + "=" * 60)
    print("   TERMINE")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n   Annulé")
        sys.exit(1)
