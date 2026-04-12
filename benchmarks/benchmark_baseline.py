"""benchmark_baseline.py — Mesure de référence des performances de transcription.

Usage:
    python benchmarks/benchmark_baseline.py
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


def run_benchmark():
    audio_path = os.path.join(_PROJECT_ROOT, "profiling/20260410_233138.wav")
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        sys.exit(1)
    
    audio = load_audio(audio_path)
    duration = len(audio) / 16000
    
    device, compute_type = config._get_device_and_compute_type()
    
    print("=" * 50)
    print("   BASELINE BENCHMARK")
    print("=" * 50)
    print(f"Device: {device}")
    print(f"Compute type: {compute_type}")
    print(f"Model: {config.FASTER_WHISPER_MAIN}")
    print(f"Audio duration: {duration:.2f}s")
    print()
    
    mem_start = get_memory_usage()
    
    start_load = time.time()
    model = WhisperModel(
        config.FASTER_WHISPER_MAIN,
        device=device,
        compute_type=compute_type,
    )
    load_time = time.time() - start_load
    
    model.transcribe(audio[:16000], language=config.LANGUAGE)
    
    start_inf = time.time()
    segments, _ = model.transcribe(
        audio,
        language=config.LANGUAGE,
        beam_size=1,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )
    segment_list = list(segments)
    text = " ".join(seg.text.strip() for seg in segment_list).strip()
    inference_time = time.time() - start_inf
    
    mem_end = get_memory_usage()
    
    print("RESULTS:")
    print(f"  Load time:   {load_time:.2f}s")
    print(f"  Inference:    {inference_time:.2f}s")
    print(f"  RTF:         {inference_time / duration:.2f}x")
    print(f"  Memory:      {mem_end - mem_start:.1f} MB")
    print()
    print(f"Text: {text[:100]}...")
    
    return {
        "load_time": load_time,
        "inference_time": inference_time,
        "rtf": inference_time / duration,
        "memory_mb": mem_end - mem_start,
        "text": text,
    }


if __name__ == "__main__":
    run_benchmark()