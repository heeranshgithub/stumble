import { api } from "@/store/api";
import type { ReadyDto } from "@/types/api";

export const healthApi = api.injectEndpoints({
  endpoints: (build) => ({
    getReady: build.query<ReadyDto, void>({
      query: () => "/ready",
    }),
  }),
});

export const { useGetReadyQuery } = healthApi;
