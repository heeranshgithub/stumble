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
  reviewDue: number;
  nextScene: SceneDto | null;
  deck: DeckStatsDto;
}

export interface ProfileDto {
  id: string | null;
  deviceId: string;
  language: string;
  createdAt: string;
}

export type StumbleType = "freeze" | "code_switch" | "correction" | "miss";
export type Patience = "relaxed" | "normal" | "real";
export type TtsProvider = "elevenlabs" | "browser";

export interface StumbleDto {
  type: StumbleType;
  said: string;
  target: string;
  context: string;
  promptLine: string;
  confidence: number;
}

export interface WinDto {
  phrase: string;
  cardId: string | null;
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
  ttsProvider: TtsProvider;
  turns: TurnDto[];
}

export interface StartSessionRequest {
  sceneId: string;
  patience?: Patience;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: { requestId?: string } & Record<string, unknown>;
  };
}
