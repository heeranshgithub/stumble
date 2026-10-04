# Later

Things decided against for the hackathon, on purpose, in the order they should be taken on. The first one is the foundation: the others all change the prompt or the model, and without it there is no way to know a change didn't break something.

1. **An eval harness for the turn prompt** — every reply-quality bug so far was found by hand and fixed blind. The guardrails now have one (`backend/evals/guardrails`, see [guardrails.md](guardrails.md)); its runner and case format are the template for this.
2. **Make the next scene ask for your words** — measured: it barely does. A due word comes up about as often with the scene told about it as without, and a word tied to its first scene never comes up.
3. **Faster turns** — the wait is the one thing a learner feels on every turn; swapping the model is one env var, and unsafe without 1.
4. **Speaking time on the debrief** — the only time figure that is about the learner; the data is already returned, just not stored.
5. **Corrections that aren't errors** — politeness logged as grammar (not seen yet), and a homophone the transcriber spelled wrong (seen; held by a prompt rule only).

## 1. An eval harness for the turn prompt

The backend tests run against fake providers and prove the plumbing: a stumble becomes a card, FSRS reschedules, a win is credited to the turn that contains it. None of them see what the model actually says. Every reply-quality bug so far (the barista asking the learner the price, the same question asked three times in different words, a greeting on every turn) was found by playing a scene and fixed by editing the prompt, with no way to know the next edit doesn't undo it.

The shape:

- `backend/evals/cases/*.json`, one per case: `{scene, patience, due_cards, turns, checks}`. Each bug found by playing becomes a case; the "c'est par carte" screenshot is `cafe_barista_asks_price`.
- `backend/evals/run.py` builds the messages with the real `system_prompt` and `learner_turn`, calls the real `OpenRouterChat` five times per case, runs the checks, prints a pass rate per case, exits non-zero under a threshold. Run before committing a prompt change or swapping `OPENROUTER_MODEL`, not on every test run.
- Two kinds of check. Deterministic, in Python: valid JSON, no leading greeting, the `coffee` case yields one `code_switch` with target `café`, a clean turn yields zero stumbles. Judged: a second model call with the scene, the role, the reply and one yes/no question ("does this reply ask the learner for something only the character would know?").
- Two-sided from the start. Over-flagging is the silent failure: a phantom card takes one of the twelve daily review slots, steers the next scene toward a word the learner already has, and gets stickier on every repeat because a second flag is a lapse. So the seed set carries as many "nothing should be caught" cases as "this should be caught" ones.

What exists today instead, all deterministic: a confidence floor (`stumble_confidence_min`) and a target-length cap, so a hedged or whole-sentence stumble never becomes a card; one retry when a reply trails off mid-sentence; a due word said cleanly counted as a win even when the model forgets to report it; and the scene beats and facts, which remove the reason the character improvises rather than forbidding the result.

## 2. Make the next scene ask for your words

The pitch is that the words you stumble on come back: the next scene is told which ones are due and steers you into saying them. `backend/evals/steering` measures it: every scene from the pharmacy on, played to the end by a simulated A2 learner who is never told the words, once handed three due words from earlier scenes and once handed none, three runs each, with a judge reading every transcript for openings.

The scene barely steers. The character created an opening for 20% of due words, against 16% for the same words in the control, and most of those openings were the scene's fixed first line, there either way. Words that travel between scenes (prices, months, "je peux") came up about half the time, mostly because the scenes invite them anyway; words tied to the scene they came from (café, ordonnance) came up 0 times in 24. A sharper instruction, with what an opening is and a short aside for words that fit no beat, changed nothing (16% against 13%), and the one aside it produced was awkward ("vous avez une ordonnance pour des lunettes ?"). The model follows the beats, which are concrete, and lets the due words go. One flaw in that test: the instruction's own examples ("combien", a doctor asking about café) were among the test words, which is leakage. It still changed nothing, so the result stands, but future examples should come from outside the test set.

So the fix isn't another prompt line. In the order worth trying, each measured with the same eval:

- **Plan per scene.** At scene start, once the due words are known, one call assigns each word that fits to a beat and writes the concrete move ("payment beat: let them ask the price"); each turn is told the move for its beat, not a list of words. One call per scene, hidden behind the opening line.
- **Choose the scene by its words.** A word tied to its first scene goes back to a replay of that scene, where it belongs, instead of being forced into the next new one.
- **Say what's true until then.** Review already makes the learner say every due word aloud, in its original sentence. That part of the claim holds; the scene steering is the part that doesn't yet.

## 3. Faster turns

A turn is three sequential calls (Whisper, the chat model, ElevenLabs first byte) and lands around 2.5–5 s. The thinking line makes the wait legible, and the voice now starts synthesizing as the reply goes out so the words and the sound land together; neither shortens the wait itself. In order of payoff: a faster chat model (one env var, and exactly where the evals earn their keep), then streaming the reply into TTS sentence by sentence, which means the reply can no longer be one JSON blob.

## 4. Speaking time on the debrief

The debrief used to show the scene's wall-clock length. Dropped: most of a scene's minutes are the character's (her line, the think gap, the learner reading), so the number said nothing about the learner. The number that would is how long the learner actually spoke. Whisper returns the audio duration on every turn (`Transcript.duration_s`); it isn't stored. Store it on the learner turn, sum it, and the debrief can say "you spoke for 1:12", a figure that should grow scene over scene. Typed turns count as zero, which is right.

## 5. Corrections that aren't errors

Two ways a correction can be logged for something the learner didn't get wrong.

**Style.** "Je veux un café" is correct French. In the *real* register the model may log it as a correction to *je voudrais*. That's politeness, not grammar, and it becomes a card. Not seen yet, so no rule for it; when it shows up, the fix is one line in `_RULES` and one eval case.

**Homophones.** The model judges a transcript, not the audio. When the learner says *j'ai payé* and Whisper writes *je payé*, the model sees a grammar error and logs a correction for a mistake nobody made. This was seen, and a rule in `_RULES` now says a correction must be audible: if "said" and "target" sound the same (je/j'ai, et/est, ses/ces/c'est, -é/-er/-ez, a/à), log nothing. That rule only asks the model to behave, where most rules with a detectable shape are also enforced in code. The code version: encode both phrases phonetically for French and drop the correction when the encodings match. Worth building once the eval harness (1) shows the prompt rule leaking.
