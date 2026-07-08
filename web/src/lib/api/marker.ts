import { apiFetch } from "@/lib/api";
import type {
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
  getNextQuestion: (topic?: string) => {
    const q = topic ? `?topic=${encodeURIComponent(topic)}` : "";
    return apiFetch<QuestionCandidate>(`/marker/next-question${q}`);
  },
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
};
