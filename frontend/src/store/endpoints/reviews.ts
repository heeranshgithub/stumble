import { api } from "@/store/api";
import type { AttemptDto, DueNowDto, Grade, GradeResultDto, ReviewListDto } from "@/types/api";

export const reviewsApi = api.injectEndpoints({
  endpoints: (build) => ({
    getDueReviews: build.query<ReviewListDto, void>({
      query: () => "/reviews/due",
      providesTags: [{ type: "Card", id: "DUE" }],
    }),
    gradeCard: build.mutation<GradeResultDto, { id: string; rating: Grade }>({
      query: ({ id, rating }) => ({ url: `/reviews/${id}`, method: "POST", body: { rating } }),
      // The due list is walked locally during a review; Today and Progress refresh once it ends.
      invalidatesTags: ["Today", "Progress"],
    }),
    attemptCard: build.mutation<AttemptDto, { id: string; form: FormData }>({
      query: ({ id, form }) => ({ url: `/reviews/${id}/attempt`, method: "POST", body: form }),
    }),
    // Testing lever (profile screen only): make everything due now so the review can be exercised today.
    dueNow: build.mutation<DueNowDto, void>({
      query: () => ({ url: "/reviews/due-now", method: "POST" }),
      invalidatesTags: ["Today", "Card", "Progress"],
    }),
  }),
});

export const { useGetDueReviewsQuery, useGradeCardMutation, useAttemptCardMutation, useDueNowMutation } = reviewsApi;
