# Benchmark Approches Round 3 — 20260411_031543

## Contexte

Test de `condition_on_previous_text=False` pour casser la dépendance séquentielle entre segments.

## Résultats

| Approche | Modèle | beam | condition | Inférence | vs baseline (25.73s) |
|----------|--------|------|-----------|-----------|---------------------|
| r3_ref | `small` | 1 | True | 36.42s | 0.71x |
| r3_no_condition | `small` | 1 | False | 33.30s | 0.77x |
| r3_base_no_condition | `base` | 1 | False | 11.92s | 2.16x |
| r3_small_beam5_no_condition | `small` | 5 | False | 42.32s | 0.61x |

## Transcriptions

### r3_ref — small beam=1 (référence)

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de 2 minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de 2 minutes. Parce qu'en fait ça n'a pas besoin d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de 1 seconde. 1 seconde c'est bien mais 1 seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On sait pas. Donc il faut avoir des metrics qui nous indiquent ok, actuellement pour transcrire 2 minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on sait qu'on fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual c'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r3_no_condition — small beam=1 no_condition

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. et cet audio sera par la suite transcrit par l'outil qui va générer les métriques et présenter combien de temps c'est après l'outil pour transcrire cet audio de deux minutes. L'objectif ici est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de deux minutes parce qu'en fait ça ça n'a pas de barrenne de comparaison donc on peut pas dire on accélérer de une seconde, une seconde c'est bien mais une seconde sur mille est-ce que ça change quelque chose est-ce que c'est un changement que révalue la peine on sait pas donc il faut avoir des métriques qui nous indiquent ok actuellement pour transcrire deux minutes ça prend 55 secondes comme ça On fait un changement qui nous fait passer de 55 à 10, on se couvre, on a fait quelque chose d'extraordinaire Mais si on fait quelque chose qui nous fait passer de 55 à 54 secondes, ce n'est pas la folie Et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer C'est ça le but du benchmark, c'est vraiment d'aller avoir des métriques solides qui vont permettre de quitter l'évolution du travail qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur
```

### r3_base_no_condition — base beam=1 no_condition

```
Ok, donc c'est ici un arbre charmant qui va permettre de... qui va s'est avis de benchmark pour... pour les tests. Ça va permettre de regarder combien de temps l'OTI prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement, c'est juste que je parle pendant 2 minutes et ce tout au jour sur rapport à la suite transcrite par l'OTI, qui va générer la métrique et présenter combien de temps ça va pour la loutier vous transcrite, c'est tout au jour de deux minutes. L'objectif c'est ici d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend l'OTI pour transcrire l'OTI. Parce qu'on fait ça n'est rien d'optimiser si on n'a pas de barrem de comparaison. Donc on ne peut pas dire, on accélérerait de 1 seconde. 1 seconde c'est bien mais 1 seconde, 1,000, est-ce que ça change quelque chose ? Est-ce que c'est un changement que révalue la peine ? On ne sait pas. Donc il faut avoir des métriques qui nous indiquent, ok. Actuellement pour transcrire 2 minutes, ça prend 5,5 secondes. Comme ça, on fait un changement qui nous fait passer de 55 à 10, on se courre, on a fait quelque chose d'extrordinaire. Mais si on fait quelque chose qui nous fait passer de 55 seconde à 54 seconde, c'est pas la folie. Et peut-être c'est une tâche qui ne va l'apparirement la peine d'effectuer. Donc c'est ça le butue Benjamin Talkchul. c'est vraiment d'avoir des métric solides qui vont permettre de quitter l'évolution du travail, qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### r3_small_beam5_no_condition — small beam=5 no_condition

```
Ok, donc ceci est un arrangement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de deux minutes. Donc l'objectif actuellement c'est juste que je parle pendant deux minutes. et cet audio sera par la suite transcrit par l'outil qui va générer les métriques et présenter combien de temps c'est après l'outil pour transcrire cet audio de deux minutes. L'objectif ici est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de deux minutes parce qu'en fait ça ça ne sert à rien d'optimiser si on n'a pas de barème de comparaison donc on peut pas dire on accélérer de une seconde, une seconde c'est bien mais une seconde c'est mille est ce que ça change quelque chose est ce que c'est un changement que révalue la peine on sait pas donc il faut avoir des métriques qui nous indiquent ok actuellement pour transcrire deux minutes ça prend 55 secondes. Comme ça, si on fait un changement qui nous fait passer de 55 à 10, on se couvre. On a fait quelque chose d'extraordinaire, mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes, ce n'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça, le but Benchmark c'est vraiment d'aller avoir des métriques solides qui vont permettre de quitter l'évolution du travail, qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

_Généré le 2026-04-11T03:17:52.882348_
