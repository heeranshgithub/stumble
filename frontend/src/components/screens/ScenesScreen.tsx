"use client";

import { Check, Lock } from "lucide-react";
import Link from "next/link";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import { getErrorMessage } from "@/lib/errors";
import { setPatience, usePatience } from "@/lib/patience";
import { useGetScenesQuery } from "@/store/endpoints/scenes";
import type { Patience, SceneDto } from "@/types/api";

const patienceLabel: Record<Patience, { title: string; body: string }> = {
  relaxed: { title: "Relaxed", body: "Slow, simple, rephrases a lot." },
  normal: { title: "Normal", body: "Natural speed, short sentences." },
  real: { title: "Real-world", body: "Fast, slang, a little impatient." },
};

export function ScenesScreen() {
  const { data, error, isLoading, refetch } = useGetScenesQuery();
  const patience = usePatience();

  if (isLoading) return <Skeleton />;
  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
        <h1 className="text-3xl font-extrabold tracking-tight">Couldn&apos;t load scenes.</h1>
        <p className="mt-2 text-ink-2">{e.message}</p>
        <PillButton className="mt-6" onClick={() => void refetch()}>
          Try again
        </PillButton>
      </div>
    );
  }

  const next = data.find((s) => s.status === "next");

  return (
    <div className="flex flex-1 flex-col" data-scene={next?.color ?? "cafe"}>
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">Paris · Track 1</p>
        <h1 className="mt-1 text-[30px] font-extrabold leading-none tracking-[-0.03em]">Scenes</h1>
      </Blob>

      <ul className="flex flex-col">
        {data.map((s) => (
          <SceneRow key={s.id} scene={s} />
        ))}
      </ul>

      <div className="mt-auto px-5 pb-8 pt-6">
        <p className="text-xs font-bold text-ink/65">Character patience</p>
        <div className="mt-2 grid grid-cols-3 gap-2" role="radiogroup" aria-label="Character patience">
          {(Object.keys(patienceLabel) as Patience[]).map((p) => {
            const on = p === patience;
            return (
              <button
                key={p}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => setPatience(p)}
                className={`rounded-2xl px-3 py-2.5 text-left transition-colors ${on ? "bg-ink text-paper" : "bg-ink/8 text-ink"}`}
              >
                <span className="block text-[13px] font-extrabold">{patienceLabel[p].title}</span>
                <span className={`block text-[11px] font-bold ${on ? "text-paper-2" : "text-ink/65"}`}>{patienceLabel[p].body}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SceneRow({ scene }: { scene: SceneDto }) {
  const isNext = scene.status === "next";
  const cleared = scene.status === "cleared";
  const inner = (
    <div className={`flex items-center gap-3 px-5 py-4 ${isNext ? "" : "border-b border-ink/10"} ${scene.status === "locked" ? "opacity-45" : ""}`}>
      <span
        className={`grid size-10 flex-none place-items-center rounded-2xl text-[12px] font-extrabold ${
          cleared ? "bg-pharmacie text-ink" : isNext ? "bg-ink text-paper" : "bg-ink/10 text-ink"
        }`}
      >
        {cleared ? <Check className="size-4" strokeWidth={3} /> : scene.status === "locked" ? <Lock className="size-4" strokeWidth={2.5} /> : scene.order}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[16px] font-extrabold leading-tight">{scene.title}</p>
        <p className="truncate text-xs font-bold text-ink/65">
          {isNext && scene.usesDueCards.length > 0
            ? `Uses your due cards: ${scene.usesDueCards.join(" · ")}`
            : cleared
              ? "Cleared · replay anytime"
              : scene.goal}
        </p>
      </div>
      {isNext ? <Chip tone="stumble">next</Chip> : null}
    </div>
  );
  if (scene.status === "locked") return <li>{inner}</li>;
  return (
    <li>
      <Link href={`/scene/${scene.id}`} data-scene={scene.color} className={isNext ? "block bg-scene" : "block"}>
        {inner}
      </Link>
    </li>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-1 flex-col" data-scene="cafe">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-20 rounded-full bg-ink/15" />
        <div className="mt-2 h-8 w-32 rounded-md bg-ink/15" />
      </div>
      <div className="space-y-4 px-5 pt-4">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="h-10 rounded-2xl bg-ink/8" />
        ))}
      </div>
    </div>
  );
}
