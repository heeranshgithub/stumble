"use client";

import { Lock, Mic } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import { SampleLink } from "@/components/stumble/SampleLink";
import { getErrorMessage } from "@/lib/errors";
import { whenDue } from "@/lib/when";
import { lastTodayColor, rememberTodayColor, type TodayColor } from "@/lib/lastScene";
import { useGetTodayQuery } from "@/store/endpoints/today";
import type { TodayDeckDto } from "@/types/api";

const weekday = new Intl.DateTimeFormat("en", { weekday: "long" });

/** One line about the deck: what happens to it next. */
function deckLine(deck: TodayDeckDto): string {
  if (deck.due > 0) return deck.due === 1 ? "1 word is due now." : `${deck.due} words are due now.`;
  const learning = deck.caught - deck.mastered;
  if (learning === 0) return "All mastered. Play a scene to catch new ones.";
  if (!deck.nextDue) return `${learning} still learning.`;
  return `Nothing due. ${learning === 1 ? "1 word comes" : `${learning} words come`} back ${whenDue(deck.nextDue)}.`;
}

export function TodayScreen() {
  const { data, error, isLoading, refetch } = useGetTodayQuery();
  const router = useRouter();
  const needsOnboarding = !!data && !data.onboarded;

  // First open on this device: the intro, then the café. Starting it is what marks the profile onboarded.
  useEffect(() => {
    if (needsOnboarding) router.replace("/onboarding");
  }, [needsOnboarding, router]);

  // The colour this screen wears is the colour its skeleton will wear next time.
  const wornColor: TodayColor | null = data
    ? data.reviewDue > 0
      ? "review"
      : (data.nextScene?.color ?? "cafe")
    : null;
  useEffect(() => {
    if (wornColor) rememberTodayColor(wornColor);
  }, [wornColor]);

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

  const todayColor: TodayColor = hasReview ? "review" : sceneColor;

  return (
    <div className="flex flex-1 flex-col" data-scene={todayColor}>
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
            ? `Clear these and ${scene?.title ?? "the next scene"} unlocks.`
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
        <div className="flex items-baseline justify-between text-xs font-bold text-ink/65">
          <span>Your deck</span>
          <span>
            {data.deck.caught} caught · {data.deck.mastered} mastered
          </span>
        </div>
        {data.deck.caught === 0 ? (
          <>
            <p className="mt-2 text-[18px] font-extrabold leading-snug lyr-off-sm">
              Every word you reach for and miss lands here.
            </p>
            <SampleLink className="mt-2" />
          </>
        ) : (
          <>
            {/* The count, not the words: listing them here would hand over the answers to the
                review one tap above. The deck itself is a tap away. */}
            <p className="mt-2 text-[18px] font-extrabold leading-snug">{deckLine(data.deck)}</p>
            <Link href="/deck" className="mt-1 inline-block text-xs font-extrabold text-ink/65 underline-offset-2 hover:underline">
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
        {/* The fact, not the list: naming the words here would cue the review they're about to sit. */}
        {uses.length > 0 ? `Built around ${uses.length === 1 ? "1 word" : `${uses.length} words`} you're reviewing.` : goal}
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

const noSubscribe = () => () => undefined;
const serverColor = () => null;

function TodaySkeleton() {
  // Neutral on the server; the colour Today last wore on the client, from the first frame.
  const color = useSyncExternalStore(noSubscribe, lastTodayColor, serverColor);
  return (
    <div className="flex flex-1 flex-col" data-scene={color ?? undefined}>
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
