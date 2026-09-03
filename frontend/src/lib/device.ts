const KEY = "stumble.device";

/**
 * No accounts. The device id is the identity, minted once per browser and sent on every request.
 * Returns "" during server rendering; every data hook runs on the client.
 */
export function getDeviceId(): string {
  if (typeof window === "undefined") return "";
  try {
    const existing = window.localStorage.getItem(KEY);
    if (existing) return existing;
    const fresh = crypto.randomUUID();
    window.localStorage.setItem(KEY, fresh);
    return fresh;
  } catch {
    // Private mode or blocked storage: a per-session id still lets the app work.
    return sessionId();
  }
}

let memo = "";
function sessionId(): string {
  if (!memo) memo = crypto.randomUUID();
  return memo;
}
