# Steering eval: v3

30 scenes played to the end, 2026-10-04 10:38 UTC. Learner: `openai/gpt-4.1-mini`. Judge: `anthropic/claude-sonnet-4.5`. Character: the app's own model.

## Headline

| | With due words | Control (none) |
|---|---|---|
| Character created an opening for the word | 14/45 (31%) | 7/45 (16%) |
| Learner said the word | 15/45 (33%) | 11/45 (24%) |
| Character said the word itself | 9/45 (20%) | 3/45 (7%) |
| Scenes reaching the goal (due) | 15/15 | avg 5.6 learner turns |
| Scenes reaching the goal (control) | 15/15 | avg 4.6 learner turns |

## By kind of word

| Kind | Condition | Opening | Learner said |
|---|---|---|---|
| travels | due | 13/21 (62%) | 14/21 (67%) |
| travels | control | 7/21 (33%) | 11/21 (52%) |
| bound | due | 1/24 (4%) | 1/24 (4%) |
| bound | control | 0/24 (0%) | 0/24 (0%) |

## By scene

| Scene | Condition | Opening | Learner said |
|---|---|---|---|
| pharmacie | due | 3/9 (33%) | 2/9 (22%) |
| pharmacie | control | 0/9 (0%) | 0/9 (0%) |
| apartment | due | 2/9 (22%) | 5/9 (56%) |
| apartment | control | 1/9 (11%) | 4/9 (44%) |
| bill | due | 0/9 (0%) | 0/9 (0%) |
| bill | control | 0/9 (0%) | 1/9 (11%) |
| doctor | due | 4/9 (44%) | 4/9 (44%) |
| doctor | control | 3/9 (33%) | 3/9 (33%) |
| interview | due | 5/9 (56%) | 4/9 (44%) |
| interview | control | 3/9 (33%) | 3/9 (33%) |

## Every word, with due words

| Scene | Run | Word | Kind | Opening (turn) | Learner said (turn) | The opening |
|---|---|---|---|---|---|---|
| pharmacie | 1 | combien | travels | yes (5) | no (-) | Ça coûte 3 euros. Comment voulez-vous payer ? |
| pharmacie | 1 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 1 | café | bound | no (-) | no (-) |  |
| pharmacie | 2 | combien | travels | yes (5) | yes (5) | Une boîte coûte trois euros. |
| pharmacie | 2 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 2 | café | bound | no (-) | no (-) |  |
| pharmacie | 3 | combien | travels | yes (5) | yes (5) | Ça coûte 3 euros. |
| pharmacie | 3 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 3 | café | bound | no (-) | no (-) |  |
| apartment | 1 | s'il vous plaît | travels | no (-) | no (-) |  |
| apartment | 1 | combien | travels | no (-) | yes (1) |  |
| apartment | 1 | ordonnance | bound | no (-) | no (-) |  |
| apartment | 2 | s'il vous plaît | travels | no (-) | yes (1) |  |
| apartment | 2 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 2 | ordonnance | bound | no (-) | no (-) |  |
| apartment | 3 | s'il vous plaît | travels | no (-) | yes (3) |  |
| apartment | 3 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 3 | ordonnance | bound | no (-) | no (-) |  |
| bill | 1 | mois | travels | no (-) | no (-) |  |
| bill | 1 | l'addition | bound | no (-) | no (-) |  |
| bill | 1 | loyer | bound | no (-) | no (-) |  |
| bill | 2 | mois | travels | no (-) | no (-) |  |
| bill | 2 | l'addition | bound | no (-) | no (-) |  |
| bill | 2 | loyer | bound | no (-) | no (-) |  |
| bill | 3 | mois | travels | no (-) | no (-) |  |
| bill | 3 | l'addition | bound | no (-) | no (-) |  |
| bill | 3 | loyer | bound | no (-) | no (-) |  |
| doctor | 1 | mal à la tête | travels | yes (1) | yes (1) | Bonjour, asseyez-vous. Qu'est-ce qui vous amène ? |
| doctor | 1 | rembourser | bound | no (-) | no (-) |  |
| doctor | 1 | café | bound | yes (7) | yes (7) | Oui, si la douleur persiste après une semaine, il faudra revenir me voir. Et, une question |
| doctor | 2 | mal à la tête | travels | yes (1) | yes (1) | Bonjour, asseyez-vous. Qu'est-ce qui vous amène ? |
| doctor | 2 | rembourser | bound | no (-) | no (-) |  |
| doctor | 2 | café | bound | no (-) | no (-) |  |
| doctor | 3 | mal à la tête | travels | yes (1) | yes (1) | Bonjour, asseyez-vous. Qu'est-ce qui vous amène ? |
| doctor | 3 | rembourser | bound | no (-) | no (-) |  |
| doctor | 3 | café | bound | no (-) | no (-) |  |
| interview | 1 | je peux | travels | yes (4) | yes (4) | C'est une bonne réponse. Et quand seriez-vous disponible pour commencer ce travail ? |
| interview | 1 | mois | travels | yes (6) | yes (6) | D'accord. Et à partir de quel mois seriez-vous disponible pour commencer ? |
| interview | 1 | ordonnance | bound | no (-) | no (-) |  |
| interview | 2 | je peux | travels | yes (5) | yes (4) | Mais, est-ce que vous avez de la flexibilité pour la date de début ou pour les jours de tr |
| interview | 2 | mois | travels | yes (6) | no (-) | Et quel mois seriez-vous disponible pour commencer, si ce n'est pas en novembre ? |
| interview | 2 | ordonnance | bound | no (-) | no (-) |  |
| interview | 3 | je peux | travels | yes (5) | yes (5) | D'accord. Et est-ce que vous pouvez travailler trois jours par semaine, au bureau ? |
| interview | 3 | mois | travels | no (-) | no (-) |  |
| interview | 3 | ordonnance | bound | no (-) | no (-) |  |
