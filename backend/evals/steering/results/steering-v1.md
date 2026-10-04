# Steering eval: v1

30 scenes played to the end, 2026-10-04 05:34 UTC. Learner: `openai/gpt-4.1-mini`. Judge: `anthropic/claude-sonnet-4.5`. Character: the app's own model.

## Headline

| | With due words | Control (none) |
|---|---|---|
| Character created an opening for the word | 9/45 (20%) | 7/45 (16%) |
| Learner said the word | 12/45 (27%) | 10/45 (22%) |
| Character said the word itself | 5/45 (11%) | 3/45 (7%) |
| Scenes reaching the goal (due) | 15/15 | avg 4.7 learner turns |
| Scenes reaching the goal (control) | 15/15 | avg 4.7 learner turns |

## By kind of word

| Kind | Condition | Opening | Learner said |
|---|---|---|---|
| travels | due | 9/21 (43%) | 12/21 (57%) |
| travels | control | 7/21 (33%) | 10/21 (48%) |
| bound | due | 0/24 (0%) | 0/24 (0%) |
| bound | control | 0/24 (0%) | 0/24 (0%) |

## By scene

| Scene | Condition | Opening | Learner said |
|---|---|---|---|
| pharmacie | due | 1/9 (11%) | 1/9 (11%) |
| pharmacie | control | 0/9 (0%) | 0/9 (0%) |
| apartment | due | 3/9 (33%) | 4/9 (44%) |
| apartment | control | 1/9 (11%) | 4/9 (44%) |
| bill | due | 1/9 (11%) | 1/9 (11%) |
| bill | control | 0/9 (0%) | 0/9 (0%) |
| doctor | due | 3/9 (33%) | 3/9 (33%) |
| doctor | control | 3/9 (33%) | 3/9 (33%) |
| interview | due | 1/9 (11%) | 3/9 (33%) |
| interview | control | 3/9 (33%) | 3/9 (33%) |

## Every word, with due words

| Scene | Run | Word | Kind | Opening (turn) | Learner said (turn) | The opening |
|---|---|---|---|---|---|---|
| pharmacie | 1 | combien | travels | no (-) | no (-) |  |
| pharmacie | 1 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 1 | café | bound | no (-) | no (-) |  |
| pharmacie | 2 | combien | travels | yes (4) | yes (4) | Oui, c'est possible d'acheter des médicaments sans ordonnance. Préférez-vous un sirop ou d |
| pharmacie | 2 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 2 | café | bound | no (-) | no (-) |  |
| pharmacie | 3 | combien | travels | no (-) | no (-) |  |
| pharmacie | 3 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 3 | café | bound | no (-) | no (-) |  |
| apartment | 1 | s'il vous plaît | travels | no (-) | yes (1) |  |
| apartment | 1 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 1 | ordonnance | bound | no (-) | no (-) |  |
| apartment | 2 | s'il vous plaît | travels | no (-) | no (-) |  |
| apartment | 2 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 2 | ordonnance | bound | no (-) | no (-) |  |
| apartment | 3 | s'il vous plaît | travels | no (-) | no (-) |  |
| apartment | 3 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 3 | ordonnance | bound | no (-) | no (-) |  |
| bill | 1 | mois | travels | yes (2) | yes (2) | C'est pour le mois dernier ? |
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
| doctor | 1 | café | bound | no (-) | no (-) |  |
| doctor | 2 | mal à la tête | travels | yes (1) | yes (1) | Bonjour, asseyez-vous. Qu'est-ce qui vous amène ? |
| doctor | 2 | rembourser | bound | no (-) | no (-) |  |
| doctor | 2 | café | bound | no (-) | no (-) |  |
| doctor | 3 | mal à la tête | travels | yes (1) | yes (1) | Bonjour, asseyez-vous. Qu'est-ce qui vous amène ? |
| doctor | 3 | rembourser | bound | no (-) | no (-) |  |
| doctor | 3 | café | bound | no (-) | no (-) |  |
| interview | 1 | je peux | travels | yes (4) | yes (4) | Et quand seriez-vous disponible pour commencer ce poste ? |
| interview | 1 | mois | travels | no (-) | no (-) |  |
| interview | 1 | ordonnance | bound | no (-) | no (-) |  |
| interview | 2 | je peux | travels | no (-) | yes (3) |  |
| interview | 2 | mois | travels | no (-) | no (-) |  |
| interview | 2 | ordonnance | bound | no (-) | no (-) |  |
| interview | 3 | je peux | travels | no (-) | yes (5) |  |
| interview | 3 | mois | travels | no (-) | no (-) |  |
| interview | 3 | ordonnance | bound | no (-) | no (-) |  |
