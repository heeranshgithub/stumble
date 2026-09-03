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

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: { requestId?: string } & Record<string, unknown>;
  };
}
