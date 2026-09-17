"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { env } from "@/lib/env";

// An empty WAV. Playing it inside the first tap unlocks audio on iOS for the rest of the session.
const SILENT_WAV =
  "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=";

export interface Played {
  /** performance.now() when sound actually started, or null if it never did. */
  startedAt: number | null;
  /** The browser refused to start sound without a user gesture. Not a failure: tap, then play again. */
  blocked?: boolean;
}

/**
 * One audio element for the whole app, not one per screen. iOS lets an element play without a
 * gesture only after a gesture has played it once, and Next navigates without reloading, so the
 * tap that opens a scene (a row on the Scenes list, a tab, any tap) can be that gesture: the
 * scene then speaks on its own. Only a hard load straight into a scene still needs "tap to hear".
 */
let shared: HTMLAudioElement | null = null;
let unlocked = false;

function getAudio(): HTMLAudioElement {
  if (shared) return shared;
  const a = new Audio();
  a.preload = "auto";
  a.setAttribute("playsinline", "true");
  shared = a;
  return a;
}

/** Call from inside a user gesture. Idempotent; never interrupts a line that is already playing. */
export function unlockAudio(): void {
  if (unlocked) return;
  const a = getAudio();
  if (!a.paused) {
    unlocked = true;
    return;
  }
  a.src = SILENT_WAV;
  void a
    .play()
    .then(() => {
      unlocked = true;
    })
    .catch(() => undefined);
}

/**
 * The character's voice. There is no fallback voice on purpose: when the stream fails the line is
 * still on screen, `error` says so, and nothing pretends otherwise.
 */
export function useSpeaker() {
  const playSeqRef = useRef(0);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const unlock = useCallback(() => unlockAudio(), []);

  const play = useCallback(
    (audioUrl: string | null, onStart?: () => void): Promise<Played> => {
      if (!audioUrl) return Promise.resolve({ startedAt: null });
      // A newer play() (or stop()) supersedes this one: the element's pending play() promise then
      // rejects with AbortError. That is not the stream failing and is not an error.
      const my = ++playSeqRef.current;
      const current = () => playSeqRef.current === my;
      return new Promise((resolve) => {
        const a = getAudio();
        let startedAt: number | null = null;
        const cleanup = () => {
          if (current()) {
            a.onplaying = null;
            a.onended = null;
            a.onerror = null;
            setSpeaking(false);
          }
        };
        const done = () => {
          cleanup();
          resolve({ startedAt });
        };
        const failed = (why: string) => {
          if (current()) setError(`Voice unavailable (${why}). The line is still on screen.`);
          done();
        };
        a.onplaying = () => {
          startedAt = performance.now();
          setError(null);
          setSpeaking(true);
          onStart?.();
        };
        a.onended = done;
        // A 503 from the API, or a cut stream, both land here.
        a.onerror = () => failed(a.error?.code === MediaError.MEDIA_ERR_NETWORK ? "network" : "stream failed");
        a.src = `${env.NEXT_PUBLIC_API_BASE_URL}${audioUrl}`;
        void a.play().catch((e: unknown) => {
          if (!current() || (e instanceof DOMException && e.name === "AbortError")) {
            done();
            return;
          }
          if (e instanceof DOMException && e.name === "NotAllowedError") {
            cleanup();
            resolve({ startedAt: null, blocked: true });
            return;
          }
          failed("playback blocked");
        });
      });
    },
    [],
  );

  const stop = useCallback(() => {
    const a = shared;
    if (a) {
      ++playSeqRef.current;
      a.pause();
      a.currentTime = 0;
    }
    setSpeaking(false);
  }, []);

  useEffect(() => stop, [stop]);

  return { unlock, play, stop, speaking, error };
}
