"use client";

import { PillButton } from "@/components/stumble/PillButton";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex flex-1 flex-col justify-end px-5 pb-8 pt-14" data-scene="review">
      <h1 className="text-3xl font-extrabold tracking-tight">Something broke.</h1>
      <p className="mt-2 text-ink-2">{error.message || "An unexpected error happened on this screen."}</p>
      {error.digest ? <p className="mt-1 text-xs text-ink-2">ref {error.digest}</p> : null}
      <PillButton className="mt-6" onClick={reset}>
        Try again
      </PillButton>
    </div>
  );
}
