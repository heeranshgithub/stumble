import { ArrowRight } from "lucide-react";

import { SAMPLE_DEVICE, switchDevice } from "@/lib/device";

/** Through switchDevice, so the id being left is remembered and "Back to mine" has somewhere to go. */
const open = (e: React.MouseEvent) => {
  e.preventDefault();
  switchDevice(SAMPLE_DEVICE);
};

/**
 * Shown only where a screen is genuinely empty. A first-time visitor can look at a profile with a
 * week of history rather than three blank screens, then come back to their own.
 *
 * A link that does a full page load: `?device=` is read once, at startup.
 */
export function SampleLink({ className = "" }: { className?: string }) {
  return (
    <a
      href={`/?device=${SAMPLE_DEVICE}`}
      onClick={open}
      className={`inline-flex items-center gap-1.5 text-xs font-extrabold text-ink/65 underline-offset-2 hover:underline ${className}`}
    >
      See a week in
      <ArrowRight className="size-3.5" strokeWidth={2.5} />
    </a>
  );
}

/**
 * The same route as a full-width button, for the one place it has to be found: Today right after a
 * first scene, when the review, the intervals and the payoff are all a day away and a first-time
 * visitor (a judge) would otherwise leave. A plain anchor for the same reason as above.
 */
export function SampleButton({ className = "" }: { className?: string }) {
  return (
    <a
      href={`/?device=${SAMPLE_DEVICE}`}
      onClick={open}
      className={`inline-flex w-full items-center justify-center gap-2 rounded-pill border border-ink/15 bg-paper px-5 py-3.5 text-[15px] font-extrabold text-ink transition-transform duration-150 ease-out-expo active:scale-[0.98] ${className}`}
    >
      See a week in · sample profile
      <ArrowRight className="size-4" strokeWidth={2.5} />
    </a>
  );
}
