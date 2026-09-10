import { ArrowRight } from "lucide-react";

import { SAMPLE_DEVICE } from "@/lib/device";

/**
 * Shown only where a screen is genuinely empty. A first-time visitor can look at a profile with a
 * week of history rather than three blank screens, then come back to their own.
 *
 * A plain link, so it's a full page load: `?device=` is read once, at startup.
 */
export function SampleLink({ className = "" }: { className?: string }) {
  return (
    <a
      href={`/?device=${SAMPLE_DEVICE}`}
      className={`inline-flex items-center gap-1.5 text-xs font-extrabold text-ink/65 underline-offset-2 hover:underline ${className}`}
    >
      See a week in
      <ArrowRight className="size-3.5" strokeWidth={2.5} />
    </a>
  );
}
