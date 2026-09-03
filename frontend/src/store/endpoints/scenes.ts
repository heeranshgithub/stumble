import { api } from "@/store/api";
import type { SceneDto } from "@/types/api";

export const scenesApi = api.injectEndpoints({
  endpoints: (build) => ({
    getScenes: build.query<SceneDto[], void>({
      query: () => "/scenes",
      providesTags: [{ type: "Scene", id: "LIST" }, "Today"],
    }),
  }),
});

export const { useGetScenesQuery } = scenesApi;
