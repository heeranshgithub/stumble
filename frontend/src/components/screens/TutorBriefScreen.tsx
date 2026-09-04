"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Blob } from "@/components/stumble/Blob";
import { PillButton } from "@/components/stumble/PillButton";
import { getErrorMessage } from "@/lib/errors";
import { useGetTutorBriefQuery } from "@/store/endpoints/progress";

export function TutorBriefScreen() {
  const { data, error, isLoading, refetch } = useGetTutorBriefQuery();
  const [copied, setCopied] = useState(false);

  if (isLoading) return <Skeleton />;
  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
        <h1 className="text-3xl font-extrabold tracking-tight">Couldn&apos;t write the brief.</h1>
        <p className="mt-2 text-ink-2">{e.message}</p>
        <PillButton className="mt-6" onClick={() => void refetch()}>
          Try again
        </PillButton>
      </div>
    );
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(data.asText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard blocked: the text is on screen
    }
  };

  if (data.cardsAnalysed === 0) {
    return (
      <div className="flex flex-1 flex-col" data-scene="review">
        <Blob color="scene" className="flex flex-1 flex-col justify-end pt-14 pb-6">
          <p className="text-xs font-bold text-ink-2">For your tutor · {data.weekLabel}</p>
          <h1 className="mt-2 text-[30px] font-extrabold leading-[1.05] tracking-[-0.03em]">
            Nothing to report yet.
          </h1>
          <p className="mt-2 text-xs font-bold text-ink-2">Play a scene or two and the patterns will show up here.</p>
        </Blob>
        <div className="px-5 pb-8 pt-4">
          <PillButton href="/">Back to Today</PillButton>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">
          Week {data.weekLabel.split("-W")[1]} · from {data.scenesPlayed} {data.scenesPlayed === 1 ? "scene" : "scenes"} ·{" "}
          {data.cardsAnalysed} stumbles
        </p>
        <h1 className="mt-1 text-[30px] font-extrabold leading-none tracking-[-0.03em]">Brief for your tutor</h1>
      </Blob>

      <div className="flex flex-1 flex-col gap-5 px-5 pt-5 pb-4">
        <section>
          <p className="text-xs font-bold text-ink/65">Patterns</p>
          <ul className="mt-1 divide-y divide-ink/10">
            {data.patterns.map((p) => (
              <li key={p.title} className="flex gap-3 py-3">
                <span className="grid size-9 flex-none place-items-center rounded-xl bg-stumble/15 text-[12px] font-extrabold text-stumble">
                  ×{p.count}
                </span>
                <div>
                  <p className="text-[15px] font-extrabold leading-tight">{p.title}</p>
                  <p className="mt-0.5 text-xs font-bold text-ink/65">{p.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {data.strengths.length > 0 ? (
          <section className="rounded-2xl bg-pharmacie/60 px-4 py-3">
            <p className="text-xs font-bold text-ink/65">Strong</p>
            <p className="mt-1 text-[14px] font-extrabold leading-snug">{data.strengths.join(" · ")}</p>
          </section>
        ) : null}

        {data.suggestedSession.length > 0 ? (
          <section className="rounded-2xl bg-ink px-4 py-3 text-paper">
            <p className="text-[10px] font-extrabold uppercase tracking-[0.12em] text-paper-2">Suggested 30-minute session</p>
            <ol className="mt-1 space-y-1.5">
              {data.suggestedSession.map((s, i) => (
                <li key={i} className="flex gap-2 text-[14px] font-bold leading-snug">
                  <span className="text-paper-2">{i + 1}.</span>
                  <span>{s}</span>
                </li>
              ))}
            </ol>
          </section>
        ) : null}
      </div>

      <div className="px-5 pb-8">
        <PillButton onClick={() => void copy()}>
          {copied ? <Check className="size-5" strokeWidth={2.5} /> : <Copy className="size-5" strokeWidth={2.25} />}
          {copied ? "Copied" : "Copy as text for my tutor"}
        </PillButton>
        <p className="mt-2 text-center text-[11px] font-bold text-ink/65">Paste it into your next Varsity Tutors session.</p>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-40 rounded-full bg-ink/15" />
        <div className="mt-2 h-8 w-3/4 rounded-md bg-ink/15" />
      </div>
      <div className="space-y-3 px-5 pt-5">
        <div className="h-12 rounded-xl bg-ink/8" />
        <div className="h-12 rounded-xl bg-ink/8" />
        <div className="h-24 rounded-2xl bg-ink/8" />
      </div>
    </div>
  );
}
