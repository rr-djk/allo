"""benchmark_extended.py — Tests supplémentaires d'optimisations faster-whisper.

Usage:
    python benchmarks/benchmark_extended.py
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
        if params.framerate != 16000:
            raise ValueError(f"Sample rate must be 16000, found {params.framerate}")
        frames = wf.readframes(params.nframes)
        audio = np.frombuffer(frames, dtype=np.int16).flatten().astype(np.float32) / 32768.0
        return audio


def run_benchmark(name, model_name, audio, duration, options):
    """Run a single benchmark with given options.
    
    @param name {str} - Display name for this configuration
    @param model_name {str} - Model name (e.g., "small", "medium", "base")
    @param audio {np.ndarray} - Audio data
    @param duration {float} - Audio duration in seconds
    @param options {dict} - Options passed to transcribe()
    
    @returns {dict} - Results with timing and text
    """
    device, compute_type = config._get_device_and_compute_type()
    cpu_threads = config._get_cpu_threads()
    
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"Model: {model_name}")
    print(f"Options: {options}")
    
    mem_start = get_memory_usage()
    
    # Model load
    start_load = time.time()
    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads,
    )
    load_time = time.time() - start_load
    
    # Warmup
    model.transcribe(audio[:16000], language=config.LANGUAGE)
    
    # Actual inference
    start_inf = time.time()
    segments, _ = model.transcribe(audio, language=config.LANGUAGE, **options)
    segment_list = list(segments)
    text = " ".join(seg.text.strip() for seg in segment_list).strip()
    inference_time = time.time() - start_inf
    
    mem_end = get_memory_usage()
    
    rtf = inference_time / duration
    
    print(f"\nRESULTS:")
    print(f"  Load time:   {load_time:.2f}s")
    print(f"  Inference:   {inference_time:.2f}s")
    print(f"  RTF:         {rtf:.3f}x")
    print(f"  Memory:      {mem_end - mem_start:.1f} MB")
    print(f"  Text len:    {len(text)} chars")
    print(f"  Text: {text[:80]}..." if len(text) > 80 else f"  Text: {text}")
    
    return {
        "name": name,
        "model": model_name,
        "load_time": load_time,
        "inference_time": inference_time,
        "rtf": rtf,
        "memory_mb": mem_end - mem_start,
        "text": text,
        "text_len": len(text),
    }


def main():
    audio_path = os.path.join(_PROJECT_ROOT, "profiling/20260410_233138.wav")
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        sys.exit(1)
    
    audio = load_audio(audio_path)
    duration = len(audio) / 16000
    
    print(f"Audio duration: {duration:.2f}s")
    print(f"Language: {config.LANGUAGE}")
    
    # Baseline - current config (small + batched)
    baseline_options = {
        "beam_size": 1,
        "condition_on_previous_text": False,
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=300),
    }
    
    # Test configurations
    tests = [
        # Baseline
        {
            "name": "baseline_small",
            "model": "small",
            "options": baseline_options,
        },
        # 1. Model: medium (expected ~40% slower but better quality)
        {
            "name": "medium_model",
            "model": "medium",
            "options": baseline_options,
        },
        # 2. Model: distil-large-v3 (expected faster with good quality)
        {
            "name": "distil_large_v3",
            "model": "distil-large-v3",
            "options": baseline_options,
        },
        # 3. beam_size=5 (better quality, slightly slower)
        {
            "name": "beam_size_5",
            "model": "small",
            "options": {**baseline_options, "beam_size": 5},
        },
        # 4. initial_prompt (better context)
        {
            "name": "initial_prompt",
            "model": "small",
            "options": {**baseline_options, "initial_prompt": "Transcription en français."},
        },
        # 5. compression_ratio_threshold (filter non-relevant audio)
        {
            "name": "compression_ratio_threshold_2.0",
            "model": "small",
            "options": {**baseline_options, "compression_ratio_threshold": 2.0},
        },
    ]
    
    results = []
    baseline_rtf = None
    
    for test in tests:
        result = run_benchmark(
            test["name"],
            test["model"],
            audio,
            duration,
            test["options"]
        )
        results.append(result)
        
        if test["name"] == "baseline_small":
            baseline_rtf = result["rtf"]
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Configuration':<35} {'RTF':>8} {'Delta':>10} {'Text':>8}")
    print("-"*60)
    
    for r in results:
        delta = ((r["rtf"] - baseline_rtf) / baseline_rtf) * 100 if baseline_rtf else 0
        marker = "✅" if delta <= 0 else "⚠️"
        print(f"{r['name']:<35} {r['rtf']:>7.3f}x {delta:>+9.1f}%{marker} {r['text_len']:>7}")
    
    # Save results
    import json
    results_path = os.path.join(_PROJECT_ROOT, "reports/benchmark_extended_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()