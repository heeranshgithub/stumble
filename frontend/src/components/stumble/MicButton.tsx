import { Mic } from "lucide-react";

export type MicState = "idle" | "holding" | "processing";

/** Visual only. The hold-to-talk hook attaches on day 2. */
export function MicButton({ state = "idle", className = "" }: { state?: MicState; className?: string }) {
  const ring =
    state === "holding"
      ? "shadow-[0_0_0_16px_color-mix(in_oklch,var(--color-stumble)_25%,transparent)] bg-stumble"
      : "shadow-[0_0_0_12px_color-mix(in_oklch,var(--color-ink)_12%,transparent)] bg-ink";
  return (
    <div
      aria-hidden="true"
      className={`mx-auto grid size-[84px] place-items-center rounded-pill text-paper transition-[background-color,box-shadow] duration-200 ease-out-expo ${ring} ${state === "processing" ? "opacity-60" : ""} ${className}`}
    >
      <Mic className="size-8" strokeWidth={2.25} />
    </div>
  );
}
