"use client";

import { Check, Copy, FastForward, Plus, RefreshCw } from "lucide-react";
import { useState, useSyncExternalStore } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import {
  freshDeviceId,
  peekDeviceId,
  previousDeviceId,
  SAMPLE_DEVICE,
  switchDevice,
} from "@/lib/device";
import { useDueNowMutation } from "@/store/endpoints/reviews";
import { useGetTodayQuery } from "@/store/endpoints/today";

const noop = () => () => undefined;
const server = () => "";

/**
 * Not in the tab bar: this is the utility screen for whoever is running the app. A device id is a
 * whole profile, so switching here is the same as switching accounts, minus the password.
 */
export function ProfileScreen() {
  const device = useSyncExternalStore(noop, peekDeviceId, server);
  const previous = useSyncExternalStore(noop, previousDeviceId, server);
  const { data } = useGetTodayQuery();
  const [draft, setDraft] = useState("");
  const [copied, setCopied] = useState(false);
  const [dueNow, dueNowState] = useDueNowMutation();

  // The id, not a link: a link is welded to one origin, and copying is for carrying the profile to
  // another one (today's tunnel, the deployed site) by pasting the id into "Switch to" there.
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(device);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard blocked: the id is on screen to copy by hand
    }
  };

  return (
    <div className="flex flex-1 flex-col" data-scene="review">
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">Profile</p>
        <h1 className="mt-1 text-[30px] font-extrabold leading-none tracking-[-0.03em]">
          Who is this deck for?
        </h1>
        <p className="mt-2 text-xs font-bold text-ink-2">
          There are no accounts. A device id is the identity, and each one is a separate profile:
          its own cards, scenes, reviews and progress.
        </p>
      </Blob>

      <Blob color="paper">
        <p className="text-xs font-bold text-ink/65">Current</p>
        <p className="mt-1 break-all text-[17px] font-extrabold leading-tight">{device || "…"}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {device === SAMPLE_DEVICE ? <Chip tone="stumble">sample account</Chip> : null}
          {data ? (
            <Chip>
              day {data.dayNumber} · {data.deck.caught} caught · {data.deck.mastered} mastered
            </Chip>
          ) : null}
        </div>
        <PillButton variant="paper" className="mt-3 border border-ink/15" onClick={() => void copy()}>
          {copied ? <Check className="size-5" strokeWidth={2.5} /> : <Copy className="size-5" strokeWidth={2.25} />}
          {copied ? "Copied" : "Copy this profile's id"}
        </PillButton>
      </Blob>

      <Blob color="paper" className="pt-0">
        <p className="text-xs font-bold text-ink/65">Switch to</p>
        <form
          className="mt-2 flex items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            switchDevice(draft);
          }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="take-1, heeransh-test, …"
            spellCheck={false}
            autoCapitalize="none"
            className="h-12 min-w-0 flex-1 rounded-pill bg-ink/8 px-4 text-[15px] font-bold text-ink outline-none placeholder:text-ink/60"
          />
          <button
            type="submit"
            disabled={!draft.trim()}
            className="h-12 shrink-0 rounded-pill bg-ink px-5 text-[14px] font-extrabold text-paper disabled:opacity-50"
          >
            Go
          </button>
        </form>
        <p className="mt-2 text-[11px] font-bold text-ink/65">
          Any name works. One that doesn&apos;t exist yet starts a clean profile at onboarding.
        </p>

        <div className="mt-4 grid gap-2">
          <PillButton variant="paper" className="border border-ink/15" onClick={() => switchDevice(freshDeviceId())}>
            <Plus className="size-5" strokeWidth={2.25} />
            Start a clean profile
          </PillButton>
          {previous ? (
            <PillButton variant="paper" className="border border-ink/15" onClick={() => switchDevice(previous)}>
              <RefreshCw className="size-5" strokeWidth={2.25} />
              Back to {previous.length > 18 ? `${previous.slice(0, 18)}…` : previous}
            </PillButton>
          ) : null}
          {device !== SAMPLE_DEVICE ? (
            <PillButton variant="paper" className="border border-ink/15" onClick={() => switchDevice(SAMPLE_DEVICE)}>
              Open the sample account
            </PillButton>
          ) : null}
        </div>
      </Blob>

      <Blob color="paper" className="pt-0">
        <p className="text-xs font-bold text-ink/65">For testing</p>
        <PillButton variant="paper" className="mt-2 border border-ink/15" onClick={() => void dueNow()} disabled={dueNowState.isLoading}>
          <FastForward className="size-5" strokeWidth={2.25} />
          {dueNowState.data ? `${dueNowState.data.cards} made due · again` : "Skip to tomorrow"}
        </PillButton>
        <p className="mt-2 text-[11px] font-bold text-ink/65">
          A new card is due tomorrow on purpose, and the next scene opens a sitting after the last, so
          neither can be tried the same day. This pulls every unmastered card forward to now and counts
          the last scene as a sitting ago; nothing else changes.
        </p>
      </Blob>

      <Blob color="paper" className="mt-auto pt-0">
        <p className="text-[11px] font-bold text-ink/65">
          Switching reloads the app. Nothing is deleted: the profile you leave is still there under its
          own id, and the link above brings you back to it.
        </p>
      </Blob>
    </div>
  );
}
