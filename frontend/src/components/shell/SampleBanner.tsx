"use client";

import { X } from "lucide-react";
import { useState, useSyncExternalStore } from "react";

import { peekDeviceId, previousDeviceId, SAMPLE_DEVICE, switchDevice } from "@/lib/device";

const DISMISSED = "stumble.sample-banner.dismissed";
const noop = () => () => undefined;
const server = () => "";

/**
 * Only appears on the shared sample profile, so nobody who clicked "see a week in" is stranded
 * in someone else's deck. Dismissible, because it would otherwise sit in the demo recording.
 */
export function SampleBanner() {
  const device = useSyncExternalStore(noop, peekDeviceId, server);
  const previous = useSyncExternalStore(noop, previousDeviceId, server);
  const [hidden, setHidden] = useState(false);

  if (device !== SAMPLE_DEVICE || hidden) return null;
  if (typeof window !== "undefined") {
    try {
      if (window.localStorage.getItem(DISMISSED)) return null;
    } catch {
      // storage blocked: show it
    }
  }

  const dismiss = () => {
    try {
      window.localStorage.setItem(DISMISSED, "1");
    } catch {
      // storage blocked: hidden for this page only
    }
    setHidden(true);
  };

  return (
    <div className="flex shrink-0 items-center gap-3 bg-ink px-5 py-2 text-paper">
      <p className="flex-1 text-[11.5px] font-extrabold leading-tight">
        You&apos;re looking at a sample account with a week of history.
      </p>
      {previous ? (
        <button
          type="button"
          onClick={() => switchDevice(previous)}
          className="shrink-0 rounded-pill bg-paper/15 px-2.5 py-1 text-[11px] font-extrabold"
        >
          Back to mine
        </button>
      ) : null}
      <button type="button" aria-label="Dismiss" onClick={dismiss} className="shrink-0 text-paper/70">
        <X className="size-4" strokeWidth={2.5} />
      </button>
    </div>
  );
}
