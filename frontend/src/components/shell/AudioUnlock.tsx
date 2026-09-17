"use client";

import { useEffect } from "react";

import { unlockAudio } from "@/hooks/useSpeaker";

/**
 * The first tap anywhere in the app unlocks the voice for the rest of the visit, so a scene opened
 * from the list speaks by itself instead of asking for a tap that does nothing else.
 */
export function AudioUnlock() {
  useEffect(() => {
    const onTap = () => unlockAudio();
    document.addEventListener("pointerdown", onTap, { capture: true, passive: true });
    return () => document.removeEventListener("pointerdown", onTap, { capture: true });
  }, []);
  return null;
}
