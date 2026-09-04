import { api } from "@/store/api";
import type { DeckDto, PlacementDto, ProgressDto, TutorBriefDto } from "@/types/api";

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
    // Onboarding: twenty seconds of anything. Multipart `audio` or `text`.
    placement: build.mutation<PlacementDto, FormData>({
      query: (form) => ({ url: "/placement", method: "POST", body: form }),
      invalidatesTags: ["Today", "Card", "Progress"],
    }),
  }),
});

export const { useGetProgressQuery, useGetDeckQuery, useGetTutorBriefQuery, usePlacementMutation } =
  progressApi;
