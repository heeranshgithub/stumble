"use client";

import type { SceneColor } from "@/types/api";

const KEY = "stumble.today.scene";
export type TodayColor = SceneColor | "review";

/**
 * Today's colour depends on data (lilac while a review is due, else the next scene's colour), so
 * its skeleton can't know it. The last colour it wore is close enough for the first frame, and
 * beats yellow for everyone whose next scene isn't the café.
 */
export function rememberTodayColor(c: TodayColor): void {
  try {
    window.localStorage.setItem(KEY, c);
  } catch {
    // storage blocked: the skeleton stays neutral
  }
}

export function lastTodayColor(): TodayColor | null {
  try {
    return (window.localStorage.getItem(KEY) as TodayColor | null) ?? null;
  } catch {
    return null;
  }
}
