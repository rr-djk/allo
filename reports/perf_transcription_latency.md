# Rapport d'expérimentation — Réduction latence de transcription

**Branche :** `perf/transcription-latency`  
**Date :** 2026-04-11  
**Audio de référence :** `profiling/20260410_233138.wav` (120s, FR)

---

## Baseline

| Paramètre | Valeur |
|-----------|--------|
| Modèle | `small` |
| Langue | `fr` |
| beam_size | 5 (défaut) |
| vad_filter | True |
| condition_on_previous_text | True (défaut) |
| Temps transcription (premier appel) | **51.96s** |
| Temps transcription (modèle warm) | **25.73s** |

> Note : l'app dispose d'un warm-up au démarrage (`_warmup()` dans `main()`). En usage réel, le temps pertinent est **25.73s** (modèle déjà en mémoire).

---

## Round 1 — Comparaison modèles et paramètres clés

Scripts : `benchmark_approaches.py` / Rapport : `benchmark_approaches_20260411_001815.md`

| Approche | Config | Inférence | Speedup | Qualité |
|----------|--------|-----------|---------|---------|
| baseline | small, beam=5, vad=True | 25.73s | 1.00x | ★★★★★ |
| voie1 | small, beam=1, vad=True | 18.70s | **1.38x** | ★★★★☆ |
| voie2 | base, beam=5, vad=True | 8.87s | **2.90x** | ★★★☆☆ |
| voie3 | small, beam=5, vad=False | 27.74s | 0.93x | ★★★★☆ |
| voie4 | base, beam=1, vad=False | 6.37s | **4.04x** | ★★☆☆☆ |
| voie5 | distil-small.fr | ÉCHEC | — | — |

### Observations

- **beam_size=1** : gain de ~1.4x avec dégradation légère (quelques mots mal transcrits)
- **modèle base** : gain de ~3x mais qualité insuffisante sur le français ("OTI" pour "outil", "5,5" pour "55")
- **vad_filter=False** : plus lent que vad=True — le filtre VAD accélère en sautant les silences
- **voie4 (base+beam1)** : speedup 4x mais transcription trop dégradée pour un outil de dictée
- **distil-small.fr** : modèle inexistant sur HuggingFace (401 unauthorized)

---

## Round 2 — cpu_threads et modèle turbo

Scripts : `benchmark_approaches_r2.py` / Rapport : `benchmark_approaches_r2_20260411_030650.md`

> ⚠️ CPU thermiquement bridé (Intel Core 7 150U, 12 cœurs) après la session Round 1 — les temps absolus sont ~2x plus lents mais les **ratios relatifs sont fiables**.

| Approche | Config | Speedup vs ref |
|----------|--------|----------------|
| r2_threads4 | small, beam=1, threads=4 | +1% |
| r2_threads8 | small, beam=1, threads=8 | -10% |
| r2_threads12 | small, beam=1, threads=12 | -2% |
| r2_beam2 | small, beam=2 | -11% |
| r2_turbo | turbo, beam=1 | **-70%** (inutilisable CPU) |

### Observations

- **cpu_threads** : aucun gain. CTranslate2 gère déjà ses threads en interne ; fixer le paramètre crée de la contention.
- **turbo** (large-v3-turbo) : 124s d'inférence sur CPU — optimisé pour GPU uniquement.
- **beam_size=2** : plus lent que beam=1, moins bon que beam=5 en qualité → pas de sweet spot ici.

---

## Round 3 — condition_on_previous_text

Scripts : `benchmark_approaches_r3.py` / Rapport : `benchmark_approaches_r3_20260411_031543.md`

> ⚠️ CPU toujours bridé — ratios relatifs à considérer.

| Approche | Config | vs r3_ref |
|----------|--------|-----------|
| r3_ref | small, beam=1, condition=True | 1.00x |
| r3_no_condition | small, beam=1, condition=False | +9% |
| r3_base_no_condition | base, beam=1, condition=False | +3x (qualité insuffisante) |
| r3_small_beam5_no_condition | small, beam=5, condition=False | -14% |

### Observations

- **condition_on_previous_text=False** : gain modeste (~9%) mais sans perte de qualité observable
- Combiné à beam=1, c'est le meilleur compromis vitesse/qualité avec le modèle `small`
- small+beam=5+condition=False produit une transcription de très bonne qualité mais reste plus lent

---

## Synthèse et décision

### Tableau de décision

| Config | Speedup (CPU froid) | Qualité | Décision |
|--------|---------------------|---------|----------|
| small, beam=5 (baseline) | 1.00x | ★★★★★ | référence |
| small, beam=1, condition=False | **~1.5x** | ★★★★☆ | ✅ **Retenu** |
| base, beam=1 | ~4x | ★★☆☆☆ | ❌ trop dégradé FR |
| turbo, beam=1 | <1x sur CPU | ★★★★★ | ❌ GPU uniquement |

### Changement appliqué

Dans `record.py`, fonction `transcribe()` :

```python
# Avant
segments, _ = _fw_main_model.transcribe(
    audio,
    language=LANGUAGE,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
)

# Après
segments, _ = _fw_main_model.transcribe(
    audio,
    language=LANGUAGE,
    beam_size=1,
    condition_on_previous_text=False,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
)
```

**Gain attendu en production** : ~25.73s → ~16-18s pour 120s d'audio (modèle warm).

---

## Pistes non explorées / futures

| Piste | Raison non testée | Impact potentiel |
|-------|-------------------|-----------------|
| GPU (CUDA) | Machine CPU only | 5-10x |
| distil-whisper FR | Modèle introuvable sur HF | 3-5x si disponible |
| Transcription progressive (streaming) | Complexité implémentation | UX améliorée |
| Modèle medium+beam=1 | Pas testé — pourrait offrir qualité++ à vitesse équivalente à small+beam=5 | À tester |
| `whisper-large-v3-turbo` sur GPU | Inutilisable CPU | 3-4x sur GPU |

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `benchmark_approaches.py` | Script Round 1 (6 configs) |
| `benchmark_approaches_r2.py` | Script Round 2 (cpu_threads, turbo) |
| `benchmark_approaches_r3.py` | Script Round 3 (condition_on_previous_text) |
| `reports/benchmark_approaches_20260411_001815.md` | Résultats Round 1 |
| `reports/benchmark_approaches_r2_20260411_030650.md` | Résultats Round 2 |
| `reports/benchmark_approaches_r3_20260411_031543.md` | Résultats Round 3 |
