import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import type { SerializedError } from "@reduxjs/toolkit";

import type { ApiErrorEnvelope } from "@/types/api";

export interface ReadableError {
  message: string;
  code: string;
  requestId: string | null;
}

function isEnvelope(data: unknown): data is ApiErrorEnvelope {
  return (
    typeof data === "object" &&
    data !== null &&
    "error" in data &&
    typeof (data as { error: unknown }).error === "object"
  );
}

/** The one place that turns an RTK Query error into something a screen can show. */
export function getErrorMessage(error: FetchBaseQueryError | SerializedError | undefined): ReadableError {
  if (!error) return { message: "Something went wrong.", code: "unknown", requestId: null };

  if ("status" in error) {
    if (error.status === "FETCH_ERROR") {
      return { message: "Can't reach the server. Check your connection.", code: "fetch_error", requestId: null };
    }
    if (error.status === "TIMEOUT_ERROR") {
      return { message: "The server took too long to answer.", code: "timeout", requestId: null };
    }
    if (isEnvelope(error.data)) {
      const { code, message, details } = error.data.error;
      return { message, code, requestId: details.requestId ?? null };
    }
    return { message: `Request failed (${String(error.status)}).`, code: "http_error", requestId: null };
  }

  return { message: error.message ?? "Something went wrong.", code: error.code ?? "unknown", requestId: null };
}
