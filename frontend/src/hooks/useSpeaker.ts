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
 * One audio element for the character's voice. There is no fallback voice on purpose: when the
 * stream fails the line is still on screen, `error` says so, and nothing pretends otherwise.
 */
export function useSpeaker() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playSeqRef = useRef(0);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAudio = useCallback(() => {
    if (audioRef.current) return audioRef.current;
    const a = new Audio();
    a.preload = "auto";
    a.setAttribute("playsinline", "true");
    audioRef.current = a;
    return a;
  }, []);

  const unlock = useCallback(() => {
    const a = getAudio();
    a.src = SILENT_WAV;
    void a.play().catch(() => undefined);
  }, [getAudio]);

  const play = useCallback(
    (audioUrl: string | null): Promise<Played> => {
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
    [getAudio],
  );

  const stop = useCallback(() => {
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.currentTime = 0;
    }
    setSpeaking(false);
  }, []);

  useEffect(() => stop, [stop]);

  return { unlock, play, stop, speaking, error };
}
