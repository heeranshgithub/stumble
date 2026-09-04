"use client";

import { Lock, Mic } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { LyricLine } from "@/components/stumble/LyricLine";
import { PillButton } from "@/components/stumble/PillButton";
import { getErrorMessage } from "@/lib/errors";
import { useGetTodayQuery } from "@/store/endpoints/today";

const weekday = new Intl.DateTimeFormat("en", { weekday: "long" });

export function TodayScreen() {
  const { data, error, isLoading, refetch } = useGetTodayQuery();
  const router = useRouter();
  const needsOnboarding = !!data && !data.onboarded;

  // First open on this device: the twenty-second placement comes before anything else.
  useEffect(() => {
    if (needsOnboarding) router.replace("/onboarding");
  }, [needsOnboarding, router]);

  if (isLoading || needsOnboarding) return <TodaySkeleton />;

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
  const hasReview = data.reviewDue > 0;
  const sceneColor = scene?.color ?? "cafe";
  const sceneHref = `/scene/${scene?.id ?? "cafe"}`;
  const reviewLabel = data.reviewDue === 1 ? "1 stumble." : `${data.reviewDue} stumbles.`;
  const uses = scene?.usesDueCards ?? [];

  return (
    <div className="flex flex-1 flex-col" data-scene={hasReview ? "review" : sceneColor}>
      <Blob color="scene" className="flex flex-[1.3] flex-col justify-end pt-14">
        <p className="text-xs font-bold text-ink-2">
          {weekday.format(new Date())} · Day {data.dayNumber}
        </p>
        <h1 className="mt-2 text-[34px] font-extrabold leading-[1] tracking-[-0.03em]">
          {hasReview ? (
            <>
              Review
              <br />
              {reviewLabel}
            </>
          ) : scene ? (
            <>
              Nothing to review.
              <br />
              Go speak.
            </>
          ) : (
            <>
              Every scene
              <br />
              cleared.
            </>
          )}
        </h1>
        <p className="mt-2 text-xs font-bold text-ink-2">
          {hasReview
            ? `~${Math.max(1, Math.round(data.reviewDue * 13))} seconds · then ${scene?.title ?? "the next scene"} unlocks`
            : scene
              ? data.deck.caught === 0
                ? "Your first stumbles will come from the scene."
                : "Nothing due. The next scene is open."
              : "Replay any scene from the Scenes tab."}
        </p>
        <PillButton href={hasReview ? "/review" : sceneHref} className="mt-4">
          <Mic className="size-5" strokeWidth={2.25} />
          {hasReview ? "Start review" : `Start ${scene?.title ?? "a scene"}`}
        </PillButton>
      </Blob>

      {scene ? (
        <NextSceneBlob
          title={scene.title}
          order={scene.order}
          goal={scene.goal}
          color={scene.color}
          uses={uses}
          unlocked={data.sceneUnlocked}
          href={sceneHref}
          label={hasReview ? "Then" : "Next"}
        />
      ) : null}

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
          <>
            <LyricLine
              size="sm"
              className="mt-2"
              words={uses.map((t) => ({ text: t, state: "miss" as const }))}
            />
            <Link href="/deck" className="mt-2 inline-block text-xs font-extrabold text-ink/60 underline-offset-2 hover:underline">
              open the deck
            </Link>
          </>
        )}
      </Blob>
    </div>
  );
}

function NextSceneBlob({
  title,
  order,
  goal,
  color,
  uses,
  unlocked,
  href,
  label,
}: {
  title: string;
  order: number;
  goal: string;
  color: "cafe" | "pharmacie" | "apartment" | "bill" | "doctor" | "interview";
  uses: string[];
  unlocked: boolean;
  href: string;
  label: string;
}) {
  const body = (
    <Blob color={color} className={`flex flex-[0.9] flex-col justify-center ${unlocked ? "" : "opacity-90"}`}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-ink-2">
          {label} · Scene {order}
        </p>
        {unlocked ? null : (
          <Chip tone="ink">
            <Lock className="size-3" strokeWidth={2.5} />
            after review
          </Chip>
        )}
      </div>
      <p className="mt-1 text-xl font-bold tracking-[-0.01em]">{title}</p>
      <p className="text-xs font-bold text-ink-2">
        {uses.length > 0 ? `Uses ${uses.length} of today's cards: ${uses.slice(0, 3).join(" · ")}` : goal}
      </p>
    </Blob>
  );
  return unlocked ? (
    <Link href={href} className="flex flex-[0.9] flex-col">
      {body}
    </Link>
  ) : (
    body
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
