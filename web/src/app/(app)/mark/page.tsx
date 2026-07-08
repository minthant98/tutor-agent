"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { markerApi } from "@/lib/api/marker";
import { dashboardApi } from "@/lib/api/dashboard";
import type { QuestionCandidate, SubmissionOut } from "@/lib/types";
import { QuestionCard } from "@/components/marker/question-card";
import { AnswerInput } from "@/components/marker/answer-input";
import { GradingProgress } from "@/components/marker/grading-progress";
import { ResultsView } from "@/components/marker/results-view";
import { useFeatureFlag } from "@/lib/feature-flags";

type View = "loading" | "answering" | "grading" | "results" | "error";

export default function MarkPage() {
  const router = useRouter();
  const markerEnabled = useFeatureFlag("marker_v2", true);
  const [view, setView] = useState<View>("loading");
  const [question, setQuestion] = useState<QuestionCandidate | null>(null);
  const [submission, setSubmission] = useState<SubmissionOut | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [dashboardMeta, setDashboardMeta] = useState<{
    exam_date: string | null;
    days_until_exam: number | null;
    predicted_grade: string | null;
  } | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!markerEnabled) {
      router.replace("/dashboard");
    }
  }, [markerEnabled, router]);

  const loadQuestion = useCallback(async () => {
    setView("loading");
    try {
      const q = await markerApi.getNextQuestion();
      setQuestion(q);
      setView("answering");
    } catch {
      setView("error");
    }
  }, []);

  useEffect(() => {
    loadQuestion();
    dashboardApi.get("pure_mathematics")
      .then((d) =>
        setDashboardMeta({
          exam_date: d.exam_date,
          days_until_exam: d.days_until_exam,
          predicted_grade: d.predicted_grade,
        })
      )
      .catch(() => {});
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [loadQuestion]);

  const submit = async (input:
    | { type: "typed"; text: string }
    | { type: "photo"; file: File; extension: string }
  ) => {
    if (!question) return;
    setSubmitting(true);
    try {
      if (input.type === "typed") {
        const res = await markerApi.createSubmission({
          question_id: question.question_id,
          question_text: question.question_text,
          mark_scheme: question.mark_scheme,
          max_marks: question.max_marks,
          input_type: "typed",
          answer_text: input.text,
          used_generated_mark_scheme: question.used_generated_mark_scheme,
        });
        await markerApi.notifyUploaded(res.submission_id);
        startPolling(res.submission_id);
      } else {
        const ext = input.extension as "jpg" | "jpeg" | "png" | "webp";
        const res = await markerApi.createSubmission({
          question_id: question.question_id,
          question_text: question.question_text,
          mark_scheme: question.mark_scheme,
          max_marks: question.max_marks,
          input_type: "photo",
          photo_extension: ext,
          used_generated_mark_scheme: question.used_generated_mark_scheme,
        });
        await fetch(res.upload_url!, {
          method: "PUT",
          headers: { "Content-Type": input.file.type },
          body: input.file,
        });
        await markerApi.notifyUploaded(res.submission_id);
        startPolling(res.submission_id);
      }
    } catch {
      setView("error");
    } finally {
      setSubmitting(false);
    }
  };

  const startPolling = (id: string) => {
    setView("grading");
    pollRef.current = setInterval(async () => {
      try {
        const s = await markerApi.getSubmission(id);
        setSubmission(s);
        if (s.status === "graded") {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setView("results");
        } else if (s.status === "error") {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setView("error");
        }
      } catch {
        clearInterval(pollRef.current!);
        pollRef.current = null;
        setView("error");
      }
    }, 1000);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <h1 className="text-xl font-semibold">Mark my work</h1>

      {view === "loading" && <p>Loading question…</p>}

      {(view === "answering" || view === "grading" || view === "results") && question && (
        <QuestionCard question={question} />
      )}

      {view === "answering" && (
        <AnswerInput onSubmit={submit} submitting={submitting} />
      )}

      {view === "grading" && submission && (
        <GradingProgress status={submission.status as "pending" | "extracting" | "grading" | "error"} />
      )}

      {view === "results" && submission && (
        <ResultsView
          submission={submission}
          examDate={dashboardMeta?.exam_date}
          predictedGrade={dashboardMeta?.predicted_grade}
          daysUntilExam={dashboardMeta?.days_until_exam}
          onMarkAnother={() => {
            setSubmission(null);
            loadQuestion();
          }}
          onDashboard={() => router.push("/dashboard")}
        />
      )}

      {view === "error" && (
        <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Something went wrong.{" "}
          <button
            className="underline"
            onClick={() => loadQuestion()}
          >
            Try again
          </button>.
        </section>
      )}
    </div>
  );
}
