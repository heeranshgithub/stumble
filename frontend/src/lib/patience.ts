"use client";

import { useSyncExternalStore } from "react";

import type { Patience } from "@/types/api";

const KEY = "stumble.patience";
const listeners = new Set<() => void>();

export function getPatience(): Patience {
  if (typeof window === "undefined") return "normal";
  try {
    const v = window.localStorage.getItem(KEY);
    return v === "relaxed" || v === "real" ? v : "normal";
  } catch {
    return "normal";
  }
}

export function setPatience(p: Patience) {
  try {
    window.localStorage.setItem(KEY, p);
  } catch {
    // storage blocked: the choice lives for this page only
  }
  listeners.forEach((l) => l());
}

function subscribe(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}

/** The learner's chosen character patience. Per device, like everything else here. */
export function usePatience(): Patience {
  return useSyncExternalStore(subscribe, getPatience, () => "normal");
}
