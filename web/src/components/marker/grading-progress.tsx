"use client";
export function GradingProgress({ status }: { status: "pending" | "extracting" | "grading" | "error" }) {
  const label =
    status === "extracting" ? "Reading your answer…" :
    status === "grading"    ? "Grading against the mark scheme…" :
    status === "error"      ? "Something went wrong" :
                              "Preparing…";
  const isError = status === "error";
  return (
    <section
      className={`rounded-lg border p-5 ${
        isError
          ? "border-red-200 bg-red-50"
          : "border-[var(--border)] bg-white"
      }`}
    >
      <div className="flex items-center gap-3">
        {!isError && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--blue)] border-t-transparent" />
        )}
        <p className={`text-sm ${isError ? "text-red-700" : "text-[var(--text-secondary)]"}`}>
          {label}
        </p>
      </div>
    </section>
  );
}
