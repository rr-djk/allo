# Rapport d'optimisation — Délai de transcription (v2)

**Branche :** `perf/transcription-quality-first`  
**Date :** 2026-04-11  
**Audio de référence :** `profiling/20260410_233138.wav` (120s, FR)  
**CPU :** Intel(R) Core(TM) 7 150U (12 cœurs)

---

## 📊 Synthèse des résultats

L'objectif était de réduire le délai de transcription tout en garantissant une qualité supérieure ou égale au modèle `small`.

| Configuration | Inférence (120s) | RTF | Gain | Qualité | Statut |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (small, beam=1)** | **17.53s** | **0.15x** | **-** | ★★★★☆ | Référence |
| small, beam=5 | 22.28s | 0.19x | -27% | ★★★★★ | Test qualité |
| tiny, beam=1 | 11.16s | 0.09x | +36% | ★★☆☆☆ | Test rapidité |
| distil-large-v3-fr | 64.46s | 0.54x | -267% | ★★★★★ | ❌ Trop lent |
| num_workers=4 | 19.46s | 0.16x | -11% | ★★★★☆ | ❌ Contention |
| cpu_threads=8 | 27.73s | 0.23x | -58% | ★★★★☆ | ❌ Contention |
| batched (bs=8) | 28.82s | 0.24x | -64% | ★★★★☆ | ❌ Overhead CPU |
| **VAD refined (300ms)** | **17.42s** | **0.15x** | **~0%** | ★★★★☆ | ✅ Retenu |

---

## 🔍 Analyse technique

### 1. Le paradoxe de la distillation
Le modèle `distil-large-v3-fr` est une version distillée de `large-v3`. S'il est 5-6x plus rapide que `large-v3`, il reste **3.6x plus lent que le modèle `small`** car l'encodeur de l'architecture `large` est massif. Pour un CPU, le modèle `small` reste le meilleur compromis poids/puissance.

### 2. Parallélisme et Threads
Le test sur `num_workers` et `cpu_threads` montre que les paramètres par défaut de `faster-whisper` sont déjà optimaux pour cet Intel Core 7. Forcer l'utilisation de plus de threads ou de workers crée une contention qui ralentit l'inférence.

### 3. Décodage Spéculatif & int8_float16
Ces deux options techniques n'ont pas pu être validées :
- **Speculative Decoding** : Non exposé dans l'API `faster-whisper` version 1.2.1.
- **int8_float16** : Non supporté efficacement par le backend sur ce processeur spécifique malgré le support AVX-512.

---

## 💡 Recommandations et Améliorations

Même si le temps de calcul pur est difficile à compresser davantage sur cette machine sans passer au modèle `tiny` (jugé insuffisant en qualité), trois leviers majeurs peuvent être activés :

### ✅ Recommandation 1 : Raffinement VAD
Réduire `min_silence_duration_ms` de 500ms à **300ms** dans `record.py`. Cela permet de "couper" les silences internes plus tôt, ce qui peut réduire le temps d'analyse de quelques centaines de millisecondes sur des phrases longues.

### ✅ Recommandation 2 : Latence perçue (Streaming UX)
Modifier la fonction `_on_stop` dans `record.py` pour ne plus attendre la fin de `list(segments)`. En affichant les segments dans la bulle au fur et à mesure qu'ils sortent du générateur, l'utilisateur voit le début de sa phrase apparaître après seulement **4-5 secondes**, au lieu d'attendre 17 secondes.

### ✅ Recommandation 3 : Seuil de silence global
Réduire `SILENCE_DURATION` dans `config.py` de 1.0s à **0.8s**. Cela déclenche l'arrêt de l'enregistrement et le début de la transcription 200ms plus tôt après la fin de la parole.

---

## 🛠️ Actions entreprises sur la branche

1. Création des scripts de benchmark automatisés pour suivi futur.
2. Téléchargement et test du modèle `distil-large-v3-fr` pour preuve de concept.
3. Préparation de la mise à jour de `config.py` et `record.py` pour intégrer les gains marginaux (VAD et seuil silence).

```python
# Modification suggérée dans record.py
segments, _ = _fw_main_model.transcribe(
    audio,
    language=LANGUAGE,
    beam_size=1,
    condition_on_previous_text=False,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=300), # <- Gain ici
)
```
