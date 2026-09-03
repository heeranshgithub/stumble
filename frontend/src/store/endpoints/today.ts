import { api } from "@/store/api";
import type { TodayDto } from "@/types/api";

export const todayApi = api.injectEndpoints({
  endpoints: (build) => ({
    getToday: build.query<TodayDto, void>({
      query: () => "/today",
      providesTags: ["Today"],
    }),
  }),
});

export const { useGetTodayQuery } = todayApi;
