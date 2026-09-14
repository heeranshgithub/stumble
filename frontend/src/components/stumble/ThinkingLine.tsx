"use client";

import { useEffect, useState } from "react";

interface Beat {
  fr: string;
  en: string;
}

/** What the character is doing while the reply is on its way. Short French, glossed, so the wait teaches too.
 * Never hesitating or searching for words: that's the learner's part, and the one the app catches. */
const SHARED: Beat[] = [
  { fr: "réfléchit", en: "is thinking" },
  { fr: "sourit", en: "smiles" },
  { fr: "hoche la tête", en: "nods" },
  { fr: "vous regarde", en: "looks at you" },
];

const BY_SCENE: Record<string, Beat[]> = {
  cafe: [
    { fr: "essuie le comptoir", en: "wipes the counter" },
    { fr: "fait mousser le lait", en: "froths the milk" },
    { fr: "range les tasses", en: "puts the cups away" },
  ],
  pharmacie: [
    { fr: "regarde l'étagère", en: "looks at the shelf" },
    { fr: "cherche dans le tiroir", en: "looks in the drawer" },
  ],
  apartment: [
    { fr: "ouvre les volets", en: "opens the shutters" },
    { fr: "regarde ses notes", en: "checks her notes" },
  ],
  bill: [
    { fr: "tape sur son clavier", en: "types on the keyboard" },
    { fr: "consulte votre dossier", en: "looks up your file" },
  ],
  doctor: [
    { fr: "note quelque chose", en: "writes something down" },
    { fr: "regarde le dossier", en: "looks at the file" },
  ],
  interview: [
    { fr: "prend des notes", en: "takes notes" },
    { fr: "relit votre CV", en: "rereads your CV" },
  ],
};

const ROTATE_MS = 1600;

function pick(beats: Beat[], avoid: Beat | null): Beat {
  const pool =
    beats.length > 1 && avoid ? beats.filter((b) => b !== avoid) : beats;
  return pool[Math.floor(Math.random() * pool.length)] as Beat;
}

/**
 * The wait for a reply: "Léa essuie le comptoir… · wipes the counter". A new beat every second or so,
 * never the same one twice in a row, each landing word by word like a turn.
 */
export function ThinkingLine({ name, sceneId }: { name: string; sceneId: string }) {
  const beats = [...SHARED, ...(BY_SCENE[sceneId] ?? [])];
  const [beat, setBeat] = useState<Beat>(() => pick(beats, null));
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setBeat((prev) => pick(beats, prev));
      setTick((n) => n + 1);
    }, ROTATE_MS);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the pool only changes with the scene
  }, [sceneId]);

  const words = `${name} ${beat.fr}…`.split(" ");
  return (
    <p className="text-xs font-bold text-ink-2" role="status" aria-live="polite">
      {words.map((w, i) => (
        <span key={`${tick}-${i}`}>
          {/* the space sits outside the animated span: inline-block swallows it inside */}
          <span className="lyr-word-in" style={{ animationDelay: `${i * 55}ms` }}>
            {w}
          </span>{" "}
        </span>
      ))}
      <span key={`${tick}-en`} className="lyr-word-in opacity-60" style={{ animationDelay: `${words.length * 55}ms` }}>
        · {beat.en}
      </span>
    </p>
  );
}
