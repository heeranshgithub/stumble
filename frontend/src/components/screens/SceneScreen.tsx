"use client";

import { ChevronLeft, Keyboard, Mic, Send, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Chip } from "@/components/stumble/Chip";
import { LyricLine, type LyricWord } from "@/components/stumble/LyricLine";
import { PillButton } from "@/components/stumble/PillButton";
import { useHoldToTalk, type Capture } from "@/hooks/useHoldToTalk";
import { useSpeaker } from "@/hooks/useSpeaker";
import { getErrorMessage } from "@/lib/errors";
import { getPatience } from "@/lib/patience";
import { useSendTurnMutation, useStartSessionMutation } from "@/store/endpoints/sessions";
import type { SessionDto, StumbleDto, TurnDto } from "@/types/api";

type Phase = "starting" | "idle" | "recording" | "thinking" | "speaking" | "done" | "failed";

const isDev = process.env.NODE_ENV !== "production";

function strip(w: string) {
  return w.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
}

/** The learner's words, with any stumbled word left hollow. */
function learnerWords(text: string, stumbles: StumbleDto[]): LyricWord[] {
  const missed = new Set(stumbles.flatMap((s) => s.said.split(/\s+/).map(strip)).filter(Boolean));
  return text
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => ({ text: w, state: missed.has(strip(w)) ? "miss" : "on" }));
}

function fmt(ms: number) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function SceneScreen({ sceneId }: { sceneId: string }) {
  const [startSession, startState] = useStartSessionMutation();
  const [sendTurn] = useSendTurnMutation();
  const [session, setSession] = useState<SessionDto | null>(null);
  const [phase, setPhase] = useState<Phase>("starting");
  const [failure, setFailure] = useState<string | null>(null);
  const [typing, setTyping] = useState(false);
  const [draft, setDraft] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [shownTranslation, setShownTranslation] = useState<string | null>(null);

  const router = useRouter();
  const startedRef = useRef(false);
  const t0Ref = useRef(0);
  const listRef = useRef<HTMLDivElement>(null);
  const speaker = useSpeaker(session?.ttsProvider ?? "browser");
  const debriefHref = session?.id ? `/scene/${sceneId}/debrief?session=${session.id}` : "/";

  // One session per visit. The ref guards React's double-invoked dev effects.
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    startSession({ sceneId, patience: getPatience() })
      .unwrap()
      .then((s) => {
        setSession(s);
        setPhase("idle");
      })
      .catch((e: unknown) => {
        setFailure(getErrorMessage(e as Parameters<typeof getErrorMessage>[0]).message);
        setPhase("failed");
      });
  }, [sceneId, startSession]);

  useEffect(() => {
    const id = window.setInterval(() => setElapsed((e) => e + 1000), 1000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    listRef.current?.lastElementChild?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [session?.turns.length, phase]);

  const sessionId = session?.id ?? null;
  const submit = useCallback(
    async (form: FormData) => {
      if (!sessionId) return;
      setPhase("thinking");
      t0Ref.current = performance.now();
      try {
        const updated = await sendTurn({ id: sessionId, form }).unwrap();
        setSession(updated);
        const reply = updated.turns[updated.turns.length - 1];
        if (reply && reply.role === "character") {
          setPhase("speaking");
          const { startedAt } = await speaker.play(reply.audioUrl, reply.text);
          if (startedAt !== null) setLatencyMs(Math.round(startedAt - t0Ref.current));
        }
        setPhase(updated.done ? "done" : "idle");
      } catch (e) {
        setFailure(getErrorMessage(e as Parameters<typeof getErrorMessage>[0]).message);
        setPhase("idle");
      }
    },
    [sessionId, sendTurn, speaker],
  );

  const onCapture = useCallback(
    (c: Capture) => {
      const form = new FormData();
      form.append("audio", c.blob, `turn.${c.mime.includes("mp4") ? "mp4" : "webm"}`);
      form.append("clientPauseMs", String(c.pauseMs));
      void submit(form);
    },
    [submit],
  );

  const busy = phase !== "idle";
  const mic = useHoldToTalk(onCapture, busy);

  // The first tap on the screen unlocks audio; also (re)plays the opening line once.
  const openedRef = useRef(false);
  const onFirstTap = useCallback(() => {
    if (openedRef.current || !session) return;
    openedRef.current = true;
    speaker.unlock();
    const opening = session.turns[0];
    if (opening) void speaker.play(opening.audioUrl, opening.text);
  }, [session, speaker]);

  const sendTyped = () => {
    const text = draft.trim();
    if (!text) return;
    const form = new FormData();
    form.append("text", text);
    form.append("clientPauseMs", "0");
    setDraft("");
    setTyping(false);
    void submit(form);
  };

  if (phase === "failed") {
    return (
      <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
        <h1 className="text-3xl font-extrabold tracking-tight">Couldn&apos;t start the scene.</h1>
        <p className="mt-2 text-ink-2">{failure ?? getErrorMessage(startState.error).message}</p>
        <PillButton href="/" className="mt-6">
          Back to Today
        </PillButton>
      </div>
    );
  }

  const color = session?.sceneColor ?? "cafe";
  const name = session?.characterName ?? "…";

  return (
    <div
      className="flex flex-1 flex-col bg-scene"
      data-scene={color}
      onPointerDownCapture={onFirstTap}
    >
      <header className="flex items-center justify-between px-5 pt-12 pb-2">
        <Link href="/" className="flex items-center gap-1 text-xs font-extrabold">
          <ChevronLeft className="size-4" strokeWidth={2.5} />
          {session?.sceneTitle ?? "Scene"}
        </Link>
        <div className="flex items-center gap-2">
          {isDev && latencyMs !== null ? <Chip tone="stumble">{latencyMs} ms</Chip> : null}
          <Chip>
            {name} · {fmt(elapsed)}
          </Chip>
          {session?.id && phase !== "done" ? (
            <button
              type="button"
              aria-label="End scene"
              onClick={() => {
                speaker.stop();
                router.push(debriefHref);
              }}
              className="grid size-7 place-items-center rounded-pill bg-ink/10 text-ink"
            >
              <X className="size-4" strokeWidth={2.5} />
            </button>
          ) : null}
        </div>
      </header>

      <div ref={listRef} className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 pt-3 pb-4">
        {session ? (
          session.turns.map((t, i) => (
            <TurnView
              key={t.id}
              turn={t}
              name={name}
              latest={i >= session.turns.length - 2}
              showTranslation={shownTranslation === t.id}
              onToggleTranslation={() => setShownTranslation((cur) => (cur === t.id ? null : t.id))}
              onReplay={() => void speaker.play(t.audioUrl, t.text)}
            />
          ))
        ) : (
          <p className="text-xs font-bold text-ink-2">Starting…</p>
        )}
        {phase === "recording" || mic.holding ? (
          <div>
            <p className="text-xs font-bold text-ink-2">You · live</p>
            <div className="mt-1 flex h-7 items-end gap-1" aria-hidden="true">
              {Array.from({ length: 12 }, (_, i) => (
                <span
                  key={i}
                  className="w-1 rounded-full bg-ink"
                  style={{ height: `${6 + Math.round(mic.level * 22 * ((i % 3) + 1) / 2)}px` }}
                />
              ))}
            </div>
          </div>
        ) : null}
        {phase === "thinking" ? <p className="text-xs font-bold text-ink-2">{name} is thinking…</p> : null}
        {phase === "done" ? (
          <section className="-mx-5 mt-2 bg-ink px-5 py-5 text-paper">
            <p className="text-2xl font-extrabold tracking-tight">Scene cleared.</p>
            <p className="mt-1 text-sm text-paper-2">
              {session?.turns.reduce((n, t) => n + t.stumbles.length, 0) ?? 0} stumbles caught. See what they
              were and when you&apos;ll meet them again.
            </p>
            <PillButton href={debriefHref} variant="paper" className="mt-4">
              See what got caught
            </PillButton>
          </section>
        ) : null}
      </div>

      {phase !== "done" ? (
        <footer className="px-5 pb-8 pt-2">
          {failure && phase === "idle" ? <p className="mb-2 text-center text-xs font-bold text-stumble">{failure}</p> : null}
          {mic.error ? <p className="mb-2 text-center text-xs font-bold text-stumble">{mic.error}</p> : null}
          {typing ? (
            <form
              className="flex items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                sendTyped();
              }}
            >
              <input
                autoFocus
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Écris ta réponse…"
                lang="fr"
                className="h-12 flex-1 rounded-pill bg-paper px-4 text-[15px] font-bold text-ink outline-none placeholder:text-ink/65"
              />
              <button
                type="submit"
                aria-label="Send"
                disabled={busy || !draft.trim()}
                className="grid size-12 place-items-center rounded-pill bg-ink text-paper disabled:opacity-50"
              >
                <Send className="size-5" strokeWidth={2.25} />
              </button>
            </form>
          ) : (
            <>
              <button
                type="button"
                aria-label="Hold to speak"
                aria-pressed={mic.holding}
                disabled={busy || !mic.supported}
                {...mic.handlers}
                className={`mx-auto grid size-[84px] touch-none select-none place-items-center rounded-pill text-paper transition-[background-color,box-shadow,transform] duration-200 ease-out-expo disabled:opacity-50 ${
                  mic.holding
                    ? "scale-105 bg-stumble shadow-[0_0_0_16px_color-mix(in_oklch,var(--color-stumble)_25%,transparent)]"
                    : "bg-ink shadow-[0_0_0_12px_color-mix(in_oklch,var(--color-ink)_12%,transparent)]"
                }`}
              >
                <Mic className="size-8" strokeWidth={2.25} />
              </button>
              <div className="mt-4 flex items-center justify-center gap-4 text-[11px] font-extrabold text-ink-2">
                <span>{mic.holding ? "release to send" : phase === "speaking" ? `${name} is speaking` : "hold to speak"}</span>
                <span aria-hidden="true">·</span>
                <button type="button" className="flex items-center gap-1 underline-offset-2 hover:underline" onClick={() => setTyping(true)}>
                  <Keyboard className="size-3.5" strokeWidth={2.5} />
                  type
                </button>
              </div>
            </>
          )}
        </footer>
      ) : null}
    </div>
  );
}

function TurnView({
  turn,
  name,
  latest,
  showTranslation,
  onToggleTranslation,
  onReplay,
}: {
  turn: TurnDto;
  name: string;
  /** The last exchange: the learner line fills in word by word, the reply fades in. */
  latest: boolean;
  showTranslation: boolean;
  onToggleTranslation: () => void;
  onReplay: () => void;
}) {
  if (turn.role === "character") {
    return (
      <div className={latest ? "fade-in" : undefined}>
        <p className="text-xs font-bold text-ink-2">{name}</p>
        <button type="button" onClick={onToggleTranslation} className="block text-left">
          <p className="text-[20px] font-extrabold leading-[1.2] tracking-[-0.02em] text-ink/65">{turn.text}</p>
        </button>
        {showTranslation && turn.textEn ? <p className="mt-1 text-sm font-bold text-ink-2">{turn.textEn}</p> : null}
        <button type="button" onClick={onReplay} className="mt-1 text-[11px] font-extrabold text-ink-2 underline-offset-2 hover:underline">
          replay{turn.textEn ? " · tap line to translate" : ""}
        </button>
      </div>
    );
  }
  const freeze = turn.stumbles.find((s) => s.type === "freeze");
  const others = turn.stumbles.filter((s) => s.type !== "freeze");
  return (
    <div>
      <p className="text-xs font-bold text-ink-2">You</p>
      {turn.text ? (
        <LyricLine className="mt-0.5" animate={latest} words={learnerWords(turn.text, turn.stumbles)} />
      ) : null}
      {turn.stumbles.length > 0 || turn.wins.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {others.map((s, i) => (
            <Chip key={i} tone="ink">
              caught · {s.said} → {s.target}
            </Chip>
          ))}
          {freeze ? (
            <Chip tone="stumble">
              you froze · {(turn.pauseMs / 1000).toFixed(0)}s → {freeze.target}
            </Chip>
          ) : null}
          {turn.wins.map((w, i) => (
            <Chip key={`w${i}`}>✓ {w.phrase}</Chip>
          ))}
        </div>
      ) : null}
    </div>
  );
}
