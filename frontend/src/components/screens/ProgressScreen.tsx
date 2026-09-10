"use client";

import { Check, FileText } from "lucide-react";
import Link from "next/link";

import { Blob } from "@/components/stumble/Blob";
import { PillButton } from "@/components/stumble/PillButton";
import { SampleLink } from "@/components/stumble/SampleLink";
import { SeriesChart } from "@/components/stumble/SeriesChart";
import { getErrorMessage } from "@/lib/errors";
import { useGetProgressQuery } from "@/store/endpoints/progress";

export function ProgressScreen() {
  const { data, error, isLoading, refetch } = useGetProgressQuery();

  if (isLoading) return <Skeleton />;
  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
        <h1 className="text-3xl font-extrabold tracking-tight">Couldn&apos;t load progress.</h1>
        <p className="mt-2 text-ink-2">{e.message}</p>
        <PillButton className="mt-6" onClick={() => void refetch()}>
          Try again
        </PillButton>
      </div>
    );
  }

  const headline =
    data.caught === 0
      ? "Nothing caught yet."
      : data.due === 0
        ? "Deck's clear."
        : data.mastered > data.due
          ? "Your deck is shrinking."
          : "Your deck is filling. Good.";

  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">
          French · {data.sessions === 1 ? "1 scene" : `${data.sessions} scenes`} · {data.minutesSpoken} min spoken
        </p>
        <h1 className="mt-1 text-[30px] font-extrabold leading-none tracking-[-0.03em]">{headline}</h1>
        <div className="mt-4 grid grid-cols-3 gap-2">
          <Stat n={data.caught} label="caught" />
          <Stat n={data.mastered} label="mastered" tone="mint" />
          <Stat n={data.due} label="still due" tone="stumble" />
        </div>
        {data.caught === 0 ? <SampleLink className="mt-3" /> : null}
      </Blob>

      <Blob color="paper">
        <p className="text-xs font-bold text-ink/65">Caught vs. mastered vs. still due</p>
        <div className="mt-2 text-ink">
          <SeriesChart points={data.series} />
        </div>
      </Blob>

      {data.underPressure.length > 0 ? (
        <Blob color="paper" className="pt-0">
          <p className="text-xs font-bold text-ink/65">Words you found under pressure</p>
          <ul className="mt-1 divide-y divide-ink/10">
            {data.underPressure.map((u) => (
              <li key={u.target} className="flex items-center gap-3 py-2.5">
                <span className="grid size-8 flex-none place-items-center rounded-xl bg-pharmacie text-ink">
                  <Check className="size-4" strokeWidth={3} />
                </span>
                <div className="min-w-0">
                  <p className="text-[15px] font-extrabold leading-tight">{u.target}</p>
                  <p className="truncate text-xs font-bold text-ink/65">
                    {u.lapses > 0 ? `stumbled ×${u.lapses + 1}` : "stumbled once"} → produced clean
                    {u.producedIn.length ? ` in ${u.producedIn.join(", ")}` : ""}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </Blob>
      ) : null}

      <div className="mt-auto px-5 pb-8 pt-2">
        <Link href="/tutor-brief" className="flex items-center justify-between rounded-2xl bg-ink px-4 py-3 text-paper">
          <div>
            <p className="text-[10px] font-extrabold uppercase tracking-[0.12em] text-paper-2">For your tutor</p>
            <p className="text-[15px] font-extrabold">This week&apos;s brief</p>
          </div>
          <FileText className="size-5" strokeWidth={2.25} />
        </Link>
      </div>
    </div>
  );
}

function Stat({ n, label, tone = "ink" }: { n: number; label: string; tone?: "ink" | "mint" | "stumble" }) {
  const color = tone === "mint" ? "text-[#1f9d55]" : tone === "stumble" ? "text-stumble" : "text-ink";
  return (
    <div className="rounded-2xl bg-paper px-3 py-2.5 text-center">
      <p className={`text-[24px] font-extrabold leading-none tracking-tight ${color}`}>{n}</p>
      <p className="mt-1 text-[11px] font-bold text-ink/65">{label}</p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-32 rounded-full bg-ink/15" />
        <div className="mt-2 h-8 w-3/4 rounded-md bg-ink/15" />
        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="h-16 rounded-2xl bg-ink/10" />
          <div className="h-16 rounded-2xl bg-ink/10" />
          <div className="h-16 rounded-2xl bg-ink/10" />
        </div>
      </div>
      <div className="px-5 pt-5">
        <div className="h-36 rounded-xl bg-ink/8" />
      </div>
    </div>
  );
}
