import { api } from "@/store/api";
import type { ProfileDto, TodayDto } from "@/types/api";

export const todayApi = api.injectEndpoints({
  endpoints: (build) => ({
    getToday: build.query<TodayDto, void>({
      query: () => "/today",
      providesTags: ["Today"],
    }),
    // Leaving the intro. Until this, Today sends a new device back to it.
    markOnboarded: build.mutation<ProfileDto, void>({
      query: () => ({ url: "/profiles/onboarded", method: "POST" }),
      invalidatesTags: ["Today"],
    }),
  }),
});

export const { useGetTodayQuery, useMarkOnboardedMutation } = todayApi;
