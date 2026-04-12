"""benchmark_optimizer.py — Test exhaustif des optimisations faster-whisper.

Usage:
    python benchmarks/benchmark_optimizer.py
"""
import os
import sys
import time
import wave

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

import numpy as np
import psutil

from faster_whisper import WhisperModel
import config


def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def load_audio(path):
    with wave.open(path, 'rb') as wf:
        params = wf.getparams()
        frames = wf.readframes(params.nframes)
        audio = np.frombuffer(frames, dtype=np.int16).flatten().astype(np.float32) / 32768.0
        return audio


def run_test(name, model_name, device, compute_type, cpu_threads=0, num_workers=1, 
             min_silence_ms=300, vad_filter=True, batched=False):
    print(f"\n--- Test: {name} ---")
    
    mem_start = get_memory_usage()
    
    start_load = time.time()
    base_model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads,
        num_workers=num_workers,
    )
    
    if batched:
        from faster_whisper import BatchedInferencePipeline
        model = BatchedInferencePipeline(model=base_model)
    else:
        model = base_model
    
    load_time = time.time() - start_load
    
    audio = load_audio(os.path.join(_PROJECT_ROOT, "profiling/20260410_233138.wav"))
    duration = len(audio) / 16000
    
    model.transcribe(audio[:16000], language=config.LANGUAGE)
    
    start_inf = time.time()
    segments, _ = model.transcribe(
        audio,
        language=config.LANGUAGE,
        beam_size=1,
        condition_on_previous_text=False,
        vad_filter=vad_filter,
        vad_parameters=dict(min_silence_duration_ms=min_silence_ms) if vad_filter else {},
    )
    segment_list = list(segments)
    text = " ".join(seg.text.strip() for seg in segment_list).strip()
    inference_time = time.time() - start_inf
    
    mem_end = get_memory_usage()
    
    rtf = inference_time / duration
    
    print(f"  Load: {load_time:.2f}s | Inference: {inference_time:.2f}s | RTF: {rtf:.3f}x | Mem: {mem_end-mem_start:.0f}MB")
    
    return {
        "name": name,
        "load_time": load_time,
        "inference_time": inference_time,
        "rtf": rtf,
        "memory_mb": mem_end - mem_start,
    }


def main():
    audio_path = os.path.join(_PROJECT_ROOT, "profiling/20260410_233138.wav")
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        sys.exit(1)
    
    device, compute_type = config._get_device_and_compute_type()
    model_name = config.FASTER_WHISPER_MAIN
    
    print("=" * 60)
    print(f"   OPTIMIZATION BENCHMARKS (device={device}, compute={compute_type})")
    print("=" * 60)
    
    results = []
    
    r = run_test("baseline", model_name, device, compute_type)
    results.append(("baseline", r))
    
    r = run_test("cpu_threads=4", model_name, device, compute_type, cpu_threads=4)
    results.append(("cpu_threads=4", r))
    
    r = run_test("cpu_threads=8", model_name, device, compute_type, cpu_threads=8)
    results.append(("cpu_threads=8", r))
    
    r = run_test("num_workers=2", model_name, device, compute_type, num_workers=2)
    results.append(("num_workers=2", r))
    
    r = run_test("num_workers=4", model_name, device, compute_type, num_workers=4)
    results.append(("num_workers=4", r))
    
    if device == "cpu":
        try:
            r = run_test("int8_float16", model_name, device, "int8_float16")
            results.append(("int8_float16", r))
        except ValueError as e:
            print(f"  Skipped int8_float16: {e}")
    
    r = run_test("vad_200ms", model_name, device, compute_type, min_silence_ms=200)
    results.append(("vad_200ms", r))
    
    r = run_test("no_vad", model_name, device, compute_type, min_silence_ms=300, vad_filter=False)
    results.append(("no_vad", r))
    
    try:
        from faster_whisper import BatchedInferencePipeline
        r = run_test("batched", model_name, device, compute_type, batched=True)
        results.append(("batched", r))
    except ImportError as e:
        print(f"  Skipped batched: {e}")
    
    print("\n" + "=" * 60)
    print("   SUMMARY")
    print("=" * 60)
    
    baseline = results[0][1]["inference_time"]
    print(f"{'Test':<20} {'Time':>8} {'RTF':>6} {'Delta':>8}")
    print("-" * 50)
    
    for name, r in results:
        delta = ((r["inference_time"] - baseline) / baseline) * 100
        delta_str = f"{delta:+.1f}%" if delta != 0 else "baseline"
        print(f"{name:<20} {r['inference_time']:>7.2f}s {r['rtf']:>5.3f}x {delta_str:>8}")
    
    best = min(results, key=lambda x: x[1]["inference_time"])
    print(f"\n🏆 Best: {best[0]} ({best[1]['inference_time']:.2f}s)")


if __name__ == "__main__":
    main()