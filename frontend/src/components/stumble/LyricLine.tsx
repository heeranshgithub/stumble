export type WordState = "on" | "off" | "miss";

export interface LyricWord {
  text: string;
  state: WordState;
}

const large: Record<WordState, string> = { on: "lyr-on", off: "lyr-off", miss: "lyr-miss" };
const small: Record<WordState, string> = { on: "lyr-on", off: "lyr-off-sm", miss: "lyr-miss-sm" };

const STAGGER_MS = 55;

/**
 * A line of words with fill states. `on` is filled ink, `off` is not yet produced, `miss` is a stumble.
 * `lg` (scene, review) uses outlines; `sm` (deck sheet) uses faded fill because outlines smear at small sizes.
 * `animate` fills the words in one after another, the lyric moment, for a line that just landed.
 */
export function LyricLine({
  words,
  size = "lg",
  animate = false,
  className = "",
}: {
  words: LyricWord[];
  size?: "lg" | "sm";
  animate?: boolean;
  className?: string;
}) {
  const map = size === "lg" ? large : small;
  const sizeCls = size === "lg" ? "text-[25px] leading-[1.15]" : "text-[18px] leading-[1.35]";
  return (
    <p className={`font-extrabold tracking-[-0.02em] [overflow-wrap:anywhere] ${sizeCls} ${className}`}>
      {words.map((w, i) => (
        <span key={`${i}-${w.text}`}>
          <span
            className={`${map[w.state]} ${animate ? "lyr-word-in" : ""}`}
            style={animate ? { animationDelay: `${i * STAGGER_MS}ms` } : undefined}
          >
            {w.text}
          </span>
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </p>
  );
}
