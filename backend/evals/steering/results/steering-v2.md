# Steering eval: v2

30 scenes played to the end, 2026-10-04 10:30 UTC. Learner: `openai/gpt-4.1-mini`. Judge: `anthropic/claude-sonnet-4.5`. Character: the app's own model.

> **What v2 changed:** the one-line "create natural openings" instruction was replaced, for scenes with due words only, by: say each due word before the scene ends; never say it yourself first; in the beat where it fits, ask a question only it answers or leave out what it's needed to ask for, and let it change how that beat is delivered ("combien": ask how many, or let them ask the price instead of stating it); a word that fits no beat gets one short aside in role ("Vous avez pris un café ce matin ?"). The control's prompt was byte-identical to v1. The change didn't help and was not kept; the exact text is in this commit's message.

## Headline

| | With due words | Control (none) |
|---|---|---|
| Character created an opening for the word | 7/45 (16%) | 6/45 (13%) |
| Learner said the word | 10/45 (22%) | 9/45 (20%) |
| Character said the word itself | 7/45 (16%) | 3/45 (7%) |
| Scenes reaching the goal (due) | 15/15 | avg 5.1 learner turns |
| Scenes reaching the goal (control) | 15/15 | avg 4.6 learner turns |

## By kind of word

| Kind | Condition | Opening | Learner said |
|---|---|---|---|
| travels | due | 7/21 (33%) | 10/21 (48%) |
| travels | control | 6/21 (29%) | 9/21 (43%) |
| bound | due | 0/24 (0%) | 0/24 (0%) |
| bound | control | 0/24 (0%) | 0/24 (0%) |

## By scene

| Scene | Condition | Opening | Learner said |
|---|---|---|---|
| pharmacie | due | 0/9 (0%) | 2/9 (22%) |
| pharmacie | control | 0/9 (0%) | 1/9 (11%) |
| apartment | due | 2/9 (22%) | 3/9 (33%) |
| apartment | control | 0/9 (0%) | 2/9 (22%) |
| bill | due | 1/9 (11%) | 1/9 (11%) |
| bill | control | 0/9 (0%) | 0/9 (0%) |
| doctor | due | 3/9 (33%) | 3/9 (33%) |
| doctor | control | 3/9 (33%) | 3/9 (33%) |
| interview | due | 1/9 (11%) | 1/9 (11%) |
| interview | control | 3/9 (33%) | 3/9 (33%) |

## Every word, with due words

| Scene | Run | Word | Kind | Opening (turn) | Learner said (turn) | The opening |
|---|---|---|---|---|---|---|
| pharmacie | 1 | combien | travels | no (-) | yes (4) |  |
| pharmacie | 1 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 1 | café | bound | no (-) | no (-) |  |
| pharmacie | 2 | combien | travels | no (-) | yes (4) |  |
| pharmacie | 2 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 2 | café | bound | no (-) | no (-) |  |
| pharmacie | 3 | combien | travels | no (-) | no (-) |  |
| pharmacie | 3 | l'addition | bound | no (-) | no (-) |  |
| pharmacie | 3 | café | bound | no (-) | no (-) |  |
| apartment | 1 | s'il vous plaît | travels | no (-) | no (-) |  |
| apartment | 1 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 1 | ordonnance | bound | no (-) | no (-) |  |
| apartment | 2 | s'il vous plaît | travels | no (-) | no (-) |  |
| apartment | 2 | combien | travels | no (-) | yes (1) |  |
| apartment | 2 | ordonnance | bound | no (-) | no (-) |  |
| apartment | 3 | s'il vous plaît | travels | no (-) | no (-) |  |
| apartment | 3 | combien | travels | yes (1) | yes (1) | Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ? |
| apartment | 3 | ordonnance | bound | no (-) | no (-) |  |
| bill | 1 | mois | travels | yes (2) | no (-) | D'accord, une facture. De quel mois s'agit-il ? |
| bill | 1 | l'addition | bound | no (-) | no (-) |  |
| bill | 1 | loyer | bound | no (-) | no (-) |  |
| bill | 2 | mois | travels | no (-) | no (-) |  |
| bill | 2 | l'addition | bound | no (-) | no (-) |  |
| bill | 2 | loyer | bound | no (-) | no (-) |  |
| bill | 3 | mois | travels | no (-) | yes (2) |  |
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
| interview | 1 | je peux | travels | no (-) | no (-) |  |
| interview | 1 | mois | travels | no (-) | no (-) |  |
| interview | 1 | ordonnance | bound | no (-) | no (-) |  |
| interview | 2 | je peux | travels | no (-) | no (-) |  |
| interview | 2 | mois | travels | no (-) | no (-) |  |
| interview | 2 | ordonnance | bound | no (-) | no (-) |  |
| interview | 3 | je peux | travels | yes (4) | yes (4) | Et quand seriez-vous disponible pour commencer à travailler ? |
| interview | 3 | mois | travels | no (-) | no (-) |  |
| interview | 3 | ordonnance | bound | no (-) | no (-) |  |
