"use client";

import { Mic } from "lucide-react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { GradeRow } from "@/components/stumble/GradeRow";
import { LyricLine } from "@/components/stumble/LyricLine";
import { MicButton } from "@/components/stumble/MicButton";
import { PillButton } from "@/components/stumble/PillButton";

const colors = ["cafe", "pharmacie", "apartment", "bill", "doctor", "interview", "review"] as const;

const line = [
  { text: "Je voudrais un", state: "on" },
  { text: "coffee", state: "miss" },
  { text: "au lait,", state: "on" },
  { text: "s'il vous plaît.", state: "off" },
] as const;

const sheet = [
  { text: "café", state: "on" },
  { text: "au lait", state: "on" },
  { text: "combien", state: "miss" },
  { text: "merci", state: "on" },
  { text: "loyer", state: "off" },
  { text: "sirop", state: "on" },
  { text: "appart", state: "off" },
  { text: "ordonnance", state: "on" },
] as const;

/**
 * Every component on every scene color. The audit surface for the design system:
 * if anything here is grey, generic, or unreadable, it's a regression.
 */
export function Kitchen() {
  return (
    <div className="flex flex-col gap-0 pb-10">
      <Blob color="ink" className="pt-14">
        <h1 className="text-2xl font-extrabold tracking-tight">Kitchen</h1>
        <p className="mt-1 text-sm text-paper-2">Seven colors, every component. Nothing grey.</p>
      </Blob>

      {colors.map((c) => (
        <section key={c} data-scene={c}>
          <Blob color="scene" className="pt-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-extrabold">{c}</h2>
              <Chip tone="ink">
                Léa · 2:14
              </Chip>
            </div>
            <p className="mt-1 text-xs font-bold text-ink-2">secondary text is tinted ink, not grey</p>

            <LyricLine className="mt-5" words={[...line]} />
            <div className="mt-3 flex flex-wrap gap-2">
              <Chip tone="ink">caught · coffee → café</Chip>
              <Chip tone="stumble">you froze here · 4s</Chip>
              <Chip>~90 seconds</Chip>
            </div>

            <PillButton className="mt-5">
              <Mic className="size-5" strokeWidth={2.25} />
              Start review
            </PillButton>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <PillButton variant="paper">Type instead</PillButton>
              <PillButton variant="stumble">Hint</PillButton>
            </div>

            <MicButton className="mt-6" state={c === "review" ? "holding" : "idle"} />
          </Blob>

          <Blob color="paper">
            <p className="text-xs font-bold text-ink/65">deck sheet on paper</p>
            <LyricLine size="sm" className="mt-1" words={[...sheet]} />
          </Blob>

          <Blob color="ink">
            <p className="text-xs font-bold text-paper-2">answer sheet</p>
            <p className="text-[34px] font-extrabold leading-none tracking-tight">Combien</p>
            <p className="mt-1 text-sm text-paper-2">C&apos;est combien ? — how much is it</p>
            <div className="mt-4">
              <GradeRow
                intervals={{ again: "10m", hard: "1d", good: "3d", easy: "7d" }}
                onGrade={() => undefined}
              />
            </div>
          </Blob>
        </section>
      ))}
    </div>
  );
}
