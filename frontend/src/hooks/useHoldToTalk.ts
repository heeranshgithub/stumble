"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent, PointerEvent } from "react";

export interface Capture {
  blob: Blob;
  mime: string;
  /** Longest silence while held (mid-turn or trailing). ≥ ~3 s is a freeze. */
  pauseMs: number;
  durationMs: number;
}

interface Stats {
  startedAt: number;
  spokeAt: number | null;
  lastSpeechAt: number | null;
  longestGapMs: number;
  floor: number;
}

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];

function pickMime(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  return MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m));
}

/**
 * Hold-to-talk on a pointer (or the space bar). Records with MediaRecorder and measures silence with an
 * AnalyserNode while held, so a freeze is known on the client before the audio even uploads.
 * `maxMs` auto-releases (the twenty-second placement).
 */
export function useHoldToTalk(onCapture: (c: Capture) => void, disabled = false, maxMs?: number) {
  const [holding, setHolding] = useState(false);
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const ctxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number>(0);
  const maxTimerRef = useRef<number>(0);
  const statsRef = useRef<Stats | null>(null);
  const activeRef = useRef(false);
  const onCaptureRef = useRef(onCapture);
  useEffect(() => {
    onCaptureRef.current = onCapture;
  }, [onCapture]);

  const supported =
    typeof window !== "undefined" &&
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof MediaRecorder !== "undefined";

  const getStream = useCallback(async () => {
    if (streamRef.current) return streamRef.current;
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    streamRef.current = stream;
    return stream;
  }, []);

  const meter = useCallback((stream: MediaStream) => {
    const ctx = ctxRef.current ?? new AudioContext();
    ctxRef.current = ctx;
    void ctx.resume();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 1024;
    source.connect(analyser);
    const buf = new Float32Array(analyser.fftSize);

    const tick = () => {
      if (!activeRef.current) {
        source.disconnect();
        return;
      }
      analyser.getFloatTimeDomainData(buf);
      let sum = 0;
      for (let i = 0; i < buf.length; i++) sum += (buf[i] ?? 0) ** 2;
      const rms = Math.sqrt(sum / buf.length);
      const now = performance.now();
      const s = statsRef.current;
      if (s) {
        // Adapt the noise floor during the first 150 ms; speech is 3× the floor, at least 0.015.
        if (now - s.startedAt < 150) s.floor = Math.max(s.floor, rms);
        const threshold = Math.max(0.015, s.floor * 3);
        if (rms > threshold) {
          if (s.spokeAt === null) s.spokeAt = now;
          if (s.lastSpeechAt !== null) s.longestGapMs = Math.max(s.longestGapMs, now - s.lastSpeechAt);
          s.lastSpeechAt = now;
        }
      }
      setLevel(Math.min(1, rms * 8));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const stop = useCallback(() => {
    if (!activeRef.current) return;
    activeRef.current = false;
    cancelAnimationFrame(rafRef.current);
    window.clearTimeout(maxTimerRef.current);
    setHolding(false);
    setLevel(0);
    const r = recorderRef.current;
    if (r && r.state !== "inactive") r.stop();
    recorderRef.current = null;
  }, []);

  const start = useCallback(async () => {
    if (disabled || activeRef.current || !supported) return;
    activeRef.current = true;
    setError(null);
    try {
      const stream = await getStream();
      if (!activeRef.current) return; // released before permission came back
      const mime = pickMime();
      const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const s = statsRef.current;
        const now = performance.now();
        const trailing = s ? (s.lastSpeechAt !== null ? now - s.lastSpeechAt : now - s.startedAt) : 0;
        const pauseMs = Math.round(Math.max(s?.longestGapMs ?? 0, trailing));
        const durationMs = Math.round(s ? now - s.startedAt : 0);
        const type = recorder.mimeType || mime || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        statsRef.current = null;
        if (blob.size > 0) onCaptureRef.current({ blob, mime: type, pauseMs, durationMs });
      };
      recorderRef.current = recorder;
      statsRef.current = {
        startedAt: performance.now(),
        spokeAt: null,
        lastSpeechAt: null,
        longestGapMs: 0,
        floor: 0,
      };
      recorder.start(250);
      meter(stream);
      setHolding(true);
      if (maxMs) maxTimerRef.current = window.setTimeout(stop, maxMs);
    } catch (e) {
      activeRef.current = false;
      setError(e instanceof Error && e.name === "NotAllowedError" ? "Microphone blocked. Type instead." : "Mic unavailable.");
    }
  }, [disabled, supported, getStream, meter, maxMs, stop]);

  useEffect(() => {
    return () => {
      activeRef.current = false;
      cancelAnimationFrame(rafRef.current);
      window.clearTimeout(maxTimerRef.current);
      const r = recorderRef.current;
      if (r && r.state !== "inactive") r.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      void ctxRef.current?.close();
    };
  }, []);

  const handlers = {
    onPointerDown: (e: PointerEvent<HTMLElement>) => {
      if (e.button !== 0 && e.pointerType === "mouse") return;
      e.preventDefault();
      e.currentTarget.setPointerCapture(e.pointerId);
      void start();
    },
    onPointerUp: () => stop(),
    onPointerCancel: () => stop(),
    onContextMenu: (e: PointerEvent<HTMLElement> | React.MouseEvent) => e.preventDefault(),
    onKeyDown: (e: KeyboardEvent<HTMLElement>) => {
      if (e.code === "Space" && !e.repeat) {
        e.preventDefault();
        void start();
      }
    },
    onKeyUp: (e: KeyboardEvent<HTMLElement>) => {
      if (e.code === "Space") stop();
    },
  };

  return { holding, level, error, supported, handlers, start, stop };
}
