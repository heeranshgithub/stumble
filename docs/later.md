# Later

Things decided against for the hackathon, on purpose, in the order they should be taken on. The first one is the foundation: the others all change the prompt or the model, and without it there is no way to know a change didn't break something.

1. **An eval harness for the turn prompt** — every reply-quality bug so far was found by hand and fixed blind.
2. **Faster turns** — the wait is the one thing a learner feels on every turn; swapping the model is one env var, and unsafe without 1.
3. **Speaking time on the debrief** — the only time figure that is about the learner; the data is already returned, just not stored.
4. **Style is not an error** — parked until it is actually seen.

## 1. An eval harness for the turn prompt

The backend tests run against fake providers and prove the plumbing: a stumble becomes a card, FSRS reschedules, a win is credited to the turn that contains it. None of them see what the model actually says. Every reply-quality bug so far (the barista asking the learner the price, the same question asked three times in different words, a greeting on every turn) was found by playing a scene and fixed by editing the prompt, with no way to know the next edit doesn't undo it.

The shape:

- `backend/evals/cases/*.json`, one per case: `{scene, patience, due_cards, turns, checks}`. Each bug found by playing becomes a case; the "c'est par carte" screenshot is `cafe_barista_asks_price`.
- `backend/evals/run.py` builds the messages with the real `system_prompt` and `learner_turn`, calls the real `OpenRouterChat` five times per case, runs the checks, prints a pass rate per case, exits non-zero under a threshold. Run before committing a prompt change or swapping `OPENROUTER_MODEL`, not on every test run.
- Two kinds of check. Deterministic, in Python: valid JSON, no leading greeting, the `coffee` case yields one `code_switch` with target `café`, a clean turn yields zero stumbles. Judged: a second model call with the scene, the role, the reply and one yes/no question ("does this reply ask the learner for something only the character would know?").
- Two-sided from the start. Over-flagging is the silent failure: a phantom card takes one of the twelve daily review slots, steers the next scene toward a word the learner already has, and gets stickier on every repeat because a second flag is a lapse. So the seed set carries as many "nothing should be caught" cases as "this should be caught" ones.

What exists today instead, all deterministic: a confidence floor (`stumble_confidence_min`) and a target-length cap, so a hedged or whole-sentence stumble never becomes a card; one retry when a reply trails off mid-sentence; a due word said cleanly counted as a win even when the model forgets to report it; and the scene beats and facts, which remove the reason the character improvises rather than forbidding the result.

## 2. Faster turns

A turn is three sequential calls (Whisper, the chat model, ElevenLabs first byte) and lands around 2.5–5 s. The thinking line makes the wait legible, and the voice now starts synthesizing as the reply goes out so the words and the sound land together; neither shortens the wait itself. In order of payoff: a faster chat model (one env var, and exactly where the evals earn their keep), then streaming the reply into TTS sentence by sentence, which means the reply can no longer be one JSON blob.

## 3. Speaking time on the debrief

The debrief used to show the scene's wall-clock length. Dropped: most of a scene's minutes are the character's (her line, the think gap, the learner reading), so the number said nothing about the learner. The number that would is how long the learner actually spoke. Whisper returns the audio duration on every turn (`Transcript.duration_s`); it isn't stored. Store it on the learner turn, sum it, and the debrief can say "you spoke for 1:12", a figure that should grow scene over scene. Typed turns count as zero, which is right.

## 4. Style is not an error

"Je veux un café" is correct French. In the *real* register the model may log it as a correction to *je voudrais*. That's politeness, not grammar, and it becomes a card. Not seen yet, so no rule for it; when it shows up, the fix is one line in `_RULES` and one eval case.
