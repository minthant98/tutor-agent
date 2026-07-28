import { apiFetch } from "@/lib/api";
import type {
  MarkerV3LandingData,
  QuestionCandidate,
  SubmissionCreateResponse,
  SubmissionOut,
} from "@/lib/types";

export interface CreateSubmissionBody {
  question_id: string;
  question_text: string;
  mark_scheme: string;
  max_marks: number;
  input_type: "photo" | "typed";
  answer_text?: string;
  photo_extension?: "jpg" | "jpeg" | "png" | "webp";
  used_generated_mark_scheme?: boolean;
}

export const markerApi = {
  getNextQuestion: () =>
    apiFetch<QuestionCandidate>("/marker/next-question"),
  createSubmission: (body: CreateSubmissionBody) =>
    apiFetch<SubmissionCreateResponse>("/marker/submissions", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  notifyUploaded: (submissionId: string) =>
    apiFetch<{ ok: boolean }>(`/marker/submissions/${submissionId}/uploaded`, {
      method: "POST",
    }),
  getSubmission: (submissionId: string) =>
    apiFetch<SubmissionOut>(`/marker/submissions/${submissionId}`),
  listSubmissions: (limit = 10, offset = 0) =>
    apiFetch<SubmissionOut[]>(`/marker/submissions?limit=${limit}&offset=${offset}`),
  listHistory: (params?: {
    status?: string;
    difficulty?: string;
    from?: string;
    to?: string;
    cursor?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.difficulty) qs.set("difficulty", params.difficulty);
    if (params?.from) qs.set("from", params.from);
    if (params?.to) qs.set("to", params.to);
    if (params?.cursor) qs.set("cursor", params.cursor);
    const query = qs.toString();
    return apiFetch<SubmissionOut[]>(`/marker/history${query ? `?${query}` : ""}`);
  },
  getV3Landing: (subject = "pure_mathematics", nocache = false) =>
    apiFetch<MarkerV3LandingData>(
      `/marker/v3/landing?subject=${subject}${nocache ? "&nocache=true" : ""}`
    ),
};
