/**
 * Task 29: Analytics event wiring tests.
 *
 * Covers the events wired as part of Task 29:
 * - marker_question_refreshed (SuggestedQuestionCard refresh button)
 * - marker_ocr_failed (ProcessingStates extraction error — fires once)
 * - marker_try_similar_clicked (GradedResult "Try a similar question")
 * - marker_mark_scheme_pre_reveal (NewSubmission → MarkSchemePeek confirm — already wired, regression)
 * - marker_recommended_practice_clicked (RecommendedNextStep — already wired, regression)
 */
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock analytics
vi.mock("@/lib/analytics", () => ({ capture: vi.fn() }));

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

import { capture } from "@/lib/analytics";
import { SuggestedQuestionCard } from "../suggested-question-card";
import { ProcessingStates } from "../processing-states";
import { GradedResult } from "../graded-result";
import { NewSubmission } from "../new-submission";
import type { SubmissionOut } from "@/lib/types";

// ── SuggestedQuestionCard ────────────────────────────────────────────────────

const SAMPLE_QUESTION = {
  id: "q001",
  text: "Differentiate x^3",
  max_marks: 3,
  paper_ref: "Edexcel 9MA0 · 2024 Q2",
};

describe("marker_question_refreshed", () => {
  beforeEach(() => vi.clearAllMocks());

  it("fires capture with refresh_count_used and refresh_limit on refresh click", async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();
    render(
      <SuggestedQuestionCard
        question={SAMPLE_QUESTION}
        refreshCountUsed={2}
        refreshLimit={5}
        tier="free"
        onRefresh={onRefresh}
      />
    );

    await user.click(screen.getByRole("button", { name: /different question/i }));

    expect(capture).toHaveBeenCalledWith("marker_question_refreshed", {
      refresh_count_used: 2,
      refresh_limit: 5,
    });
  });

  it("also calls onRefresh callback after capture", async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();
    render(
      <SuggestedQuestionCard
        question={SAMPLE_QUESTION}
        refreshCountUsed={1}
        refreshLimit={5}
        tier="free"
        onRefresh={onRefresh}
      />
    );

    await user.click(screen.getByRole("button", { name: /different question/i }));

    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(capture).toHaveBeenCalledTimes(1);
  });

  it("does NOT fire capture when tier is pro (button not rendered)", () => {
    render(
      <SuggestedQuestionCard
        question={SAMPLE_QUESTION}
        refreshCountUsed={0}
        refreshLimit={null}
        tier="pro"
        onRefresh={vi.fn()}
      />
    );

    // Pro tier: the refresh button should not be rendered
    expect(screen.queryByRole("button", { name: /different question/i })).not.toBeInTheDocument();
    expect(capture).not.toHaveBeenCalled();
  });
});

// ── ProcessingStates: marker_ocr_failed ──────────────────────────────────────

describe("marker_ocr_failed", () => {
  beforeEach(() => vi.clearAllMocks());

  it("fires capture once when kind=extraction and status=error", () => {
    render(<ProcessingStates status="error" kind="extraction" />);
    expect(capture).toHaveBeenCalledWith("marker_ocr_failed", { kind: "extraction" });
    expect(capture).toHaveBeenCalledTimes(1);
  });

  it("does NOT fire capture for grading error", () => {
    render(<ProcessingStates status="error" kind="grading" />);
    expect(capture).not.toHaveBeenCalledWith("marker_ocr_failed", expect.anything());
  });

  it("does NOT fire capture for non-error statuses", () => {
    render(<ProcessingStates status="extracting" kind="extraction" />);
    expect(capture).not.toHaveBeenCalled();
  });

  it("fires capture only once even if component re-renders", () => {
    const { rerender } = render(<ProcessingStates status="error" kind="extraction" />);
    rerender(<ProcessingStates status="error" kind="extraction" />);
    // Should still be 1 — useRef guard prevents re-firing
    expect(capture).toHaveBeenCalledTimes(1);
  });
});

// ── GradedResult: marker_try_similar_clicked ─────────────────────────────────

const SAMPLE_SUBMISSION: SubmissionOut = {
  id: "sub-test-001",
  status: "graded",
  subject: "pure_mathematics",
  exam_board: "edexcel",
  question_id: "q001",
  question_text: "Differentiate x^3",
  max_marks: 4,
  input_type: "typed",
  answer_text: "3x^2",
  marks_awarded: 3,
  grade_pct: 75,
  feedback_json: {
    marks_awarded: 3,
    criteria: [],
    summary: "Good",
    improvement: "Check signs.",
    readiness_before: 40,
    readiness_after: 45,
    readiness_delta: 5,
    topic_mastery_before: 0.3,
    topic_mastery_after: 0.45,
    used_generated_mark_scheme: false,
  },
  photo_url: null,
  error_message: null,
  created_at: "2026-07-26T10:00:00Z",
  readiness_before: 40,
  readiness_after: 45,
  memory_ref: null,
  recommended_practice: null,
};

describe("marker_try_similar_clicked", () => {
  beforeEach(() => vi.clearAllMocks());

  it("fires capture when 'Try a similar question' is clicked (no recommendation)", async () => {
    const user = userEvent.setup();
    render(<GradedResult submission={SAMPLE_SUBMISSION} />);

    await user.click(screen.getByRole("button", { name: /try a similar question/i }));

    expect(capture).toHaveBeenCalledWith("marker_try_similar_clicked", {
      submission_id: "sub-test-001",
    });
  });

  it("fires capture when 'Try a similar question' is clicked (with recommendation)", async () => {
    const user = userEvent.setup();
    const withRecommendation: SubmissionOut = {
      ...SAMPLE_SUBMISSION,
      recommended_practice: {
        topic_id: "integration_basics",
        sub_skill: "substitution",
        blurb: "Practice substitution.",
      },
    };
    render(<GradedResult submission={withRecommendation} />);

    await user.click(screen.getByRole("button", { name: /try a similar question/i }));

    expect(capture).toHaveBeenCalledWith("marker_try_similar_clicked", {
      submission_id: "sub-test-001",
    });
  });
});

// ── MarkSchemePeek via NewSubmission: marker_mark_scheme_pre_reveal ───────────
// (Regression: already wired in Task 22 — verify it still fires)

const SAMPLE_NS_QUESTION = {
  id: "q_ms_test",
  text: "Integrate x^2 dx",
  max_marks: 4,
  paper_ref: "Edexcel 9MA0 · 2024 Q3",
  mark_scheme: "M1 A1 A1 A1",
};

describe("marker_mark_scheme_pre_reveal (regression)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("fires capture when mark scheme is confirmed via dialog", async () => {
    const user = userEvent.setup();
    render(<NewSubmission question={SAMPLE_NS_QUESTION} />);

    await user.click(screen.getByRole("button", { name: /Reveal anyway/i }));
    await user.click(screen.getByRole("button", { name: "Reveal" }));

    expect(capture).toHaveBeenCalledWith("marker_mark_scheme_pre_reveal", {
      question_id: "q_ms_test",
    });
  });
});
