---
status: done
type: benchmark
priority: medium
assigned_to: implementation-specialist
started_at: 2026-04-12T00:45:00
depends_on: []
files_touched:
  - benchmarks/benchmark_extended.py
  - reports/faster-whisper-optimization.md
  - reports/benchmark_extended_results.json
related_to: faster-whisper-optimization
---

# Benchmark optimisations faster-whisper v2

## Objectif
Tester 5 optimisations supplémentaires pour améliorer les performances.

## Résultats

| Configuration | RTF | Delta | Décision |
|--------------|-----|-------|----------|
| baseline (small) | 0.154x | — | Référence |
| medium | 0.437x | +184% | REJETÉ |
| distil-large-v3 | 0.555x | +261% | REJETÉ |
| beam_size=5 | 0.192x | +25% | REJETÉ |
| initial_prompt | 0.158x | +2.7% | REJETÉ |
| compression_ratio_threshold=2.0 | 0.157x | +1.8% | REJETÉ |

## Conclusion
Aucune nouvelle optimisation acceptée. Le modèle small avec BatchedInferencePipeline reste optimal sur CPU.