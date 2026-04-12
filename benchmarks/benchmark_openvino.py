"""benchmark_openvino.py — Comparaison faster-whisper CPU vs OpenVINO.

Mesure le temps d'inférence (warm) sur l'audio de référence pour :
  1. faster-whisper small (baseline actuelle)
  2. OpenVINO Whisper small via optimum-intel

Audio de référence : profiling/20260410_233138.wav (120s, FR)
"""
import os
import sys
import time
import wave
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_FILE = os.path.join(_PROJECT_ROOT, "profiling/20260410_233138.wav")


def load_audio(path: str) -> np.ndarray:
    with wave.open(path, "rb") as wf:
        if wf.getframerate() != 16000:
            raise ValueError(f"Sample rate must be 16000, got {wf.getframerate()}")
        frames = wf.readframes(wf.getnframes())
        return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def bench_faster_whisper(audio: np.ndarray, duration_s: float) -> dict:
    from faster_whisper import WhisperModel

    model = WhisperModel("small", device="cpu", compute_type="int8")

    # Warm-up
    list(model.transcribe(audio[:16000], language="fr")[0])

    # Mesure
    t0 = time.perf_counter()
    segments, _ = model.transcribe(
        audio,
        language="fr",
        beam_size=1,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )
    text = " ".join(s.text.strip() for s in segments)
    elapsed = time.perf_counter() - t0

    return {
        "engine": "faster-whisper (baseline)",
        "model": "small / int8 / beam=1",
        "inference_s": round(elapsed, 2),
        "rtf": round(elapsed / duration_s, 3),
        "text_preview": text[:120],
    }


def bench_openvino(audio: np.ndarray, duration_s: float) -> dict:
    from transformers import AutoProcessor, pipeline
    from optimum.intel import OVModelForSpeechSeq2Seq

    model_id = "openai/whisper-small"
    cache_dir = os.path.join(_PROJECT_ROOT, ".cache", "openvino_whisper_small")

    print("  Chargement modèle OpenVINO (cache si déjà compilé)…")
    t_load = time.perf_counter()
    processor = AutoProcessor.from_pretrained(model_id)
    model = OVModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        export=True,
        cache_dir=cache_dir,
        compile=True,
    )
    load_elapsed = time.perf_counter() - t_load
    print(f"  Chargement terminé en {load_elapsed:.1f}s")

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=30,
    )

    # Warm-up sur 1s de silence
    pipe(np.zeros(16000, dtype=np.float32), generate_kwargs={"language": "fr", "task": "transcribe"})

    # Mesure
    t0 = time.perf_counter()
    result = pipe(audio.copy(), generate_kwargs={"language": "fr", "task": "transcribe"})
    elapsed = time.perf_counter() - t0
    text = result["text"] if isinstance(result, dict) else result[0]["text"]

    return {
        "engine": "OpenVINO (optimum-intel)",
        "model": "whisper-small / OV",
        "inference_s": round(elapsed, 2),
        "rtf": round(elapsed / duration_s, 3),
        "text_preview": text[:120],
        "load_s": round(load_elapsed, 1),
    }


def print_result(r: dict, label: str) -> None:
    print(f"\n{'─'*55}")
    print(f"  {label}")
    print(f"{'─'*55}")
    print(f"  Moteur     : {r['engine']}")
    print(f"  Modèle     : {r['model']}")
    print(f"  Inférence  : {r['inference_s']}s")
    print(f"  RTF        : {r['rtf']}x")
    if "load_s" in r:
        print(f"  Chargement : {r['load_s']}s (hors mesure)")
    print(f"  Texte      : {r['text_preview']}…")


def main():
    print(f"Audio : {AUDIO_FILE}")
    audio = load_audio(AUDIO_FILE)
    duration_s = len(audio) / 16000
    print(f"Durée : {duration_s:.1f}s\n")

    results = []

    print("▶ [1/2] faster-whisper baseline…")
    r1 = bench_faster_whisper(audio, duration_s)
    results.append(r1)
    print_result(r1, "1/2 — faster-whisper baseline")

    print("\n▶ [2/2] OpenVINO (optimum-intel)…")
    try:
        r2 = bench_openvino(audio, duration_s)
        results.append(r2)
        print_result(r2, "2/2 — OpenVINO")
    except Exception as e:
        print(f"  ÉCHEC OpenVINO : {e}")
        results.append({"engine": "OpenVINO", "error": str(e)})

    # Synthèse
    print(f"\n{'═'*55}")
    print("  SYNTHÈSE")
    print(f"{'═'*55}")
    print(f"  {'Moteur':<35} {'Inférence':>10}  {'RTF':>6}")
    print(f"  {'─'*35} {'─'*10}  {'─'*6}")
    for r in results:
        if "error" in r:
            print(f"  {r['engine']:<35} {'ÉCHEC':>10}")
        else:
            speedup = ""
            if len(results) > 1 and r != results[0] and "inference_s" in results[0]:
                sp = results[0]["inference_s"] / r["inference_s"]
                speedup = f"  ({sp:+.2f}x vs baseline)" if sp != 1.0 else ""
            print(f"  {r['engine']:<35} {r['inference_s']:>8.2f}s  {r['rtf']:>6.3f}x{speedup}")
    print()


if __name__ == "__main__":
    main()
