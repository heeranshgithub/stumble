/**
 * Wire types. camelCase, mirroring the backend DTOs one for one.
 * Adding a field means editing the Pydantic model and this file in the same commit.
 */

export type SceneColor = "cafe" | "pharmacie" | "apartment" | "bill" | "doctor" | "interview";

export type SceneStatus = "cleared" | "next" | "locked";

export interface SceneDto {
  id: string;
  title: string;
  color: SceneColor;
  goal: string;
  characterName: string;
  characterRole: string;
  order: number;
  status: SceneStatus;
  usesDueCards: string[];
}

export interface DeckStatsDto {
  caught: number;
  mastered: number;
  due: number;
}

export interface TodayDto {
  dayNumber: number;
  onboarded: boolean;
  reviewDue: number;
  sceneUnlocked: boolean;
  nextScene: SceneDto | null;
  deck: DeckStatsDto;
}

export type Grade = "again" | "hard" | "good" | "easy";

export interface IntervalsDto {
  again: string;
  hard: string;
  good: string;
  easy: string;
}

export interface ReviewCardDto {
  id: string | null;
  sceneId: string;
  sceneTitle: string;
  sceneColor: SceneColor | "review";
  characterName: string;
  type: StumbleType;
  said: string;
  target: string;
  context: string;
  promptLine: string;
  /** English of the line the learner answered, and of their sentence with the slot fixed. */
  promptLineEn: string | null;
  contextEn: string | null;
  due: string;
  reps: number;
  lapses: number;
  intervals: IntervalsDto;
  audioUrl: string;
}

export interface ReviewListDto {
  cards: ReviewCardDto[];
  totalDue: number;
}

export interface GradeResultDto {
  cardId: string;
  rating: Grade;
  due: string;
  interval: string;
  remainingDue: number;
}

export interface AttemptDto {
  heard: string;
  matched: boolean;
}

export interface ProfileDto {
  id: string | null;
  deviceId: string;
  language: string;
  createdAt: string;
  onboarded: boolean;
  level: string | null;
}

export type WordState = "on" | "off" | "miss";

export interface SeriesPointDto {
  date: string;
  caught: number;
  mastered: number;
  struggling: number;
}

export interface UnderPressureDto {
  target: string;
  type: StumbleType;
  lapses: number;
  producedIn: string[];
}

export interface ProgressDto {
  caught: number;
  mastered: number;
  due: number;
  scenesCleared: number;
  sessions: number;
  minutesSpoken: number;
  series: SeriesPointDto[];
  underPressure: UnderPressureDto[];
}

export interface DeckCardDto {
  id: string;
  target: string;
  state: WordState;
  type: StumbleType;
  sceneId: string;
  sceneTitle: string;
  context: string;
  due: string;
  lapses: number;
  produced: number;
}

export interface DeckDto {
  cards: DeckCardDto[];
  caught: number;
  mastered: number;
  due: number;
}

export interface BriefPatternDto {
  title: string;
  detail: string;
  count: number;
}

export interface TutorBriefDto {
  weekLabel: string;
  generatedAt: string;
  cardsAnalysed: number;
  scenesPlayed: number;
  patterns: BriefPatternDto[];
  strengths: string[];
  suggestedSession: string[];
  asText: string;
}

export interface PlacementDto {
  level: "A1" | "A2" | "B1";
  heard: string;
  note: string;
  stumbles: StumbleDto[];
  cardsAdded: number;
}

export type StumbleType = "freeze" | "code_switch" | "correction" | "miss";
export type Patience = "relaxed" | "normal" | "real";

export interface StumbleDto {
  type: StumbleType;
  said: string;
  target: string;
  context: string;
  promptLine: string;
  confidence: number;
  /** The target, spoken. */
  audioUrl: string | null;
}

export interface WinDto {
  phrase: string;
  cardId: string | null;
  /** The phrase, spoken. */
  audioUrl: string | null;
}

export interface TurnDto {
  id: string;
  role: "character" | "learner";
  text: string;
  textEn: string | null;
  stumbles: StumbleDto[];
  wins: WinDto[];
  goalProgress: number;
  audioUrl: string | null;
  pauseMs: number;
  createdAt: string;
}

export interface SessionDto {
  id: string | null;
  sceneId: string;
  sceneTitle: string;
  sceneColor: SceneColor;
  characterName: string;
  characterRole: string;
  goal: string;
  patience: Patience;
  goalProgress: number;
  done: boolean;
  turns: TurnDto[];
}

/** GET /ready: what the backend process is actually running on. */
export interface ReadyDto {
  status: string;
  providers: "real" | "fake";
  stt: string;
  llm: string;
  tts: string;
}

/** POST /reviews/due-now: a testing lever that pulls every unmastered card's due date to now. */
export interface DueNowDto {
  cards: number;
}

export interface StartSessionRequest {
  sceneId: string;
  patience?: Patience;
}

export interface CardDto {
  id: string | null;
  sceneId: string;
  type: StumbleType;
  said: string;
  target: string;
  context: string;
  promptLine: string;
  due: string;
  reps: number;
  lapses: number;
  produced: number;
  mastered: boolean;
  createdAt: string;
}

export interface DebriefStumbleDto extends StumbleDto {
  cardId: string;
  isNew: boolean;
}

export interface DebriefDto {
  sessionId: string;
  sceneId: string;
  sceneTitle: string;
  sceneColor: SceneColor;
  characterName: string;
  goal: string;
  goalReached: boolean;
  goalProgress: number;
  durationS: number;
  turnsSpoken: number;
  stumbles: DebriefStumbleDto[];
  wins: WinDto[];
  cardsAdded: number;
  cardsRelapsed: number;
  nextReviewAt: string | null;
  deck: DeckStatsDto;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: { requestId?: string } & Record<string, unknown>;
  };
}
