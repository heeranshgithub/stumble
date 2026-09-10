"use client";

import { useState } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import { SampleLink } from "@/components/stumble/SampleLink";
import { getErrorMessage } from "@/lib/errors";
import { useGetDeckQuery } from "@/store/endpoints/progress";
import type { DeckCardDto } from "@/types/api";

const stateCls = { on: "lyr-on", off: "lyr-off-sm", miss: "lyr-miss-sm" } as const;

export function DeckScreen() {
  const { data, error, isLoading, refetch } = useGetDeckQuery();
  const [open, setOpen] = useState<string | null>(null);

  if (isLoading) return <Skeleton />;
  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
        <h1 className="text-3xl font-extrabold tracking-tight">Couldn&apos;t load the deck.</h1>
        <p className="mt-2 text-ink-2">{e.message}</p>
        <PillButton className="mt-6" onClick={() => void refetch()}>
          Try again
        </PillButton>
      </div>
    );
  }

  const selected = data.cards.find((c) => c.id === open) ?? null;

  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">
          {data.caught} caught · {data.mastered} mastered · {data.due} due
        </p>
        <h1 className="mt-1 text-[30px] font-extrabold leading-none tracking-[-0.03em]">Your deck</h1>
        <p className="mt-2 text-xs font-bold text-ink-2">
          Filled words are yours. Faded ones are on their way. Pink ones are due.
        </p>
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
          <p className="text-[19px] font-extrabold leading-[1.5] tracking-[-0.01em]">
            {data.cards.map((c, i) => (
              <span key={c.id}>
                <button
                  type="button"
                  onClick={() => setOpen((cur) => (cur === c.id ? null : c.id))}
                  className={`rounded-md px-0.5 ${stateCls[c.state]} ${open === c.id ? "bg-ink/10" : ""}`}
                >
                  {c.target}
                </button>
                {i < data.cards.length - 1 ? " " : ""}
              </span>
            ))}
          </p>
        )}
        {selected ? <CardDetail card={selected} /> : null}
      </Blob>
    </div>
  );
}

function CardDetail({ card }: { card: DeckCardDto }) {
  const due = new Date(card.due);
  const days = Math.round((due.getTime() - Date.now()) / 86_400_000);
  return (
    <div className="mt-4 rounded-2xl bg-ink px-4 py-3 text-paper">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[20px] font-extrabold leading-none tracking-tight">{card.target}</p>
        <Chip tone={card.state === "miss" ? "stumble" : "muted"} className={card.state === "miss" ? "" : "bg-paper/15 text-paper"}>
          {card.state === "on" ? "mastered" : card.state === "miss" ? "due now" : days <= 0 ? "due today" : `due in ${days}d`}
        </Chip>
      </div>
      {card.context ? <p className="mt-2 text-sm text-paper-2">&ldquo;{card.context}&rdquo;</p> : null}
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
