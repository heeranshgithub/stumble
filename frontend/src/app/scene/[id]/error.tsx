"use client";

import { PillButton } from "@/components/stumble/PillButton";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex flex-1 flex-col justify-end px-5 pb-8 pt-14" data-scene="review">
      <h1 className="text-3xl font-extrabold tracking-tight">The scene broke.</h1>
      <p className="mt-2 text-ink-2">{error.message || "Something went wrong mid-conversation."}</p>
      <PillButton className="mt-6" onClick={reset}>
        Try again
      </PillButton>
      <PillButton href="/" variant="paper" className="mt-2">
        Back to Today
      </PillButton>
    </div>
  );
}
