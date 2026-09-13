"use client";

import { ChevronLeft, Keyboard, Mic, Send, Volume2, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import type { PointerEvent } from "react";

import { Chip } from "@/components/stumble/Chip";
import { LyricLine, type LyricWord } from "@/components/stumble/LyricLine";
import { PillButton } from "@/components/stumble/PillButton";
import { useHoldToTalk, type Capture } from "@/hooks/useHoldToTalk";
import { useSpeaker } from "@/hooks/useSpeaker";
import { getErrorMessage } from "@/lib/errors";
import { getPatience } from "@/lib/patience";
import { sceneColor } from "@/lib/scenes";
import { useGetReadyQuery } from "@/store/endpoints/health";
import { useLazyGetSessionQuery, useSendTurnMutation, useStartSessionMutation } from "@/store/endpoints/sessions";
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

function scrollParent(el: HTMLElement | null): HTMLElement | null {
  for (let n = el?.parentElement ?? null; n; n = n.parentElement) {
    const { overflowY } = getComputedStyle(n);
    if (overflowY === "auto" || overflowY === "scroll") return n;
  }
  return null;
}

/** The line the learner is answering: the last thing the character said. */
function latestCharacterLine(session: SessionDto): TurnDto | undefined {
  for (let i = session.turns.length - 1; i >= 0; i--) {
    const t = session.turns[i];
    if (t?.role === "character") return t;
  }
  return undefined;
}

/** `resumeId` is the `?session=` from the URL: an earlier session of this scene to pick back up. */
export function SceneScreen({ sceneId, resumeId }: { sceneId: string; resumeId: string | null }) {
  const [startSession, startState] = useStartSessionMutation();
  const [getSession] = useLazyGetSessionQuery();
  const [sendTurn] = useSendTurnMutation();
  const [session, setSession] = useState<SessionDto | null>(null);
  const [phase, setPhase] = useState<Phase>("starting");
  const [failure, setFailure] = useState<string | null>(null);
  const [typing, setTyping] = useState(false);
  const [draft, setDraft] = useState("");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [shownTranslation, setShownTranslation] = useState<string | null>(null);

  const router = useRouter();
  const startedRef = useRef(false);
  const t0Ref = useRef(0);
  const listRef = useRef<HTMLDivElement>(null);
  const speaker = useSpeaker();
  // Fake providers are a deliberate offline mode; when they're on, say so where the reviewer looks.
  const ready = useGetReadyQuery();
  const debriefHref = session?.id ? `/scene/${sceneId}/debrief?session=${session.id}` : "/";

  // One session per URL: a fresh visit starts one and writes its id into the query string, so a
  // refresh resumes the conversation instead of abandoning it (and its stumbles) for a new one.
  // The ref guards React's double-invoked dev effects.
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    const fresh = () =>
      startSession({ sceneId, patience: getPatience() })
        .unwrap()
        .then((s) => {
          setSession(s);
          setPhase("idle");
          if (s.id) {
            const url = new URL(window.location.href);
            url.searchParams.set("session", s.id);
            window.history.replaceState(null, "", url);
          }
        });
    const resume = (id: string) =>
      getSession(id)
        .unwrap()
        .then((s) => {
          if (s.sceneId !== sceneId) throw new Error("session belongs to another scene");
          setSession(s);
          setPhase(s.done ? "done" : "idle");
        })
        // Gone, or another device's: start over rather than show an error for a stale link.
        .catch(() => fresh());
    (resumeId ? resume(resumeId) : fresh()).catch((e: unknown) => {
      setFailure(getErrorMessage(e as Parameters<typeof getErrorMessage>[0]).message);
      setPhase("failed");
    });
  }, [sceneId, resumeId, startSession, getSession]);

  // The shell's `main` is the only scroller and the header and mic are pinned inside it, so a new
  // turn (or the live meter) scrolls it to the bottom: the latest line lands just above the mic.
  useEffect(() => {
    const scroller = scrollParent(listRef.current);
    scroller?.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" });
  }, [session?.turns.length, phase]);

  const sessionId = session?.id ?? null;
  const submit = useCallback(
    async (form: FormData) => {
      if (!sessionId) return;
      // A failed turn's message ("Nothing was heard…") belongs to that turn only.
      setFailure(null);
      setPhase("thinking");
      t0Ref.current = performance.now();
      try {
        const updated = await sendTurn({ id: sessionId, form }).unwrap();
        setSession(updated);
        const reply = updated.turns[updated.turns.length - 1];
        if (reply && reply.role === "character") {
          setPhase("speaking");
          const { startedAt } = await speaker.play(reply.audioUrl);
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
      // Silence is never sent to the transcriber, which invents captions for it. A long silent
      // hold is still a turn: the freeze the server logs from the pause alone.
      if (c.spoke) form.append("audio", c.blob, `turn.${c.mime.includes("mp4") ? "mp4" : "webm"}`);
      form.append("clientPauseMs", String(c.spoke ? c.pauseMs : c.durationMs));
      void submit(form);
    },
    [submit],
  );

  const busy = phase !== "idle";
  const mic = useHoldToTalk(onCapture, busy);

  // The first tap on the screen unlocks audio; also (re)plays the opening line once. A tap on
  // something that speaks by itself (replay, a stumble chip) is left to it, so nothing starts twice.
  const openedRef = useRef(false);
  const [needsTap, setNeedsTap] = useState(false);
  const onFirstTap = useCallback(
    (e: PointerEvent<HTMLElement>) => {
      if (openedRef.current || !session) return;
      openedRef.current = true;
      setNeedsTap(false);
      speaker.unlock();
      if ((e.target as HTMLElement).closest("[data-speaks]")) return;
      const line = latestCharacterLine(session);
      if (line && !session.done) void speaker.play(line.audioUrl);
    },
    [session, speaker],
  );

  // Try to speak the line as soon as the session is here. Browsers allow that only after the page
  // has been touched (Chrome: any earlier click on the site; iOS: never on a fresh load), so a
  // refusal isn't an error: it means "wait for the first tap", and the screen says so.
  const autoTriedRef = useRef(false);
  useEffect(() => {
    if (autoTriedRef.current || !session || session.done || phase !== "idle") return;
    autoTriedRef.current = true;
    const line = latestCharacterLine(session);
    if (!line?.audioUrl) return;
    void speaker.play(line.audioUrl).then((r) => {
      if (openedRef.current) return;
      if (r.blocked) setNeedsTap(true);
      else openedRef.current = true;
    });
  }, [session, phase, speaker]);

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

  const color = session?.sceneColor ?? sceneColor(sceneId);
  const name = session?.characterName ?? "…";

  return (
    <div
      className="flex min-h-0 flex-1 flex-col bg-scene"
      data-scene={color}
      onPointerDownCapture={onFirstTap}
    >
      <header className="sticky top-0 z-10 flex items-center justify-between bg-scene px-5 pt-12 pb-2">
        {/* Back means back: to Scenes, Today, the review's end or the debrief, whichever sent you here.
            A deep link with no history goes to the scene list. */}
        <button
          type="button"
          onClick={() => (window.history.length > 1 ? router.back() : router.push("/scenes"))}
          className="flex items-center gap-1 text-xs font-extrabold"
        >
          <ChevronLeft className="size-4" strokeWidth={2.5} />
          {session?.sceneTitle ?? "Scene"}
        </button>
        <div className="flex items-center gap-2">
          {ready.data && ready.data.providers !== "real" ? <Chip tone="stumble">{ready.data.providers} providers</Chip> : null}
          {isDev && latencyMs !== null ? <Chip tone="stumble">{latencyMs} ms</Chip> : null}
          {/* No clock: a scene has no time limit, and a counter running while you search for a word
              is a grade in disguise. The debrief says how long it took. */}
          <Chip>{name}</Chip>
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

      {session ? (
        <p className="px-5 pb-2 text-xs font-bold text-ink-2">
          Goal · {session.goal.toLowerCase().replace(/\.$/, "")}
        </p>
      ) : null}

      <div
        ref={listRef}
        className="flex flex-1 flex-col gap-4 px-5 pt-3 pb-4"
      >
        {session ? (
          session.turns.map((t, i) => (
            <TurnView
              key={t.id}
              turn={t}
              name={name}
              latest={i >= session.turns.length - 2}
              showTranslation={shownTranslation === t.id}
              onToggleTranslation={() => setShownTranslation((cur) => (cur === t.id ? null : t.id))}
              onReplay={() => void speaker.play(t.audioUrl)}
              onSay={(audioUrl) => void speaker.play(audioUrl)}
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
        <footer className="sticky bottom-0 z-10 bg-scene px-5 pb-8 pt-2">
          {failure && phase === "idle" ? <p className="mb-6 text-center text-xs font-bold text-stumble">{failure}</p> : null}
          {speaker.error ? <p className="mb-6 text-center text-xs font-bold text-stumble">{speaker.error}</p> : null}
          {needsTap && !speaker.error ? (
            <p className="mb-6 text-center text-xs font-bold text-ink-2">tap anywhere to hear {name}</p>
          ) : null}
          {mic.error ? <p className="mb-6 text-center text-xs font-bold text-stumble">{mic.error}</p> : null}
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
  onSay,
}: {
  turn: TurnDto;
  name: string;
  /** The last exchange: the learner line fills in word by word, the reply fades in. */
  latest: boolean;
  /** Off by default on purpose: a little friction, so the learner listens first and reads only when stuck. */
  showTranslation: boolean;
  onToggleTranslation: () => void;
  onReplay: () => void;
  /** Speak a target phrase: tapping a stumble chip is how the learner hears what they should have said. */
  onSay: (audioUrl: string | null) => void;
}) {
  if (turn.role === "character") {
    return (
      <div className={latest ? "fade-in" : undefined}>
        <p className="text-xs font-bold text-ink-2">{name}</p>
        <button type="button" onClick={onToggleTranslation} className="block text-left">
          <p className="text-[20px] font-extrabold leading-[1.2] tracking-[-0.02em] text-ink/65">{turn.text}</p>
        </button>
        {showTranslation && turn.textEn ? <p className="mt-1 text-sm font-bold text-ink-2">{turn.textEn}</p> : null}
        <button
          type="button"
          data-speaks
          onClick={onReplay}
          className="mt-1 text-[11px] font-extrabold text-ink-2 underline-offset-2 hover:underline"
        >
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
            <button key={i} type="button" data-speaks onClick={() => onSay(s.audioUrl)} aria-label={`Hear ${s.target}`}>
              <Chip tone="ink">
                <Volume2 className="size-3" strokeWidth={2.5} />
                caught · {s.said} → {s.target}
              </Chip>
            </button>
          ))}
          {freeze ? (
            <button type="button" data-speaks onClick={() => onSay(freeze.audioUrl)} aria-label={`Hear ${freeze.target}`}>
              <Chip tone="stumble">
                <Volume2 className="size-3" strokeWidth={2.5} />
                you froze · {(turn.pauseMs / 1000).toFixed(0)}s → {freeze.target}
              </Chip>
            </button>
          ) : null}
          {turn.wins.map((w, i) => (
            <Chip key={`w${i}`}>✓ {w.phrase}</Chip>
          ))}
        </div>
      ) : null}
    </div>
  );
}
