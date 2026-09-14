import { api } from "@/store/api";
import type { DeckDto, ProgressDto, TutorBriefDto } from "@/types/api";

export const progressApi = api.injectEndpoints({
  endpoints: (build) => ({
    getProgress: build.query<ProgressDto, void>({
      query: () => "/progress",
      providesTags: ["Progress"],
    }),
    getDeck: build.query<DeckDto, void>({
      query: () => "/deck",
      providesTags: [{ type: "Card", id: "LIST" }, "Progress"],
    }),
    getTutorBrief: build.query<TutorBriefDto, void>({
      query: () => "/tutor-brief",
      providesTags: ["Progress"],
    }),
  }),
});

export const { useGetProgressQuery, useGetDeckQuery, useGetTutorBriefQuery } =
  progressApi;
