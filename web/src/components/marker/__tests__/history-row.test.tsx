import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { HistoryRow } from "../history-row";
import type { HistoryRowItem } from "../history-row";

// next/link works fine in jsdom with Next.js test setup

const BASE_ITEM: HistoryRowItem = {
  id: "1",
  status: "graded",
  marks: 4,
  max_marks: 6,
  delta: 2,
  question_preview: "Integrate x^2",
  topic: "integration_basics",
  created_at: "2026-07-10T10:00:00Z",
};

describe("HistoryRow", () => {
  it("Graded row shows Check icon with aria-label 'Graded'", () => {
    render(<HistoryRow item={BASE_ITEM} />);
    expect(screen.getByLabelText("Graded")).toBeInTheDocument();
  });

  it("Graded row does not show AlertTriangle or Clock icons", () => {
    render(<HistoryRow item={BASE_ITEM} />);
    expect(screen.queryByLabelText("Extraction failed")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Pending")).not.toBeInTheDocument();
  });

  it("Error row shows AlertTriangle icon with aria-label 'Extraction failed'", () => {
    render(
      <HistoryRow
        item={{
          ...BASE_ITEM,
          status: "error",
          marks: null,
          delta: null,
        }}
      />
    );
    expect(screen.getByLabelText("Extraction failed")).toBeInTheDocument();
  });

  it("Error row does not show Check icon", () => {
    render(
      <HistoryRow
        item={{
          ...BASE_ITEM,
          status: "error",
          marks: null,
          delta: null,
        }}
      />
    );
    expect(screen.queryByLabelText("Graded")).not.toBeInTheDocument();
  });

  it("Pending row shows Clock icon with aria-label 'Pending'", () => {
    render(
      <HistoryRow
        item={{
          ...BASE_ITEM,
          status: "pending",
          marks: null,
          delta: null,
        }}
      />
    );
    expect(screen.getByLabelText("Pending")).toBeInTheDocument();
  });

  it("Graded row renders marks score", () => {
    render(<HistoryRow item={BASE_ITEM} />);
    expect(screen.getByText("4/6")).toBeInTheDocument();
  });

  it("Graded row renders positive delta pill", () => {
    render(<HistoryRow item={BASE_ITEM} />);
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("question preview is truncated at 80 chars with ellipsis", () => {
    const longPreview = "A".repeat(100);
    render(
      <HistoryRow item={{ ...BASE_ITEM, question_preview: longPreview }} />
    );
    // Should show 80 chars + ellipsis character
    expect(screen.getByText("A".repeat(80) + "…")).toBeInTheDocument();
  });

  it("row renders as a link to /mark/{id}", () => {
    render(<HistoryRow item={BASE_ITEM} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/mark/1");
  });

  it("topic badge renders with formatted topic name", () => {
    render(<HistoryRow item={BASE_ITEM} />);
    expect(screen.getByText("integration basics")).toBeInTheDocument();
  });
});
