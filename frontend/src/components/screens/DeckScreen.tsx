"use client";

import { Mic } from "lucide-react";
import { useState } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import { SampleLink } from "@/components/stumble/SampleLink";
import { getErrorMessage } from "@/lib/errors";
import { whenDue } from "@/lib/when";
import { useGetDeckQuery } from "@/store/endpoints/progress";
import type { DeckCardDto, WordState } from "@/types/api";

// The deck is a list in three groups. A sheet of all the words at once read as one long paragraph
// with nothing to do; a row per card says what each word is and when it's back.
const groups: { state: WordState; title: string }[] = [
  { state: "miss", title: "Due now" },
  { state: "off", title: "Learning" },
  { state: "on", title: "Mastered" },
];

export function DeckScreen() {
  const { data, error, isLoading, refetch } = useGetDeckQuery();
  const [open, setOpen] = useState<string | null>(null);

  if (isLoading) return <Skeleton />;
  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <div
        className="flex flex-1 flex-col justify-end px-5 pb-8"
        data-scene="review"
      >
        <h1 className="text-3xl font-extrabold tracking-tight">
          Couldn&apos;t load the deck.
        </h1>
        <p className="mt-2 text-ink-2">{e.message}</p>
        <PillButton className="mt-6" onClick={() => void refetch()}>
          Try again
        </PillButton>
      </div>
    );
  }

  const toggle = (id: string) => setOpen((cur) => (cur === id ? null : id));

  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">
          {data.caught} caught · {data.mastered} mastered · {data.due} due
        </p>
        <h1 className="mt-1 text-[30px] font-extrabold leading-none tracking-[-0.03em]">
          Your deck
        </h1>
        <NextStep cards={data.cards} due={data.due} />
      </Blob>

      <Blob color="paper" className="flex-1">
        {data.cards.length === 0 ? (
          <>
            <p className="text-[18px] font-extrabold leading-snug lyr-off-sm">
              Every word you reach for and miss lands here.
            </p>
            <SampleLink className="mt-3" />
          </>
        ) : (
          groups
            .map((g) => ({
              ...g,
              cards: data.cards.filter((c) => c.state === g.state),
            }))
            .filter((g) => g.cards.length > 0)
            .map((g) => (
              <section key={g.state} className="mt-2 first:mt-0">
                <p
                  className={`text-xs font-bold ${g.state === "miss" ? "text-stumble" : "text-ink/65"}`}
                >
                  {g.title} · {g.cards.length}
                </p>
                <ul className="-mx-5 mt-1 divide-y divide-ink/10">
                  {g.cards.map((c) => (
                    <li key={c.id}>
                      <button
                        type="button"
                        onClick={() => toggle(c.id)}
                        aria-expanded={open === c.id}
                        className="flex w-full items-center gap-3 px-5 py-3 text-left"
                      >
                        <div className="min-w-0 flex-1">
                          <p
                            className={`text-[17px] font-extrabold leading-tight ${c.state === "miss" ? "text-stumble" : c.state === "on" ? "text-ink/45" : "text-ink"}`}
                          >
                            {c.target}
                          </p>
                          <p className="truncate text-xs font-bold text-ink/65">
                            {c.context ? `"${c.context}"` : c.sceneTitle}
                          </p>
                        </div>
                        <DueChip card={c} />
                      </button>
                      {open === c.id ? (
                        <div className="px-5 pb-3">
                          <CardDetail card={c} />
                        </div>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </section>
            ))
        )}
      </Blob>
    </div>
  );
}

/** The one line that changes with the deck: what happens to these words next, and the way there. */
function NextStep({ cards, due }: { cards: DeckCardDto[]; due: number }) {
  if (cards.length === 0) {
    return (
      <p className="mt-2 text-xs font-bold text-ink-2">
        Play a scene. Whatever you reach for and miss lands here.
      </p>
    );
  }
  if (due > 0) {
    return (
      <>
        <p className="mt-2 text-xs font-bold text-ink-2">
          {due === 1 ? "1 word is due." : `${due} words are due.`} Say each one
          in its own sentence; the scheduler does the rest.
        </p>
        <PillButton href="/review" className="mt-3">
          <Mic className="size-5" strokeWidth={2.25} />
          Start review
        </PillButton>
      </>
    );
  }
  const next = cards
    .filter((c) => c.state !== "on")
    .map((c) => new Date(c.due).getTime())
    .sort((a, b) => a - b)[0];
  const learning = cards.filter((c) => c.state === "off").length;
  return (
    <p className="mt-2 text-xs font-bold text-ink-2">
      {learning === 0
        ? "Every word here is mastered. Play a scene to catch new ones."
        : `Nothing due yet. ${learning === 1 ? "1 word comes" : `${learning} words come`} back ${next ? whenDue(next) : "soon"}.`}
    </p>
  );
}

function DueChip({ card }: { card: DeckCardDto }) {
  if (card.state === "on") return <Chip>mastered</Chip>;
  if (card.state === "miss") return <Chip tone="stumble">due now</Chip>;
  return <Chip>{whenDue(card.due)}</Chip>;
}

function CardDetail({ card }: { card: DeckCardDto }) {
  return (
    <div className="mt-4 rounded-2xl bg-ink px-4 py-3 text-paper">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[20px] font-extrabold leading-none tracking-tight">
          {card.target}
        </p>
        <Chip
          tone={card.state === "miss" ? "stumble" : "muted"}
          className={card.state === "miss" ? "" : "bg-paper/15 text-paper"}
        >
          {card.state === "on"
            ? "mastered"
            : card.state === "miss"
              ? "due now"
              : whenDue(card.due)}
        </Chip>
      </div>
      {card.context ? (
        <p className="mt-2 text-sm text-paper-2">
          &ldquo;{card.context}&rdquo;
        </p>
      ) : null}
      <p className="mt-1 text-xs font-bold text-paper-2">
        {card.sceneTitle} · {card.type.replace("_", "-")}
        {card.lapses > 0 ? ` · stumbled ×${card.lapses + 1}` : ""}
        {card.produced > 0 ? ` · produced clean ×${card.produced}` : ""}
      </p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-40 rounded-full bg-ink/15" />
        <div className="mt-2 h-8 w-40 rounded-md bg-ink/15" />
      </div>
      <div className="space-y-3 px-5 pt-5">
        <div className="h-6 w-full rounded-md bg-ink/8" />
        <div className="h-6 w-5/6 rounded-md bg-ink/8" />
        <div className="h-6 w-2/3 rounded-md bg-ink/8" />
      </div>
    </div>
  );
}
