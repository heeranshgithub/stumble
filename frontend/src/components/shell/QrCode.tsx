"use client";

import QR from "qrcode";
import { useEffect, useRef, useSyncExternalStore } from "react";

const noop = () => () => undefined;
const readOrigin = () => window.location.origin;
const serverOrigin = () => "";

/** A QR code of the page the viewer is on, so a desktop judge can open it on their phone. */
export function QrCode({ size = 132 }: { size?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // Browser-only value with an SSR fallback, without a setState-in-effect.
  const url = useSyncExternalStore(noop, readOrigin, serverOrigin);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !url) return;
    void QR.toCanvas(canvas, url, {
      width: size,
      margin: 0,
      color: { dark: "#1a1233", light: "#ffffff" },
      errorCorrectionLevel: "M",
    });
  }, [url, size]);

  return (
    <figure className="m-0">
      <div className="inline-block rounded-2xl bg-paper p-3">
        <canvas ref={canvasRef} width={size} height={size} className="block" aria-label={`QR code for ${url}`} />
      </div>
      <figcaption className="mt-2 max-w-[220px] truncate text-xs text-paper-2">{url}</figcaption>
    </figure>
  );
}
