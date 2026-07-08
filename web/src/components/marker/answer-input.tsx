"use client";
import { useRef, useState } from "react";

type Mode = "typed" | "photo";
type AllowedExt = "jpg" | "jpeg" | "png" | "webp";

export interface AnswerInputProps {
  onSubmit: (input:
    | { type: "typed"; text: string }
    | { type: "photo"; file: File; extension: string }
  ) => void | Promise<void>;
  submitting: boolean;
}

const MAX_PHOTO_BYTES = 10 * 1024 * 1024;
const ALLOWED_EXTS: ReadonlyArray<AllowedExt> = ["jpg", "jpeg", "png", "webp"];

function isAllowedExt(ext: string): ext is AllowedExt {
  return ALLOWED_EXTS.includes(ext as AllowedExt);
}

export function AnswerInput({ onSubmit, submitting }: AnswerInputProps) {
  const [mode, setMode] = useState<Mode>("typed");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const pickFile = (f: File) => {
    setError(null);
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    if (!isAllowedExt(ext)) {
      setError("Only JPG, PNG, or WebP images are supported.");
      return;
    }
    if (f.size > MAX_PHOTO_BYTES) {
      setError("Photo must be under 10 MB — try a smaller version");
      return;
    }
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  };

  const clearFile = () => {
    setFile(null);
    setPreviewUrl(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const disabled = submitting || (mode === "typed" ? text.trim().length === 0 : !file);

  const handleSubmit = () => {
    if (mode === "typed") {
      onSubmit({ type: "typed", text: text.trim() });
    } else if (file) {
      const ext = file.name.split(".").pop()?.toLowerCase() ?? "jpg";
      onSubmit({ type: "photo", file, extension: ext });
    }
  };

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <div className="mb-3 flex gap-2">
        <button
          onClick={() => setMode("typed")}
          className={`rounded-md px-3 py-1.5 text-sm ${
            mode === "typed"
              ? "bg-[var(--blue)] text-white"
              : "border border-[var(--border)] hover:bg-gray-50"
          }`}
        >
          Type answer
        </button>
        <button
          onClick={() => setMode("photo")}
          className={`rounded-md px-3 py-1.5 text-sm ${
            mode === "photo"
              ? "bg-[var(--blue)] text-white"
              : "border border-[var(--border)] hover:bg-gray-50"
          }`}
        >
          Upload photo
        </button>
      </div>

      {mode === "typed" && (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Write your working here…"
          className="min-h-32 w-full rounded-md border border-[var(--border)] p-3 text-sm"
        />
      )}

      {mode === "photo" && (
        <div>
          {!previewUrl && (
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) pickFile(f);
              }}
            />
          )}
          {previewUrl && (
            <div className="flex flex-col gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="preview"
                className="max-h-64 rounded-md border border-[var(--border)]"
              />
              <button
                onClick={clearFile}
                className="self-start rounded-md border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                Retake
              </button>
            </div>
          )}
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={disabled}
        className="mt-4 rounded-lg bg-[var(--blue)] px-4 py-2 text-white disabled:opacity-50"
      >
        {submitting ? "Submitting…" : "Submit for marking"}
      </button>
    </section>
  );
}
