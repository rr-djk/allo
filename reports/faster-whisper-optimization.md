# Rapport d'optimisation faster-whisper

## Date
2026-04-12

## Objectif
Accélérer les transcriptions et réduire le délai perçu.

## Méthode
Benchmarks systématiques sur 120s d'audio (profiling/20260410_233138.wav) avec variations de paramètres.

## Résultats benchmarks

| Configuration | Temps | RTF | Delta |
|---------------|-------|-----|-------|
| **baseline** (actuel) | 17.72s | 0.148x | — |
| cpu_threads=4 | 17.65s | 0.147x | -0.4% |
| cpu_threads=8 | 28.61s | 0.238x | +61.4% ⚠️ |
| num_workers=2 | 18.48s | 0.154x | +4.3% |
| num_workers=4 | 19.85s | 0.165x | +12.0% |
| vad_200ms | 17.92s | 0.149x | +1.1% |
| no_vad | 18.21s | 0.152x | +2.7% |
| **batched** | **15.26s** | **0.127x** | **-13.9%** ✅ |

## Optimisations appliquées

### ✅ BatchedInferencePipeline (+14% performance)
Implémenté dans `record.py:236-250` et `config.py:24-52`

### ✅ cpu_threads=4 (marginal)
Ajout de `_get_cpu_threads()` dans config.py pour éviter le surcoût CPU.

### ❌ Rejetées (dégradation)
- **cpu_threads=8** : +61% plus lent
- **num_workers>1** : +4-12% plus lent
- **int8_float16** : non supporté sur ce CPU
- **VAD ajusté** : impact négligeable

## Changements de code

### record.py
- Ajout de `BatchedInferencePipeline` pour le modèle principal
- Ajout de `cpu_threads` explicite

### config.py
- Nouvelle fonction `_get_cpu_threads()` limitant à 4 threads
- Application à `transcribe_tiny()` pour cohérence

## Conclusion

L'optimisation la plus significative est **BatchedInferencePipeline** avec un gain de ~14% sur le temps de transcription.

```
Avant: ~18s pour 120s audio (RTF 0.15x)
Après: ~15s pour 120s audio (RTF 0.13x)
```

Les autres paramètres n'apportent pas d'amélioration notable sur ce CPU. Si un GPU devient disponible, les gains seront bien supérieurs (float16).