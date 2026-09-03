type Tone = "ink" | "stumble" | "muted";

const styles: Record<Tone, string> = {
  ink: "bg-ink text-paper",
  stumble: "bg-stumble text-paper",
  muted: "bg-ink/12 text-ink",
};

/** A small fact: "caught · coffee → café", "you froze here · 4s", "Léa · 2:14". */
export function Chip({
  tone = "muted",
  className = "",
  children,
}: {
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-pill px-2.5 py-1 text-[11px] font-extrabold leading-none ${styles[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
