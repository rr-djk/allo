# Benchmark Approches Round 2 — 20260411_030650

## Fichier audio

| Paramètre | Valeur |
|-----------|--------|
| Fichier | `profiling/20260410_233138.wav` |
| Durée | 120s |

## Référence Round 1

| Config | Inférence |
|--------|----------|
| baseline (small, beam=5, vad=True) | 25.73s |
| voie1 (small, beam=1, vad=True) | 18.70s |

## Résultats Round 2

| Approche | Modèle | beam | threads | Inférence | vs baseline | Ratio |
|----------|--------|------|---------|-----------|-------------|-------|
| r2_ref | `small` | 1 | auto | 37.29s | 0.69x | 0.31x |
| r2_threads4 | `small` | 1 | 4 | 36.74s | 0.70x | 0.31x |
| r2_threads8 | `small` | 1 | 8 | 40.88s | 0.63x | 0.34x |
| r2_threads12 | `small` | 1 | 12 | 37.87s | 0.68x | 0.32x |
| r2_beam2 | `small` | 2 | auto | 42.04s | 0.61x | 0.35x |
| r2_turbo | `turbo` | 1 | auto | 124.93s | 0.21x | 1.04x |

## Transcriptions

### r2_ref — Référence (small beam=1)

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de 2 minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de 2 minutes. Parce qu'en fait ça n'a pas besoin d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de 1 seconde. 1 seconde c'est bien mais 1 seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On sait pas. Donc il faut avoir des metrics qui nous indiquent ok, actuellement pour transcrire 2 minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on sait qu'on fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual c'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r2_threads4 — small beam=1 threads=4

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de 2 minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de 2 minutes. Parce qu'en fait ça n'a pas besoin d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de 1 seconde. 1 seconde c'est bien mais 1 seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On sait pas. Donc il faut avoir des metrics qui nous indiquent ok, actuellement pour transcrire 2 minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on sait qu'on fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual c'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r2_threads8 — small beam=1 threads=8

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de 2 minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de 2 minutes. Parce qu'en fait ça n'a pas besoin d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de 1 seconde. 1 seconde c'est bien mais 1 seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On sait pas. Donc il faut avoir des metrics qui nous indiquent ok, actuellement pour transcrire 2 minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on sait qu'on fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual c'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r2_threads12 — small beam=1 threads=12

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de 2 minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de 2 minutes. Parce qu'en fait ça n'a pas besoin d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de 1 seconde. 1 seconde c'est bien mais 1 seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On sait pas. Donc il faut avoir des metrics qui nous indiquent ok, actuellement pour transcrire 2 minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on sait qu'on fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual c'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r2_beam2 — small beam=2

```
Ok, donc ceci est un arrangement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de deux minutes. Donc l'objectif actuellement c'est juste que je parle pendant deux minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de deux minutes. L'objectif ici est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de deux minutes. Parce qu'en fait, ça n'est pas à rien d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire, on accélérerait d'une seconde. Une seconde c'est bien mais une seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On ne sait pas. Donc il faut avoir des metrics qui nous indiquent, ok, actuellement pour transcrire deux minutes ça prend 55 secondes. Comme ça, si on fait un changement qui nous fait passer de 55 à 10, on sait que oui, on a fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes, c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual. C'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r2_turbo — turbo (large-v3-turbo)

```
Ok donc ceci est un enregistrement qui va permettre de qui va servir de benchmark pour pour les tests ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de deux minutes dont l'objectif actuellement c'est juste que je parle pendant deux minutes et cet audio sera par la suite transcrit par l'outil qui va générer les métriques et présenter combien de temps ça fera l'outil pour transcrire cet audio de deux minutes l'objectif ici est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend l'outil pour transcrire l'audio de deux minutes parce qu'en fait ça ne sert à rien d'optimiser si on n'a pas de barème de comparaison donc on peut pas dire en accélérer d'une seconde une seconde c'est bien mais une seconde sur 1000 est ce que ça a changé quelque chose est ce que c'est un changement qui aurait valu la peine on sait pas donc il faut avoir des métriques qui nous indique ok actuellement pour transcrire deux minutes ça prend 55 secondes comme ça si on fait un changement qui nous fait passer de 55 à 10 ans on sait qu'on a fait quelque chose d'extraordinaire mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer donc c'est ça le but du benchmark actuel c'est vraiment d'aller avoir des métriques solides qui vont permettre de guider l'évolution du travail qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur
```

_Généré le 2026-04-11T03:14:27.401669_
