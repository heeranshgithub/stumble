"use client";

import { ChevronLeft, Mic, Play } from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";

import { Chip } from "@/components/stumble/Chip";
import { GradeRow, type Grade } from "@/components/stumble/GradeRow";
import { PillButton } from "@/components/stumble/PillButton";
import { useHoldToTalk, type Capture } from "@/hooks/useHoldToTalk";
import { useSpeaker } from "@/hooks/useSpeaker";
import { getErrorMessage } from "@/lib/errors";
import { useAttemptCardMutation, useGetDueReviewsQuery, useGradeCardMutation } from "@/store/endpoints/reviews";
import { useGetTodayQuery } from "@/store/endpoints/today";
import type { ReviewCardDto } from "@/types/api";

type Attempt = { heard: string; matched: boolean } | null;

export function ReviewScreen() {
  const { data, error, isLoading, refetch } = useGetDueReviewsQuery();
  const [index, setIndex] = useState(0);
  const [reviewed, setReviewed] = useState(0);
  const [remaining, setRemaining] = useState<number | null>(null);

  if (isLoading) return <Skeleton />;
  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <Shell title="Couldn't load your reviews." body={e.message} requestId={e.requestId}>
        <PillButton onClick={() => void refetch()}>Try again</PillButton>
      </Shell>
    );
  }

  const cards = data.cards;
  if (cards.length === 0) return <Done reviewed={0} remaining={0} />;
  const card = cards[index];
  if (!card) return <Done reviewed={reviewed} remaining={remaining ?? 0} />;

  return (
    <Card
      key={card.id ?? index}
      card={card}
      position={index + 1}
      total={cards.length}
      onGraded={(left) => {
        setReviewed((n) => n + 1);
        setRemaining(left);
        setIndex((i) => i + 1);
      }}
    />
  );
}

function Card({
  card,
  position,
  total,
  onGraded,
}: {
  card: ReviewCardDto;
  position: number;
  total: number;
  onGraded: (remaining: number) => void;
}) {
  const [revealed, setRevealed] = useState(false);
  const [attempt, setAttempt] = useState<Attempt>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [attemptCard, attemptState] = useAttemptCardMutation();
  const [gradeCard, gradeState] = useGradeCardMutation();
  const speaker = useSpeaker();
  const cardId = card.id ?? "";

  const onCapture = useCallback(
    (c: Capture) => {
      const form = new FormData();
      form.append("audio", c.blob, `attempt.${c.mime.includes("mp4") ? "mp4" : "webm"}`);
      attemptCard({ id: cardId, form })
        .unwrap()
        .then((a) => {
          setAttempt(a);
          setRevealed(true);
        })
        .catch((e: unknown) => setFailure(getErrorMessage(e as Parameters<typeof getErrorMessage>[0]).message));
    },
    [attemptCard, cardId],
  );
  const mic = useHoldToTalk(onCapture, revealed || attemptState.isLoading);

  const grade = (g: Grade) => {
    gradeCard({ id: cardId, rating: g })
      .unwrap()
      .then((r) => onGraded(r.remainingDue))
      .catch((e: unknown) => setFailure(getErrorMessage(e as Parameters<typeof getErrorMessage>[0]).message));
  };

  const [before, after] = splitContext(card.context, card.target);
  // A sentence that is nothing but the slot gives the learner no scaffold to build from.
  const bare = `${before}${after}`.replace(/[\s.!?,…]/g, "") === "";
  const isFreeze = card.type === "freeze";

  return (
    <div
      className="flex flex-1 flex-col bg-scene"
      data-scene="review"
      onPointerDownCapture={() => speaker.unlock()}
    >
      <header className="flex items-center justify-between px-5 pt-12 pb-2">
        <Link href="/" className="flex items-center gap-1 text-xs font-extrabold">
          <ChevronLeft className="size-4" strokeWidth={2.5} />
          Review · {position} of {total}
        </Link>
        <Chip>
          {card.sceneTitle}
          {card.lapses > 0 ? ` · ×${card.lapses + 1}` : ""}
        </Chip>
      </header>
      <div className="flex gap-1 px-5">
        {Array.from({ length: total }, (_, i) => (
          <i key={i} className={`h-1.5 flex-1 rounded-full ${i < position ? "bg-ink" : "bg-ink/20"}`} />
        ))}
      </div>

      <div className="flex flex-1 flex-col px-5 pt-6">
        {card.promptLine ? (
          <>
            <p className="text-xs font-bold text-ink-2">{card.characterName || "They"} asked</p>
            <p className="text-[18px] font-extrabold leading-tight tracking-[-0.01em] text-ink/65">
              « {card.promptLine} »
            </p>
          </>
        ) : null}
        {/* The sentence is the learner's, with the slot fixed: never "You said" over the corrected form.
            When the whole answer is the slot and no question was asked, the slip itself is the cue. */}
        <p className={`text-xs font-bold text-ink-2 ${card.promptLine ? "mt-5" : ""}`}>
          {isFreeze
            ? "You were trying to say"
            : revealed
              ? "Your sentence, fixed"
              : bare && !card.promptLine
                ? `Not “${card.said}” — say it the French way`
                : "Your sentence"}
        </p>
        <p className="mt-1 text-[28px] font-extrabold leading-[1.15] tracking-[-0.02em]">
          {before}
          {revealed ? (
            <span className="lyr-word-in text-ink underline decoration-ink decoration-[3px] underline-offset-[6px]">
              {card.target}
            </span>
          ) : (
            <span className="inline-block min-w-[96px] border-b-[3px] border-ink align-baseline">&nbsp;</span>
          )}
          {after}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {isFreeze ? (
            <Chip tone="stumble">you froze here</Chip>
          ) : (
            <Chip tone="stumble">
              you said &ldquo;{card.said}&rdquo;
            </Chip>
          )}
          {attempt ? (
            <Chip tone={attempt.matched ? "ink" : "muted"}>
              heard &ldquo;{attempt.heard}&rdquo; · {attempt.matched ? "that's it" : "not quite"}
            </Chip>
          ) : null}
        </div>

        <div className="flex-1" />

        {!revealed ? (
          <div className="pb-6">
            {failure || mic.error ? (
              <p className="mb-2 text-center text-xs font-bold text-stumble">{failure ?? mic.error}</p>
            ) : null}
            <button
              type="button"
              aria-label="Hold to say it"
              aria-pressed={mic.holding}
              disabled={!mic.supported || attemptState.isLoading}
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
              <span>{attemptState.isLoading ? "listening…" : mic.holding ? "release" : "hold and say it"}</span>
              <span aria-hidden="true">·</span>
              <button type="button" className="underline-offset-2 hover:underline" onClick={() => setRevealed(true)}>
                tap to reveal
              </button>
            </div>
          </div>
        ) : null}
      </div>

      {revealed ? (
        <section className="sheet-up rounded-t-[28px] bg-ink px-5 pt-5 pb-8 text-paper">
          <p className="text-[10px] font-extrabold uppercase tracking-[0.12em] text-paper-2">Answer</p>
          <div className="flex items-center justify-between gap-3">
            <p className="text-[34px] font-extrabold leading-none tracking-tight">{card.target}</p>
            <button
              type="button"
              aria-label="Play"
              onClick={() => void speaker.play(card.audioUrl)}
              className="grid size-11 flex-none place-items-center rounded-pill bg-paper/15 text-paper"
            >
              <Play className="size-5 fill-current" strokeWidth={0} />
            </button>
          </div>
          {speaker.error ? <p className="mt-2 text-xs font-bold text-paper-2">{speaker.error}</p> : null}
          {!isFreeze && card.said ? (
            <p className="mt-1 text-sm text-paper-2">
              not &ldquo;{card.said}&rdquo;
            </p>
          ) : null}
          <p className="mt-4 text-center text-[11px] font-extrabold text-paper-2">
            {attempt?.matched ? "you said it. how did it feel?" : "how did that go?"}
          </p>
          <div className="mt-2">
            <GradeRow intervals={card.intervals} onGrade={grade} disabled={gradeState.isLoading} />
          </div>
          {failure ? <p className="mt-2 text-center text-xs font-bold text-stumble">{failure}</p> : null}
        </section>
      ) : null}
    </div>
  );
}

function splitContext(context: string, target: string): [string, string] {
  if (context.includes("___")) {
    const [b, ...rest] = context.split("___");
    return [b ?? "", rest.join("___")];
  }
  const i = context.toLowerCase().indexOf(target.toLowerCase());
  if (i >= 0) return [context.slice(0, i), context.slice(i + target.length)];
  return [context ? `${context} ` : "", ""];
}

function Done({ reviewed, remaining }: { reviewed: number; remaining: number }) {
  const { data } = useGetTodayQuery();
  const scene = data?.nextScene;
  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <div className="flex flex-1 flex-col justify-end bg-scene px-5 pb-6 pt-14">
        <p className="text-xs font-bold text-ink-2">Review</p>
        <h1 className="mt-2 text-[34px] font-extrabold leading-[1] tracking-[-0.03em]">
          {reviewed === 0 ? (
            <>
              Nothing due.
              <br />
              Go speak.
            </>
          ) : (
            <>
              {reviewed} reviewed.
              <br />
              {remaining > 0 ? `${remaining} still due.` : "Deck's clear."}
            </>
          )}
        </h1>
        <p className="mt-2 text-xs font-bold text-ink-2">
          {scene ? `${scene.title} is open${scene.usesDueCards.length ? ` and will use ${scene.usesDueCards.length} of these` : ""}.` : "Every scene cleared."}
        </p>
      </div>
      <div className="px-5 pb-8 pt-4">
        {scene ? (
          <PillButton href={`/scene/${scene.id}`}>
            <Mic className="size-5" strokeWidth={2.25} />
            Start {scene.title}
          </PillButton>
        ) : null}
        <PillButton href="/" variant="paper" className="mt-2 border border-ink/15">
          Back to Today
        </PillButton>
      </div>
    </div>
  );
}

function Shell({ title, body, requestId, children }: { title: string; body: string; requestId?: string | null; children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
      <h1 className="text-3xl font-extrabold tracking-tight">{title}</h1>
      <p className="mt-2 text-ink-2">{body}</p>
      {requestId ? <p className="mt-1 text-xs text-ink-2">ref {requestId}</p> : null}
      <div className="mt-6">{children}</div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-1 flex-col bg-scene px-5 pt-12" data-scene="review">
      <div className="h-3 w-24 rounded-full bg-ink/15" />
      <div className="mt-8 h-3 w-16 rounded-full bg-ink/15" />
      <div className="mt-2 h-6 w-3/4 rounded-md bg-ink/15" />
      <div className="mt-6 h-3 w-12 rounded-full bg-ink/15" />
      <div className="mt-2 h-8 w-5/6 rounded-md bg-ink/15" />
      <div className="flex-1" />
      <div className="mx-auto mb-14 size-[84px] rounded-pill bg-ink/15" />
    </div>
  );
}
