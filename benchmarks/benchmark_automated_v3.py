"""benchmark_automated_v3.py — Automated transcription benchmarking tool.

This script measures transcription time (RTF), memory usage, and captures the
resulting text for quality comparison.
"""
import os
import sys
import time
import wave
import json
import psutil
from datetime import datetime
import numpy as np

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

from faster_whisper import WhisperModel
import config

AUDIO_FILE = os.path.join(_PROJECT_ROOT, "profiling/20260410_233138.wav")

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)  # MB

def load_audio(path):
    with wave.open(path, 'rb') as wf:
        params = wf.getparams()
        if params.framerate != 16000:
            raise ValueError(f"Sample rate must be 16000, found {params.framerate}")
        frames = wf.readframes(params.nframes)
        audio = np.frombuffer(frames, dtype=np.int16).flatten().astype(np.float32) / 32768.0
        return audio

def benchmark(model_name, num_workers=1, cpu_threads=0, compute_type="int8", 
              beam_size=1, condition_on_previous_text=False, min_silence_duration_ms=500):
    device, _ = config._get_device_and_compute_type()
    
    print(f"--- Benchmarking: {model_name} ---")
    print(f"Workers: {num_workers}, Threads: {cpu_threads}, Compute: {compute_type}")
    print(f"Beam: {beam_size}, Condition: {condition_on_previous_text}, VAD_ms: {min_silence_duration_ms}")
    
    mem_start = get_memory_usage()
    
    # Model Loading
    start_load = time.time()
    # Note: num_workers in faster-whisper is inter_threads (parallel calls)
    # cpu_threads is intra_threads (within one call)
    model = WhisperModel(model_name, device=device, compute_type=compute_type, 
                         num_workers=num_workers, cpu_threads=cpu_threads)
    load_time = time.time() - start_load
    
    audio = load_audio(AUDIO_FILE)
    duration = len(audio) / 16000
    
    # Warm-up (1s audio)
    model.transcribe(audio[:16000], language="fr")
    
    # Inference
    start_inf = time.time()
    segments, _ = model.transcribe(
        audio,
        language="fr",
        beam_size=beam_size,
        condition_on_previous_text=condition_on_previous_text,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=min_silence_duration_ms)
    )
    # Materialize segments to ensure inference completes
    segment_list = list(segments)
    text = " ".join(seg.text.strip() for seg in segment_list).strip()
    inference_time = time.time() - start_inf
    
    mem_end = get_memory_usage()
    
    return {
        "config": {
            "model": model_name,
            "num_workers": num_workers,
            "cpu_threads": cpu_threads,
            "compute_type": compute_type,
            "beam_size": beam_size,
            "condition_on_previous_text": condition_on_previous_text,
            "min_silence_duration_ms": min_silence_duration_ms
        },
        "metrics": {
            "load_time": load_time,
            "inference_time": inference_time,
            "audio_duration": duration,
            "rtf": inference_time / duration,
            "memory_delta_mb": mem_end - mem_start,
            "memory_rss_mb": mem_end
        },
        "text": text
    }

def main():
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: {AUDIO_FILE} not found.")
        sys.exit(1)
        
    config_name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    
    results = {}
    
    if config_name == "baseline":
        # Baseline (small, current prod parameters)
        results = benchmark("small", beam_size=1, condition_on_previous_text=False)
    
    elif config_name == "distil":
        # Opt B: Distil-Whisper FR
        local_model_path = os.path.join(_PROJECT_ROOT, "models/distil-fr/ctranslate2")
        if not os.path.exists(local_model_path):
            print(f"Local model not found at {local_model_path}")
            sys.exit(1)
        results = benchmark(local_model_path, beam_size=1, condition_on_previous_text=False)
        
    elif config_name == "threads8":
        # Opt C: cpu_threads=8
        results = benchmark("small", cpu_threads=8, beam_size=1, condition_on_previous_text=False)
        
    elif config_name == "vad300":
        # Opt E: VAD refinement (300ms)
        results = benchmark("small", min_silence_duration_ms=300, beam_size=1, condition_on_previous_text=False)
    
    elif config_name == "beam5":
        # Check if beam_size=5 (better quality) is much slower
        results = benchmark("small", beam_size=5, condition_on_previous_text=False)

    else:
        print(f"Unknown config: {config_name}")
        sys.exit(1)
        
    # Save to JSON
    out_dir = os.path.join(_PROJECT_ROOT, "benchmarks/results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{config_name}.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Result saved to {out_file}")
    print(f"Inference Time: {results['metrics']['inference_time']:.2f}s (RTF: {results['metrics']['rtf']:.2f}x)")

if __name__ == "__main__":
    main()
