"use client";

import { Keyboard, Mic, Send, Square } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { LyricLine, type LyricWord } from "@/components/stumble/LyricLine";
import { PillButton } from "@/components/stumble/PillButton";
import { useHoldToTalk, type Capture } from "@/hooks/useHoldToTalk";
import { getErrorMessage } from "@/lib/errors";
import { usePlacementMutation } from "@/store/endpoints/progress";
import type { PlacementDto } from "@/types/api";

const MAX_MS = 20_000;

/**
 * Something to attempt, so the mic isn't a blank page. Deliberately English tasks and never French
 * sentences: a French example would get read aloud, and reading is not producing — it would place
 * the learner far above where they can actually hold a scene. Ordered easy to hard.
 */
const TASKS = [
  { title: "Say hello and your name", hint: "Then your age, if it comes." },
  { title: "Count as high as you can", hint: "Stop wherever you run out." },
  { title: "Order a coffee", hint: "Ask what it costs too." },
  { title: "Say what you did yesterday", hint: "Two or three sentences." },
];

/**
 * The headline's claim, shown instead of asserted: one café line, the word that got reached for in
 * English, and the card it becomes. Built from the same components the scene and deck use, so the
 * pitch doubles as an honest preview of the real UI.
 */
const CAUGHT_LINE: LyricWord[] = [
  { text: "Je", state: "on" },
  { text: "voudrais", state: "on" },
  { text: "un", state: "on" },
  { text: "café", state: "on" },
  { text: "avec", state: "on" },
  { text: "du", state: "on" },
  { text: "sugar.", state: "miss" },
];

function LoopPreview() {
  return (
    <div className="w-full">
      <p className="text-[11px] font-extrabold text-ink-2">Léa · barista</p>
      <p className="mt-1 text-[15px] font-bold text-ink-2">Qu&apos;est-ce que je vous sers ?</p>
      <p className="mt-5 text-[11px] font-extrabold text-ink-2">You</p>
      <LyricLine className="mt-1" words={CAUGHT_LINE} animate />
      <div className="mt-5 fade-in" style={{ animationDelay: "560ms" }}>
        <Chip tone="stumble">caught · sugar → sucre</Chip>
        <p className="mt-2 text-[11px] font-extrabold text-ink-2">Due tomorrow, in your own sentence.</p>
      </div>
    </div>
  );
}

type Step = "intro" | "speak" | "result";

export function OnboardingScreen() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("intro");
  const [typing, setTyping] = useState(false);
  const [draft, setDraft] = useState("");
  const [picked, setPicked] = useState<number | null>(null);
  const [result, setResult] = useState<PlacementDto | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [placement, placementState] = usePlacementMutation();

  const submit = useCallback(
    (form: FormData) => {
      setFailure(null);
      placement(form)
        .unwrap()
        .then((r) => {
          setResult(r);
          setStep("result");
        })
        .catch((e: unknown) => setFailure(getErrorMessage(e as Parameters<typeof getErrorMessage>[0]).message));
    },
    [placement],
  );

  const onCapture = useCallback(
    (c: Capture) => {
      if (c.durationMs < 1200 || !c.spoke) {
        setFailure(c.spoke ? "That was quick. Tap again and say a few words." : "Didn't hear anything. Tap again and say a few words.");
        return;
      }
      const form = new FormData();
      form.append("audio", c.blob, `placement.${c.mime.includes("mp4") ? "mp4" : "webm"}`);
      submit(form);
    },
    [submit],
  );
  const mic = useHoldToTalk(onCapture, placementState.isLoading, MAX_MS);

  // Placement is composed, not reacted to: you need both hands free to think, so it is tap to start
  // and tap to stop rather than hold. Without the press to feel, the time left has to be visible.
  const [span, setSpan] = useState({ startedAt: 0, now: 0 });
  useEffect(() => {
    if (!mic.holding) return;
    const id = window.setInterval(() => setSpan((s) => ({ ...s, now: Date.now() })), 200);
    return () => window.clearInterval(id);
  }, [mic.holding]);
  const leftMs = Math.max(0, MAX_MS - (span.now - span.startedAt));

  const onMicTap = () => {
    if (mic.holding) {
      mic.stop();
      return;
    }
    const t = Date.now();
    setSpan({ startedAt: t, now: t });
    void mic.start();
  };

  const sendTyped = () => {
    const text = draft.trim();
    if (!text) return;
    const form = new FormData();
    form.append("text", text);
    submit(form);
  };

  if (step === "intro") {
    return (
      <div className="flex flex-1 flex-col" data-scene="cafe">
        <Blob color="scene" className="flex flex-1 flex-col pt-14 pb-6">
          <div className="flex min-h-0 flex-1 items-center overflow-hidden pb-8">
            <LoopPreview />
          </div>
          <p className="text-[44px] font-black leading-none tracking-[-0.03em]">
            Stumble<span className="text-stumble">.</span>
          </p>
          <h1 className="mt-4 text-[26px] font-extrabold leading-[1.1] tracking-[-0.02em]">
            Speak French. The words you can&apos;t find become the words you review.
          </h1>
          <p className="mt-3 text-sm font-bold text-ink-2">
            Real scenes, a real voice on the other side. Every time you freeze, fall back to English, or get corrected,
            that word is caught and comes back until it&apos;s yours.
          </p>
          <div className="mt-4 flex gap-2">
            <Chip tone="ink">French</Chip>
            <Chip>more languages later</Chip>
          </div>
        </Blob>
        <div className="px-5 pb-8 pt-4">
          <PillButton onClick={() => setStep("speak")}>Continue</PillButton>
        </div>
      </div>
    );
  }

  if (step === "result" && result) {
    return (
      <div className="flex flex-1 flex-col" data-scene="cafe">
        <Blob color="scene" className="flex flex-1 flex-col justify-end pt-14 pb-6">
          <Chip tone="ink">placed at {result.level}</Chip>
          <h1 className="mt-3 text-[30px] font-extrabold leading-[1.05] tracking-[-0.03em]">
            {result.cardsAdded === 0
              ? "Clean. Let's find the gaps in a real scene."
              : result.cardsAdded === 1
                ? "One stumble already caught."
                : `${result.cardsAdded} stumbles already caught.`}
          </h1>
          <p className="mt-2 text-sm font-bold text-ink-2">{result.note}</p>
          {result.stumbles.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {result.stumbles.map((s, i) => (
                <Chip key={i} tone="stumble">
                  {s.said ? `${s.said} → ` : ""}
                  {s.target}
                </Chip>
              ))}
            </div>
          ) : null}
        </Blob>
        <div className="px-5 pb-8 pt-4">
          <PillButton onClick={() => router.replace("/scene/cafe")}>
            <Mic className="size-5" strokeWidth={2.25} />
            Start Café
          </PillButton>
          <PillButton variant="paper" className="mt-2 border border-ink/15" onClick={() => router.replace("/")}>
            Look around first
          </PillButton>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col" data-scene="cafe">
      <Blob color="scene" className="flex flex-1 flex-col pt-14">
        <p className="text-xs font-bold text-ink-2">Step 2 of 2</p>
        <h1 className="mt-2 text-[30px] font-extrabold leading-[1.05] tracking-[-0.03em]">
          Say anything you know in French.
        </h1>
        <p className="mt-2 text-sm font-bold text-ink-2">
          Even just <em>bonjour</em>. Up to twenty seconds. No test, no score: it picks your first scene and catches the
          first words you reach for and miss.
        </p>

        <div className="mt-5 flex-1">
          <p className="text-xs font-bold text-ink-2">Nothing coming? Try one of these.</p>
          <div className="mt-2 grid gap-2" role="radiogroup" aria-label="Something to try">
            {TASKS.map((t, i) => {
              const on = i === picked;
              return (
                <button
                  key={t.title}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  onClick={() => setPicked(on ? null : i)}
                  className={`rounded-2xl px-3 py-2.5 text-left transition-colors ${on ? "bg-ink text-paper" : "bg-ink/8 text-ink"}`}
                >
                  <span className="block text-[13px] font-extrabold">{t.title}</span>
                  <span className={`block text-[11px] font-bold ${on ? "text-paper-2" : "text-ink/65"}`}>{t.hint}</span>
                </button>
              );
            })}
          </div>
        </div>

        {failure || mic.error ? <p className="mb-3 text-center text-xs font-bold text-stumble">{failure ?? mic.error}</p> : null}
        {typing ? (
          <form
            className="mb-6 flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              sendTyped();
            }}
          >
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Bonjour, je m'appelle…"
              lang="fr"
              className="h-12 flex-1 rounded-pill bg-paper px-4 text-[15px] font-bold text-ink outline-none placeholder:text-ink/65"
            />
            <button
              type="submit"
              aria-label="Send"
              disabled={placementState.isLoading || !draft.trim()}
              className="grid size-12 place-items-center rounded-pill bg-ink text-paper disabled:opacity-50"
            >
              <Send className="size-5" strokeWidth={2.25} />
            </button>
          </form>
        ) : (
          <div className="mb-6">
            <button
              type="button"
              aria-label={mic.holding ? "Stop recording" : "Start recording"}
              aria-pressed={mic.holding}
              disabled={!mic.supported || placementState.isLoading}
              onClick={onMicTap}
              className={`mx-auto grid size-[84px] touch-none select-none place-items-center rounded-pill text-paper transition-[background-color,box-shadow,transform] duration-200 ease-out-expo disabled:opacity-50 ${
                mic.holding
                  ? "scale-105 bg-stumble shadow-[0_0_0_16px_color-mix(in_oklch,var(--color-stumble)_25%,transparent)]"
                  : "bg-ink shadow-[0_0_0_12px_color-mix(in_oklch,var(--color-ink)_12%,transparent)]"
              }`}
            >
              {mic.holding ? <Square className="size-7 fill-current" strokeWidth={2.25} /> : <Mic className="size-8" strokeWidth={2.25} />}
            </button>
            <div className="mt-4 flex items-center justify-center gap-4 text-[11px] font-extrabold text-ink-2">
              <span>
                {placementState.isLoading
                  ? "listening…"
                  : mic.holding
                    ? `tap when done · ${Math.ceil(leftMs / 1000)}s left`
                    : "tap to start"}
              </span>
              <span aria-hidden="true">·</span>
              <button type="button" className="flex items-center gap-1 underline-offset-2 hover:underline" onClick={() => setTyping(true)}>
                <Keyboard className="size-3.5" strokeWidth={2.5} />
                type instead
              </button>
            </div>
          </div>
        )}
      </Blob>
    </div>
  );
}
