import { api } from "@/store/api";
import type { DebriefDto, SessionDto, StartSessionRequest } from "@/types/api";

export const sessionsApi = api.injectEndpoints({
  endpoints: (build) => ({
    startSession: build.mutation<SessionDto, StartSessionRequest>({
      query: (body) => ({ url: "/sessions", method: "POST", body }),
      invalidatesTags: [{ type: "Session", id: "LIST" }],
    }),
    getSession: build.query<SessionDto, string>({
      query: (id) => `/sessions/${id}`,
      providesTags: (_r, _e, id) => [{ type: "Session", id }],
    }),
    // Multipart: `audio` (Blob) or `text`, plus `clientPauseMs`. Returns the whole session.
    sendTurn: build.mutation<SessionDto, { id: string; form: FormData }>({
      query: ({ id, form }) => ({ url: `/sessions/${id}/turns`, method: "POST", body: form }),
      async onQueryStarted({ id }, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        dispatch(sessionsApi.util.upsertQueryData("getSession", id, data));
      },
    }),
    // Idempotent: ends the scene, turns stumbles into cards. Today and Progress change as a result.
    finishSession: build.mutation<DebriefDto, string>({
      query: (id) => ({ url: `/sessions/${id}/finish`, method: "POST" }),
      invalidatesTags: (_r, _e, id) => [
        { type: "Session", id },
        "Today",
        "Card",
        "Progress",
      ],
    }),
  }),
});

export const {
  useStartSessionMutation,
  useGetSessionQuery,
  useSendTurnMutation,
  useFinishSessionMutation,
} = sessionsApi;
