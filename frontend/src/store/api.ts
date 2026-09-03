import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { getDeviceId } from "@/lib/device";
import { env } from "@/lib/env";

/** The app's entire HTTP layer. Feature endpoints attach with `injectEndpoints`, one file per domain. */
export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({
    baseUrl: env.NEXT_PUBLIC_API_BASE_URL,
    prepareHeaders: (headers) => {
      headers.set("X-Device-Id", getDeviceId());
      return headers;
    },
  }),
  tagTypes: ["Today", "Scene", "Card", "Session", "Progress"],
  endpoints: () => ({}),
});
