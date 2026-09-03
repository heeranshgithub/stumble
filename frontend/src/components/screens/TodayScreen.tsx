"use client";

import { Mic } from "lucide-react";

import { Blob } from "@/components/stumble/Blob";
import { LyricLine } from "@/components/stumble/LyricLine";
import { PillButton } from "@/components/stumble/PillButton";
import { getErrorMessage } from "@/lib/errors";
import { useGetTodayQuery } from "@/store/endpoints/today";

const weekday = new Intl.DateTimeFormat("en", { weekday: "long" });

export function TodayScreen() {
  const { data, error, isLoading, refetch } = useGetTodayQuery();

  if (isLoading) return <TodaySkeleton />;

  if (error || !data) {
    const e = getErrorMessage(error);
    return (
      <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
        <h1 className="text-3xl font-extrabold tracking-tight">Couldn&apos;t load today.</h1>
        <p className="mt-2 text-ink-2">{e.message}</p>
        {e.requestId ? <p className="mt-1 text-xs text-ink-2">ref {e.requestId}</p> : null}
        <PillButton className="mt-6" onClick={() => void refetch()}>
          Try again
        </PillButton>
      </div>
    );
  }

  const scene = data.nextScene;
  const sceneColor = scene?.color ?? "cafe";
  const reviewLabel = data.reviewDue === 1 ? "1 stumble." : `${data.reviewDue} stumbles.`;

  return (
    <div className="flex flex-1 flex-col" data-scene={sceneColor}>
      <Blob color="scene" className="flex flex-[1.3] flex-col justify-end pt-14">
        <p className="text-xs font-bold text-ink-2">
          {weekday.format(new Date())} · Day {data.dayNumber}
        </p>
        <h1 className="mt-2 text-[34px] font-extrabold leading-[1] tracking-[-0.03em]">
          {data.reviewDue > 0 ? (
            <>
              Review
              <br />
              {reviewLabel}
            </>
          ) : (
            <>
              Nothing to review.
              <br />
              Go speak.
            </>
          )}
        </h1>
        <p className="mt-2 text-xs font-bold text-ink-2">
          {data.reviewDue > 0 ? "~90 seconds" : "Your first stumbles will come from the scene."}
        </p>
        <PillButton href={data.reviewDue > 0 ? "/review" : `/scene/${scene?.id ?? "cafe"}`} className="mt-4">
          <Mic className="size-5" strokeWidth={2.25} />
          {data.reviewDue > 0 ? "Start review" : `Start ${scene?.title ?? "the first scene"}`}
        </PillButton>
      </Blob>

      <Blob color="apartment" className="flex flex-[0.9] flex-col justify-center">
        <p className="text-xs font-bold text-ink-2">{data.reviewDue > 0 ? "Then" : "Next"} · Scene {scene?.order ?? 1}</p>
        <p className="mt-1 text-xl font-bold tracking-[-0.01em]">{scene?.title ?? "Café"}</p>
        <p className="text-xs font-bold text-ink-2">
          {scene && scene.usesDueCards.length > 0
            ? `Uses ${scene.usesDueCards.length} of today's cards`
            : (scene?.goal ?? "")}
        </p>
      </Blob>

      <Blob color="paper" className="flex-[0.8]">
        <div className="flex items-baseline justify-between text-xs font-bold text-ink/60">
          <span>Your deck</span>
          <span>
            {data.deck.caught} caught · {data.deck.mastered} mastered
          </span>
        </div>
        {data.deck.caught === 0 ? (
          <p className="mt-2 text-[18px] font-extrabold leading-snug lyr-off-sm">
            Every word you reach for and miss lands here.
          </p>
        ) : (
          <LyricLine size="sm" className="mt-2" words={[]} />
        )}
      </Blob>
    </div>
  );
}

function TodaySkeleton() {
  return (
    <div className="flex flex-1 flex-col" data-scene="cafe">
      <div className="flex-[1.3] bg-scene px-5 pt-14">
        <div className="h-3 w-24 rounded-full bg-ink/15" />
        <div className="mt-4 h-9 w-48 rounded-md bg-ink/15" />
        <div className="mt-2 h-9 w-40 rounded-md bg-ink/15" />
        <div className="mt-6 h-12 w-full rounded-pill bg-ink/15" />
      </div>
      <div className="flex-[0.9] bg-ink/5" />
      <div className="flex-[0.8]" />
    </div>
  );
}
