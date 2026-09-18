"use client";

import { useSyncExternalStore } from "react";

import { freshDeviceId, peekDeviceId, previousDeviceId, SAMPLE_DEVICE, switchDevice } from "@/lib/device";

const noop = () => () => undefined;
const server = () => "";

/**
 * On while the shared sample profile is open, and never dismissible: like a "test mode" bar, its
 * job is that you can't forget whose deck this is, and the way back has to stay reachable. A
 * direct link into the sample has no previous profile, so the button then starts a fresh one.
 */
export function SampleBanner() {
  const device = useSyncExternalStore(noop, peekDeviceId, server);
  const previous = useSyncExternalStore(noop, previousDeviceId, server);

  if (device !== SAMPLE_DEVICE) return null;

  return (
    <div className="flex shrink-0 items-center gap-3 bg-ink px-5 py-2 text-paper">
      <p className="flex-1 text-[11.5px] font-extrabold leading-tight">Sample account, a week of history. Not yours.</p>
      <button
        type="button"
        onClick={() => switchDevice(previous || freshDeviceId())}
        className="shrink-0 rounded-pill bg-paper/15 px-2.5 py-1 text-[11px] font-extrabold"
      >
        {previous ? "Back to mine" : "Start mine"}
      </button>
    </div>
  );
}
