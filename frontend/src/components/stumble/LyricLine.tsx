export type WordState = "on" | "off" | "miss";

export interface LyricWord {
  text: string;
  state: WordState;
}

const large: Record<WordState, string> = { on: "lyr-on", off: "lyr-off", miss: "lyr-miss" };
const small: Record<WordState, string> = { on: "lyr-on", off: "lyr-off-sm", miss: "lyr-miss-sm" };

/**
 * A line of words with fill states. `on` is filled ink, `off` is not yet produced, `miss` is a stumble.
 * `lg` (scene, review) uses outlines; `sm` (deck sheet) uses faded fill because outlines smear at small sizes.
 */
export function LyricLine({
  words,
  size = "lg",
  className = "",
}: {
  words: LyricWord[];
  size?: "lg" | "sm";
  className?: string;
}) {
  const map = size === "lg" ? large : small;
  const sizeCls = size === "lg" ? "text-[25px] leading-[1.15]" : "text-[18px] leading-[1.35]";
  return (
    <p className={`font-extrabold tracking-[-0.02em] ${sizeCls} ${className}`}>
      {words.map((w, i) => (
        <span key={`${i}-${w.text}`} className={map[w.state]}>
          {w.text}
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </p>
  );
}
