import type { SceneColor } from "@/types/api";

export type BlobColor = SceneColor | "review" | "scene" | "paper" | "ink";

const bg: Record<BlobColor, string> = {
  cafe: "bg-cafe text-ink",
  pharmacie: "bg-pharmacie text-ink",
  apartment: "bg-apartment text-ink",
  bill: "bg-bill text-ink",
  doctor: "bg-doctor text-ink",
  interview: "bg-interview text-ink",
  review: "bg-review text-ink",
  scene: "bg-scene text-ink",
  paper: "bg-paper text-ink",
  ink: "bg-ink text-paper",
};

/** An edge-to-edge block of color. No radius, no border, no shadow: the color is the container. */
export function Blob({
  color = "scene",
  className = "",
  children,
}: {
  color?: BlobColor;
  className?: string;
  children: React.ReactNode;
}) {
  return <section className={`px-5 py-4 ${bg[color]} ${className}`}>{children}</section>;
}
