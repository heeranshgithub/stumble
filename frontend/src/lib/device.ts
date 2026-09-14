const KEY = "stumble.device";
const PREV_KEY = "stumble.device.prev";

/** The seeded five-day profile, so a first-time visitor can see a lived-in deck. */
export const SAMPLE_DEVICE = "demo-maya";

/** Kept only for the case where localStorage throws (private mode, blocked site data). */
let memo = "";

function readLS(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeLS(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Storage blocked: the id lives for this page only.
  }
}

/**
 * No accounts: the device id is the identity, minted once and kept in localStorage.
 * `?device=<id>` adopts that id for this browser and remembers the one it replaced,
 * so you can always get back. Every id is a fully separate profile server-side.
 */
export function getDeviceId(): string {
  if (typeof window === "undefined") return "";
  const fromUrl = new URLSearchParams(window.location.search).get("device")?.trim();
  if (fromUrl) {
    const current = readLS(KEY);
    if (current && current !== fromUrl) writeLS(PREV_KEY, current);
    writeLS(KEY, fromUrl);
    memo = fromUrl;
    return fromUrl;
  }
  const stored = readLS(KEY);
  if (stored) return stored;
  if (memo) return memo;
  memo = crypto.randomUUID();
  writeLS(KEY, memo);
  return memo;
}

/** Reads the current id without minting one. For UI that only displays it. */
export function peekDeviceId(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("device")?.trim() || readLS(KEY) || "";
}

/** The id this browser was on before the last `?device=` switch, if it's still a different one. */
export function previousDeviceId(): string {
  if (typeof window === "undefined") return "";
  const prev = readLS(PREV_KEY) ?? "";
  return prev && prev !== peekDeviceId() ? prev : "";
}

/**
 * Switching reloads the page on purpose: every cached query, and the audio element, belong to
 * the identity being left behind.
 */
export function switchDevice(id: string, path = "/"): void {
  const trimmed = id.trim();
  if (!trimmed) return;
  // A hard navigation is the point: router.push() would keep the RTK Query cache and the unlocked
  // audio element, both of which belong to the identity being left behind. And a replace, not an
  // assign: the profile screen belongs to that identity too, so it must not sit under the new
  // one's history, where the first scene's back button would find it.
  window.location.replace(`${path}?device=${encodeURIComponent(trimmed)}`);
}

export function freshDeviceId(): string {
  return crypto.randomUUID();
}
