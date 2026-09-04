"use client";

import { Keyboard, Mic, Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import { useHoldToTalk, type Capture } from "@/hooks/useHoldToTalk";
import { getErrorMessage } from "@/lib/errors";
import { usePlacementMutation } from "@/store/endpoints/progress";
import type { PlacementDto } from "@/types/api";

const MAX_MS = 20_000;

type Step = "intro" | "speak" | "result";

export function OnboardingScreen() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("intro");
  const [typing, setTyping] = useState(false);
  const [draft, setDraft] = useState("");
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
      if (c.durationMs < 1200) {
        setFailure("That was quick. Hold and say a few words.");
        return;
      }
      const form = new FormData();
      form.append("audio", c.blob, `placement.${c.mime.includes("mp4") ? "mp4" : "webm"}`);
      submit(form);
    },
    [submit],
  );
  const mic = useHoldToTalk(onCapture, placementState.isLoading, MAX_MS);

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
        <Blob color="scene" className="flex flex-1 flex-col justify-end pt-14 pb-6">
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
        <div className="flex-1" />
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
              aria-label="Hold to speak"
              aria-pressed={mic.holding}
              disabled={!mic.supported || placementState.isLoading}
              {...mic.handlers}
              className={`mx-auto grid size-[84px] touch-none select-none place-items-center rounded-pill text-paper transition-[background-color,box-shadow,transform] duration-200 ease-out-expo disabled:opacity-50 ${
                mic.holding
                  ? "scale-105 bg-stumble shadow-[0_0_0_16px_color-mix(in_oklch,var(--color-stumble)_25%,transparent)]"
                  : "bg-ink shadow-[0_0_0_12px_color-mix(in_oklch,var(--color-ink)_12%,transparent)]"
              }`}
            >
              <Mic className="size-8" strokeWidth={2.25} />
            </button>
            <div className="mt-4 flex items-center justify-center gap-4 text-[11px] font-extrabold text-ink-2">
              <span>{placementState.isLoading ? "listening…" : mic.holding ? "release when done" : "hold to speak"}</span>
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
