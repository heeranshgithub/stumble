"use client";

import { Mic } from "lucide-react";
import { useRouter } from "next/navigation";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { LyricLine, type LyricWord } from "@/components/stumble/LyricLine";
import { PillButton } from "@/components/stumble/PillButton";
import { useMarkOnboardedMutation } from "@/store/endpoints/today";

/**
 * The headline's claim, shown instead of asserted: one café line, the word that got reached for in
 * English, and the card it becomes. Built from the same components the scene and deck use, so the
 * pitch doubles as an honest preview of the real UI.
 */
const CAUGHT_LINE: LyricWord[] = [
  { text: "Je", state: "on" },
  { text: "voudrais", state: "on" },
  { text: "un", state: "on" },
  { text: "café", state: "on" },
  { text: "avec", state: "on" },
  { text: "du", state: "on" },
  { text: "sugar.", state: "miss" },
];

function LoopPreview() {
  return (
  <div className="w-full">
    <p className="text-[11px] font-extrabold text-ink-2">Léa · barista</p>
    <p className="mt-1 text-[15px] font-bold text-ink-2">Qu&apos;est-ce que je vous sers ?</p>
    <p className="mt-5 text-[11px] font-extrabold text-ink-2">You</p>
    <LyricLine className="mt-1" words={CAUGHT_LINE} animate />
    <div className="mt-5 fade-in" style={{ animationDelay: "560ms" }}>
      <Chip tone="stumble">caught · sugar → sucre</Chip>
      <p className="mt-2 text-[11px] font-extrabold text-ink-2">Due tomorrow, in your own sentence.</p>
    </div>
  </div>
  );
}

/** The first screen on a new device: the claim, shown as one caught sentence, and the café. */
export function OnboardingScreen() {
  const router = useRouter();
  const [markOnboarded, { isLoading }] = useMarkOnboardedMutation();
  const begin = () => {
    // Marked before leaving, or the Today tab would send you back here until a scene was played.
    void markOnboarded()
      .unwrap()
      .finally(() => router.replace("/scenes"));
  };
  return (
    <div className="flex flex-1 flex-col" data-scene="cafe">
      <Blob color="scene" className="flex flex-1 flex-col pt-14 pb-6">
        <div className="flex min-h-0 flex-1 items-center overflow-hidden pb-8">
          <LoopPreview />
        </div>
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
        {/* One button, to the scene list. There is no placement step: the café catches the first
            stumbles in a real sentence, with Léa scaffolding, which "say anything you know" never
            did. */}
        <PillButton onClick={begin} disabled={isLoading}>
          <Mic className="size-5" strokeWidth={2.25} />
          Pick a scene
        </PillButton>
      </div>
    </div>
  );
}
