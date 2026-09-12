import type { SceneColor } from "@/types/api";

const COLORS: readonly SceneColor[] = ["cafe", "pharmacie", "apartment", "bill", "doctor", "interview"];

/**
 * A scene's colour is its id (the six scenes are code, on both sides). Knowing it from the URL
 * means the scene screen wears the right colour from its first frame, not café yellow until the
 * session arrives.
 */
export function sceneColor(sceneId: string): SceneColor {
  return (COLORS as readonly string[]).includes(sceneId) ? (sceneId as SceneColor) : "cafe";
}
