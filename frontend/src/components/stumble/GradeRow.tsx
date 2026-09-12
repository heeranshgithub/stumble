"use client";

export type Grade = "again" | "hard" | "good" | "easy";

export interface GradeIntervals {
  again: string;
  hard: string;
  good: string;
  easy: string;
}

const order: Grade[] = ["again", "hard", "good", "easy"];
const label: Record<Grade, string> = { again: "Again", hard: "Hard", good: "Good", easy: "Easy" };
const tone: Record<Grade, string> = {
  again: "bg-paper text-stumble",
  hard: "bg-paper text-[#c98a00]",
  good: "bg-pharmacie text-ink",
  easy: "bg-paper text-[#2b7fd0]",
};

/** The four FSRS grades as circles. Good is filled; it's the one most people should press. */
export function GradeRow({
  intervals,
  onGrade,
  disabled = false,
}: {
  intervals: GradeIntervals;
  onGrade: (grade: Grade) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {order.map((g) => (
        <button
          key={g}
          type="button"
          disabled={disabled}
          onClick={() => onGrade(g)}
          className={`flex aspect-square flex-col items-center justify-center rounded-pill text-[12.5px] font-extrabold transition-transform duration-150 ease-out-expo active:scale-95 disabled:opacity-50 ${tone[g]}`}
        >
          {label[g]}
          {/* Again's interval is the same "1d" as Hard's on a first review (FSRS never schedules
              sooner than a day), so a date says nothing. What Again does is reset the card. */}
          <span className="text-[10px] font-bold opacity-60">{g === "again" ? "forgot" : intervals[g]}</span>
        </button>
      ))}
    </div>
  );
}
