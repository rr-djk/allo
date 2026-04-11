# Benchmark Approches — 20260411_121817

## Fichier audio

| Paramètre | Valeur |
|-----------|--------|
| Fichier | `/home/rr-djk/Documents/projets/allo/profiling/20260410_233138.wav` |
| Durée | 120s |

## Résultats

| Approche | Nom | Modèle | beam_size | vad_filter | Temps total | Temps inférence | Speedup | Ratio |
|----------|-----|--------|-----------|------------|-------------|-----------------|---------|-------|
| baseline | Baseline (actuel) | `small` | 5 | True | 26.50s | 25.52s | 1.00x | 0.21x |
| voie1 | beam_size=1 | `small` | 1 | True | 20.56s | 18.96s | 1.35x | 0.16x |
| voie2 | model base | `base` | 5 | True | 9.64s | 9.05s | 2.82x | 0.08x |
| voie3 | vad_filter=False | `small` | 5 | False | 28.45s | 27.73s | 0.92x | 0.23x |
| voie4 | base+beam1 | `base` | 1 | False | 7.11s | 6.16s | 4.14x | 0.05x |
| voie5 | distil-small.fr | `Systran/faster-distil-whisper-small.fr` | 5 | True | ECHEC | ECHEC | — | — |

## Transcriptions

### baseline — Baseline (actuel)

```
Ok, donc ceci est un arrangement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de deux minutes. Donc l'objectif actuellement c'est juste que je parle pendant deux minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de deux minutes. L'objectif ici est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de deux minutes. Parce qu'en fait ça ne sert à rien d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de une seconde. Une seconde c'est bien mais une seconde c'est mille. Est-ce que ça change quelque chose? Est-ce que c'est un changement que révalue la peine? On ne sait pas. Donc il faut avoir des metrics qui nous indiquent. Ok, actuellement pour transcrire deux minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on se couvre. On a fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes ce n'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but du benchmark actuel. C'est vraiment d'aller avoir des metrics solides qui vont permettre de quitter l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### voie1 — beam_size=1

```
Ok, donc ceci est un arrêchement qui va permettre de, qui va servir de benchmark pour les tests. Ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de 2 minutes. Donc l'objectif actuellement c'est juste que je parle pendant 2 minutes. Et cet audio sera par la suite transcrit par l'outil qui va générer les metrics et présenter combien de temps c'est après l'outil pour transcrire cet audio de 2 minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de 2 minutes. Parce qu'en fait ça n'a pas besoin d'optimiser si on n'a pas de barren de comparaison. Donc on peut pas dire on accélérer de 1 seconde. 1 seconde c'est bien mais 1 seconde c'est mille. Est-ce que ça change quelque chose ? Est-ce que c'est un changement qui révalue la peine ? On sait pas. Donc il faut avoir des metrics qui nous indiquent ok, actuellement pour transcrire 2 minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on sait qu'on fait quelque chose d'extraordinaire. Mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but Benchmark Actual c'est vraiment d'aller avoir des metrics solides qui vont permettre de guider l'évolution du travail. Qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### voie2 — model base

```
Ok, donc c'est ici un arouchement qui va permettre de, qui va c'est la vie de Benchmark pour la test, ça va permettre de regarder combien de temps l'OTI prend à transcrire un audio de 2 minutes, dont l'objectif actuellement c'est juste que je parle pendant 2 minutes et c'est au jour sur rapport à la suite transcrit par l'OTI, qui va générer la maîtrique et présenter combien de temps, ça va faire l'OTI pour transcrire cet audio de 2 minutes, l'objectif c'est ici d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'OTI pour transcrire l'OTI parce qu'en fait ça ne sert à rien d'optimiser si on n'a pas de barrem, de comparaison, donc on ne peut pas dire qu'on a accéléré de 1 second, 1 second c'est bien mais 1 second c'est 1000, est-ce que ça a changé quelque chose, est-ce que c'est un changement que réval de la peine, on ne sait pas, donc il faut avoir des maîtriques qui nous indiquent OK, actuellement pour transcrire 2 minutes, ça prend 5,5 secondes, comme ça si on fait un changement qui nous fait passer de 5,5 à 10, on sait qu'on a fait quelque chose d'extérieur, mais si on fait quelque chose qui nous fait passer de 5,5 secondes, la 5,4 secondes, c'est pas la folie et peut-être c'est une tâche qui ne va l'appareillement la peine d'effectuer, donc c'est ça le butue Benjamin Talkchul, c'est vraiment d'avoir des maîtriques solides qui vont permettre de quitter l'évolution du travail, qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le fait.
```

### voie3 — vad_filter=False

```
Ok, donc ceci est un arrachement qui va permettre de, qui va servir de benchmark pour les tests, ça va permettre de regarder combien de temps l'outil prend à transcrire un audio de deux minutes. Donc l'objectif actuellement c'est juste que je parle pendant deux minutes et cet audio sera par la suite transcrit par l'outil qui va générer les métriques et présenter combien de temps ça fera aboutir pour transcrire cet audio de deux minutes. L'objectif c'est d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour réduire le délai que ça prend à l'outil pour transcrire l'audio de deux minutes. Parce qu'en fait ça ne sert à rien d'optimiser si on n'a pas de barren de comparaison donc on peut pas dire on accélérer de une seconde. Une seconde c'est bien mais une seconde c'est humil. Est-ce que ça change quelque chose ? Est-ce que c'est un changement et que révalue la peine ? On ne sait pas. Donc il faut avoir des métriques qui nous indiquent ok, actuellement pour transcrire deux minutes ça prend 55 secondes. Comme ça si on fait un changement qui nous fait passer de 55 à 10 on se couvre. On a fait quelque chose d'extraordinaire mais si on fait quelque chose qui nous fait passer de 55 secondes à 54 secondes c'est pas la folie et peut-être c'est une tâche qui ne valait pas réellement la peine d'effectuer. Donc c'est ça le but du benchmark actuel c'est vraiment d'aller avoir des métriques solides qui vont permettre de quitter l'évolution du travail, qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### voie4 — base+beam1

```
Ok donc c'est ici un arouchement qui va permettre de... qui va s'y avider de benchmark pour... pour... pour... les tests ça va permettre de regarder combien de temps l'outil prend à transcrire au lieu de 2 minutes. Dans l'objectif, franchement c'est juste que je parle pendant 2 minutes et cette audio sur rapport à la suite transcre par l'outil qui va générer la métrique et présenter combien de temps ça va avoir l'outil vous transcre, c'est tout le jeu de 2 minutes. L'objectif c'est ici d'avoir une base fixe qui va permettre d'aller effectuer des optimisations pour faire durer le délai que ça prend l'outil pour transcrire l'outil de 2 minutes. Parce qu'en fait ça n'est-ce à rien d'optimiser si on n'a pas de barrennes de comparaison. Donc on ne peut pas dire... on a accéléré de 1 seconde. 1 seconde c'est bien mais 1 seconde tu mets... est-ce que ça change quelque chose ? Est-ce que c'est un changement qui réveille la peine ? On sait pas. Donc il faut avoir un... des métriques qui nous indiquent. Ok, actuellement pour transcrire 2 minutes ça prend 5 seconds. Comme ça on fait un changement qui nous fait passer de 5 seconds à 10. On se courre, on a fait que quelque chose t'extrôle. Mais si on fait quelque chose qui nous fait passer de 5 seconds la 5x4 seconds c'est pas la folie et peut-être c'est une tâche qui ne va l'apparir vraiment la peine des factues. Donc c'est ça le butue bèche pas t'actuel. C'est vraiment d'avoir des métriques solides qui vont permettre de quitter l'évolution du travail, qui vont permettre de guider comment on pense le projet et dans la vision d'amélioration pour le futur.
```

### voie5 — distil-small.fr

**ECHEC** : 401 Client Error. (Request ID: Root=1-69da74a6-722961cb21c5a4ff279c47b2;812efe8c-d652-4716-b144-8bc4b2c8b3e8)

Repository Not Found for url: https://huggingface.co/api/models/Systran/faster-distil-whisper-small.fr/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

_Généré le 2026-04-11T12:19:50.623348_
