# Rapport d'optimisation faster-whisper v2

## Date
2026-04-12

## Objectif
Tester des optimisations supplémentaires pour améliorer les performances de transcription.

## Méthode
Benchmarks systématiques sur 120s d'audio (profiling/20260410_233138.wav) avec variations de modèles et paramètres.

## Résultats benchmarks v2 (120s audio)

| Configuration | RTF | Delta | Qualité | Décision |
|--------------|-----|-------|---------|----------|
| **baseline (small)** | 0.154x | — | ✅ | Référence |
| medium | 0.437x | +184% ⚠️ | ✅ | REJETÉ |
| distil-large-v3 | 0.555x | +261% ⚠️ | ❌ anglais | REJETÉ |
| beam_size=5 | 0.192x | +25% ⚠️ | ✅ | REJETÉ |
| initial_prompt | 0.158x | +2.7% ⚠️ | ✅ | REJETÉ |
| compression_ratio_threshold=2.0 | 0.157x | +1.8% ⚠️ | ✅ | REJETÉ |

## Décisions

### ❌ Toutes les optimisations rejetées

1. **medium** : Attendu ~40% plus rapide, mais en réalité +184% plus lent. Modèle trop lourd pour CPU.
2. **distil-large-v3** : +261% plus lent, qualité dégradée (transcription anglaise incorrecte).
3. **beam_size=5** : +25% plus lent, pas de gain de performance.
4. **initial_prompt** : +2.7% plus lent, pas de gain mesurable.
5. **compression_ratio_threshold** : +1.8% plus lent, pas d'impact positif.

## Résultats benchmarks v1 (précédent)

| Configuration | Temps | RTF | Delta |
|---------------|-------|-----|-------|
| **baseline** (actuel) | 17.72s | 0.148x | — |
| cpu_threads=4 | 17.65s | 0.147x | -0.4% |
| cpu_threads=8 | 28.61s | 0.238x | +61.4% |
| num_workers=2 | 18.48s | 0.154x | +4.3% |
| num_workers=4 | 19.85s | 0.165x | +12.0% |
| vad_200ms | 17.92s | 0.149x | +1.1% |
| no_vad | 18.21s | 0.152x | +2.7% |
| **batched** | **15.26s** | **0.127x** | **-13.9%** ✅ |

## Optimisations validées (v1)

### ✅ BatchedInferencePipeline (+14% performance)
Implémenté dans `record.py:236-250` et `config.py:24-52`

### ✅ cpu_threads=4 (marginal)
Ajout de `_get_cpu_threads()` dans config.py

## Changements de code (v1)

### record.py
- Ajout de `BatchedInferencePipeline` pour le modèle principal
- Ajout de `cpu_threads` explicite

### config.py
- Nouvelle fonction `_get_cpu_threads()` limitant à 4 threads
- Application à `transcribe_tiny()` pour cohérence

## Conclusion

**Aucune nouvelle optimisation acceptée**. Les tests v2 montrent que:
- Les modèles plus grands (medium, distil-large) sont trop lourds pour CPU
- Les paramètres additionnels (beam_size, initial_prompt, compression_ratio) n'apportent pas de gain
- Le modèle **small** avec BatchedInferencePipeline reste optimal sur CPU

```
Performance actuelle: ~15s pour 120s audio (RTF 0.13x)
```

Pour des gains supplémentaires, un GPU serait nécessaire (float16 enabled).