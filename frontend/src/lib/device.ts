const KEY = "stumble.device";

/**
 * No accounts: the device id is the identity, minted once and kept in localStorage.
 * `?device=<id>` in the URL adopts that id for this browser (used to open the seeded demo profile).
 */
export function getDeviceId(): string {
  if (typeof window === "undefined") return "";
  try {
    const fromUrl = new URLSearchParams(window.location.search).get("device");
    if (fromUrl) {
      window.localStorage.setItem(KEY, fromUrl);
      return fromUrl;
    }
    let id = window.localStorage.getItem(KEY);
    if (!id) {
      id = crypto.randomUUID();
      window.localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    // Storage blocked (private mode, strict settings): a per-page identity is better than none.
    return "no-storage";
  }
}
