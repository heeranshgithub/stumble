"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { env } from "@/lib/env";
import type { TtsProvider } from "@/types/api";

// 0.1 s of silence. Playing it inside the first tap unlocks audio on iOS for the rest of the session.
const SILENT_WAV =
  "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=";

export interface Played {
  /** performance.now() when sound actually started, or null if it never did. */
  startedAt: number | null;
}

/** One audio element for the character's voice, plus the browser's own synthesizer as fallback. */
export function useSpeaker(provider: TtsProvider) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [speaking, setSpeaking] = useState(false);

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
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance("");
      u.volume = 0;
      window.speechSynthesis.speak(u);
    }
  }, [getAudio]);

  const speakWithBrowser = useCallback(
    (text: string): Promise<Played> =>
      new Promise((resolve) => {
        if (!("speechSynthesis" in window)) return resolve({ startedAt: null });
        const synth = window.speechSynthesis;
        synth.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = "fr-FR";
        u.rate = 0.95;
        const fr = synth.getVoices().find((v) => v.lang.toLowerCase().startsWith("fr"));
        if (fr) u.voice = fr;
        let startedAt: number | null = null;
        u.onstart = () => {
          startedAt = performance.now();
          setSpeaking(true);
        };
        u.onend = () => {
          setSpeaking(false);
          resolve({ startedAt });
        };
        u.onerror = () => {
          setSpeaking(false);
          resolve({ startedAt });
        };
        synth.speak(u);
      }),
    [],
  );

  const play = useCallback(
    (audioUrl: string | null, text: string): Promise<Played> => {
      if (provider === "browser" || !audioUrl) return speakWithBrowser(text);
      return new Promise((resolve) => {
        const a = getAudio();
        let startedAt: number | null = null;
        const done = () => {
          a.onplaying = null;
          a.onended = null;
          a.onerror = null;
          setSpeaking(false);
          resolve({ startedAt });
        };
        a.onplaying = () => {
          startedAt = performance.now();
          setSpeaking(true);
        };
        a.onended = done;
        a.onerror = () => {
          // The stream failed (quota, network). Say the line anyway.
          done();
          void speakWithBrowser(text);
        };
        a.src = `${env.NEXT_PUBLIC_API_BASE_URL}${audioUrl}`;
        void a.play().catch(() => {
          done();
          void speakWithBrowser(text);
        });
      });
    },
    [provider, getAudio, speakWithBrowser],
  );

  const stop = useCallback(() => {
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.currentTime = 0;
    }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  useEffect(() => stop, [stop]);

  return { unlock, play, stop, speaking };
}
