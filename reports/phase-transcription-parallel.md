# phase-transcription-parallel — Transcription Parallèle par Chunks

## Contexte

Objectif : réduire le délai de transcription en découpant l'audio en chunks et en les transcrire en parallèle.

## Expérimentation

### Hypothèse

Découper l'audio en chunks de 30s et lancer la transcription en parallèle sur plusieurs threads Python permettrait de réduire le temps de transcription.

### Métrique de base

| Audio | Transcription | Ratio |
|-------|--------------|-------|
| 120s | 27.90s | 0.23x |

### Résultats

| Configuration | Temps | Ratio | Speedup |
|---------------|-------|-------|---------|
| Séquentiel (1 thread) | 27.90s | 0.23x | 1.00x |
| Parallèle 1 worker | 32.22s | 0.27x | 0.87x |
| Parallèle 2 workers | 30.59s | 0.25x | 0.91x |
| Parallèle 4 workers | 30.24s | 0.25x | 0.92x |
| Parallèle 8 workers | 30.31s | 0.25x | 0.92x |

### Conclusion

**La transcription parallèle par chunks ne fonctionne pas sur CPU.**

Causes identifiées :
1. `faster-whisper` utilise déjà des optimisations internes (INT8, multithreading au niveau C++)
2. Le GIL (Global Interpreter Lock) de Python limite les gains des threads Python
3. L'overhead de création/synchronisation des threads dépasse le gain potentiel

## Pistes d'amélioration restantes

| Piste | Impact estimé | Status |
|-------|--------------|--------|
| GPU disponible | 3-5x plus rapide | ❌ CPU only sur cette machine |
| SILENCE_DURATION 1.5s → 1.0s | -500ms | ✅ Déjà implémenté |
| Transcription pendant l'enregistrement | UX améliorée | ⏳ Non testé |
| num_workers C++ dans faster-whisper | Variable | ⏳ À tester |

## Recommandation

1. **Fusionner les résultats de benchmark** dans `main` pour documenter les métriques
2. **Explorer la transcription progressive** pendant l'enregistrement pour améliorer l'UX
3. **Tester sur machine avec GPU** pour valider le gain potentiel

## Fichiers de benchmark

- `profiling/20260410_233138.wav` — audio de test (120s)
- `profiling/20260410_233138_report.md` — rapport initial
- `benchmark_parallel_20260410_235924.md` — rapport de benchmark parallèle
