"use client";

import { Check, Languages, MessageCircleQuestion, PenLine, Timer } from "lucide-react";
import { useEffect, useRef } from "react";

import { Blob } from "@/components/stumble/Blob";
import { Chip } from "@/components/stumble/Chip";
import { PillButton } from "@/components/stumble/PillButton";
import { getErrorMessage } from "@/lib/errors";
import { useFinishSessionMutation } from "@/store/endpoints/sessions";
import type { DebriefStumbleDto, StumbleType } from "@/types/api";

const icon: Record<StumbleType, typeof Languages> = {
  code_switch: Languages,
  freeze: Timer,
  correction: PenLine,
  miss: MessageCircleQuestion,
};

const label: Record<StumbleType, string> = {
  code_switch: "code-switch",
  freeze: "freeze",
  correction: "correction",
  miss: "miss",
};

function whenLabel(iso: string | null): string {
  if (!iso) return "no reviews yet";
  const due = new Date(iso);
  const now = new Date();
  const days = Math.round((due.getTime() - now.getTime()) / 86_400_000);
  const time = due.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  if (days <= 0) return `due now`;
  if (days === 1) return `due tomorrow ${time}`;
  return `due in ${days} days`;
}

export function DebriefScreen({ sceneId, sessionId }: { sceneId: string; sessionId: string | null }) {
  const [finish, { data, error, isLoading }] = useFinishSessionMutation();
  const firedRef = useRef(false);

  useEffect(() => {
    if (firedRef.current || !sessionId) return;
    firedRef.current = true;
    void finish(sessionId);
  }, [finish, sessionId]);

  if (!sessionId) {
    return (
      <Missing title="No scene to debrief." body="Start a scene first; the debrief comes at the end of it." />
    );
  }
  if (error) {
    const e = getErrorMessage(error);
    return <Missing title="Couldn't finish the scene." body={e.message} requestId={e.requestId} />;
  }
  if (isLoading || !data) return <Skeleton />;

  const d = data;
  const total = d.stumbles.length;
  const win = d.wins[0];
  const headline = d.goalReached ? goalHeadline(d.sceneId) : `Not quite. ${d.characterName} is still waiting.`;

  return (
    <div className="flex flex-1 flex-col" data-scene={d.sceneColor}>
      <Blob color="scene" className="pt-14 pb-5">
        <p className="text-xs font-bold text-ink-2">
          {d.sceneTitle} · {Math.floor(d.durationS / 60)}:{String(d.durationS % 60).padStart(2, "0")}
        </p>
        <h1 className="mt-2 text-[30px] font-extrabold leading-[1.05] tracking-[-0.03em]">{headline}</h1>
        <p className="mt-2 text-sm font-bold text-ink-2">
          {d.goalReached ? "Goal reached. " : `Goal: ${d.goal.toLowerCase().replace(/\.$/, "")}. `}
          {total === 0 ? "No stumbles caught." : total === 1 ? "1 stumble caught" : `${total} stumbles caught`}
          {win ? `, 1 clean win.` : total === 0 ? "" : "."}
        </p>
      </Blob>

      <div className="flex flex-1 flex-col">
        {total > 0 ? (
          <ul className="divide-y divide-ink/10 px-5">
            {d.stumbles.map((s) => (
              <StumbleRow key={s.cardId} s={s} />
            ))}
            {win ? (
              <li className="flex gap-3 py-3">
                <span className="grid size-9 flex-none place-items-center rounded-xl bg-pharmacie text-ink">
                  <Check className="size-4" strokeWidth={2.5} />
                </span>
                <div className="min-w-0">
                  <p className="text-[15px] font-extrabold leading-tight">{win.phrase}</p>
                  <p className="text-xs font-bold text-ink/65">
                    {win.cardId ? "a card you'd stumbled on, produced clean" : "clean, first try"}
                  </p>
                </div>
              </li>
            ) : null}
          </ul>
        ) : (
          <div className="px-5 py-6">
            <p className="text-[18px] font-extrabold leading-snug text-ink/65">
              Nothing to catch this time. Try the next scene at a harder patience.
            </p>
          </div>
        )}

        <div className="mt-auto px-5 pb-8 pt-4">
          <div className="flex items-center justify-between rounded-2xl bg-ink px-4 py-3 text-paper">
            <div>
              <p className="text-[10px] font-extrabold uppercase tracking-[0.12em] text-paper-2">Added to deck</p>
              <p className="text-[15px] font-extrabold">
                {d.cardsAdded === 1 ? "1 card" : `${d.cardsAdded} cards`}
                {d.cardsRelapsed > 0 ? ` · ${d.cardsRelapsed} relapsed` : ""} · {whenLabel(d.nextReviewAt)}
              </p>
            </div>
            <Chip tone="stumble">FSRS</Chip>
          </div>
          <PillButton href="/" className="mt-4">
            Done for today
          </PillButton>
          <PillButton href={`/scene/${sceneId}`} variant="paper" className="mt-2 border border-ink/15">
            Replay scene
          </PillButton>
        </div>
      </div>
    </div>
  );
}

function StumbleRow({ s }: { s: DebriefStumbleDto }) {
  const Icon = icon[s.type];
  return (
    <li className="flex gap-3 py-3">
      <span
        className={`grid size-9 flex-none place-items-center rounded-xl ${
          s.type === "freeze" ? "bg-stumble/15 text-stumble" : "bg-ink/10 text-ink"
        }`}
      >
        <Icon className="size-4" strokeWidth={2.5} />
      </span>
      <div className="min-w-0">
        <p className="text-[15px] font-extrabold leading-tight">
          {s.type === "freeze" ? s.target : (
            <>
              <span className="text-ink/65 line-through decoration-stumble decoration-2">{s.said}</span> → {s.target}
            </>
          )}
        </p>
        <p className="truncate text-xs font-bold text-ink/65">
          {s.context ? `"${s.context}"` : s.promptLine ? `after "${s.promptLine}"` : ""} · {label[s.type]}
          {s.isNew ? "" : " · again"}
        </p>
      </div>
    </li>
  );
}

function goalHeadline(sceneId: string): string {
  switch (sceneId) {
    case "cafe":
      return "You got your coffee.";
    case "pharmacie":
      return "Headache sorted.";
    case "apartment":
      return "You got the rent and the date.";
    case "bill":
      return "That charge is gone.";
    case "doctor":
      return "Diagnosis received.";
    case "interview":
      return "Three questions, answered.";
    default:
      return "Scene cleared.";
  }
}

function Missing({ title, body, requestId }: { title: string; body: string; requestId?: string | null }) {
  return (
    <div className="flex flex-1 flex-col justify-end px-5 pb-8" data-scene="review">
      <h1 className="text-3xl font-extrabold tracking-tight">{title}</h1>
      <p className="mt-2 text-ink-2">{body}</p>
      {requestId ? <p className="mt-1 text-xs text-ink-2">ref {requestId}</p> : null}
      <PillButton href="/" className="mt-6">
        Back to Today
      </PillButton>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-1 flex-col" data-scene="cafe">
      <div className="bg-scene px-5 pt-14 pb-5">
        <div className="h-3 w-20 rounded-full bg-ink/15" />
        <div className="mt-3 h-8 w-3/4 rounded-md bg-ink/15" />
        <div className="mt-2 h-3 w-1/2 rounded-full bg-ink/15" />
      </div>
      <div className="space-y-3 px-5 pt-4">
        <div className="h-9 rounded-xl bg-ink/8" />
        <div className="h-9 rounded-xl bg-ink/8" />
        <div className="h-9 rounded-xl bg-ink/8" />
      </div>
    </div>
  );
}
