/**
 * When a card enters the review, in the learner's words. One rule for every screen, and the same
 * rule the server uses to decide what's due: a card is "due now" once its due time is within the
 * next eight hours (so "tomorrow" means the next sitting, not exactly 24 h later).
 */
export const DUE_WINDOW_MS = 8 * 3_600_000;

export function whenDue(due: string | number | Date, now = Date.now()): string {
  const t = new Date(due).getTime();
  const ms = t - now;
  if (ms <= DUE_WINDOW_MS) return "due now";
  const d = new Date(t);
  const today = new Date(now);
  const sameDay = d.toDateString() === today.toDateString();
  if (sameDay) return d.getHours() >= 17 ? "tonight" : "later today";
  const tomorrow = new Date(now + 86_400_000);
  if (d.toDateString() === tomorrow.toDateString()) return "tomorrow";
  const days = Math.round(ms / 86_400_000);
  return `in ${days} days`;
}
