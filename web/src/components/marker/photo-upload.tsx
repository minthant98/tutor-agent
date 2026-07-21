"use client";

import { useRef, useState, useCallback, DragEvent, ChangeEvent } from "react";
import { uploadFile } from "@/hooks/use-signed-upload";

const MAX_FILES = 4;

interface FileEntry {
  id: string;
  file: File;
  preview: string;
  status: "idle" | "uploading" | "done" | "error";
  path?: string;
}

export interface PhotoUploadProps {
  onSubmit: (paths: string[]) => void;
}

export function PhotoUpload({ onSubmit }: PhotoUploadProps) {
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Helpers ────────────────────────────────────────────────────────────────

  const addFiles = useCallback((files: File[]) => {
    setEntries((prev) => {
      const remaining = MAX_FILES - prev.length;
      if (remaining <= 0) return prev;
      const toAdd = files.slice(0, remaining).map((f) => ({
        id: `${Date.now()}-${Math.random()}`,
        file: f,
        preview: URL.createObjectURL(f),
        status: "idle" as const,
      }));
      return [...prev, ...toAdd];
    });
  }, []);

  const removeEntry = useCallback((id: string) => {
    setEntries((prev) => {
      const entry = prev.find((e) => e.id === id);
      if (entry) URL.revokeObjectURL(entry.preview);
      return prev.filter((e) => e.id !== id);
    });
  }, []);

  const moveUp = useCallback((index: number) => {
    if (index === 0) return;
    setEntries((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next;
    });
  }, []);

  const moveDown = useCallback((index: number) => {
    setEntries((prev) => {
      if (index >= prev.length - 1) return prev;
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next;
    });
  }, []);

  // ── Drag + drop ────────────────────────────────────────────────────────────

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files).filter((f) =>
        f.type.startsWith("image/")
      );
      addFiles(files);
    },
    [addFiles]
  );

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragOver(false), []);

  // ── File input ────────────────────────────────────────────────────────────

  const handleInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      addFiles(files);
      // Reset so the same file can be re-selected
      e.target.value = "";
    },
    [addFiles]
  );

  // ── Upload & submit ────────────────────────────────────────────────────────

  const handleSubmit = useCallback(async () => {
    const paths: string[] = [];

    for (const entry of entries) {
      setEntries((prev) =>
        prev.map((e) =>
          e.id === entry.id ? { ...e, status: "uploading" } : e
        )
      );
      try {
        const path = await uploadFile(entry.file);
        paths.push(path);
        setEntries((prev) =>
          prev.map((e) =>
            e.id === entry.id ? { ...e, status: "done", path } : e
          )
        );
      } catch {
        setEntries((prev) =>
          prev.map((e) =>
            e.id === entry.id ? { ...e, status: "error" } : e
          )
        );
        return; // abort on first error
      }
    }

    onSubmit(paths);
  }, [entries, onSubmit]);

  // ── Render ────────────────────────────────────────────────────────────────

  const hasFiles = entries.length > 0;
  const isUploading = entries.some((e) => e.status === "uploading");

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        role="region"
        aria-label="Photo drop zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={[
          "relative flex flex-col items-center justify-center cursor-pointer",
          "w-full md:w-[480px] h-[280px]",
          "rounded-card border border-dashed border-border-subtle",
          "transition-colors duration-150",
          dragOver
            ? "bg-surface-2 border-[var(--color-primary)]"
            : "bg-surface-1 hover:bg-surface-2",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          capture
          aria-label="Upload photos"
          className="sr-only"
          onChange={handleInputChange}
          disabled={entries.length >= MAX_FILES}
        />
        <div className="flex flex-col items-center gap-2 pointer-events-none select-none">
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            className="text-[var(--text-secondary)]"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p className="text-14 text-[var(--text-secondary)]">
            {entries.length >= MAX_FILES
              ? "Maximum 4 photos reached"
              : "Drop photos here or click to browse"}
          </p>
          <p className="text-11 text-[var(--text-tertiary)]">
            JPEG, PNG, WebP · up to 4 pages
          </p>
        </div>
      </div>

      {/* Thumbnails */}
      {hasFiles && (
        <div className="flex flex-wrap gap-3" role="list" aria-label="Pages">
          {entries.map((entry, index) => (
            <div
              key={entry.id}
              role="listitem"
              className="relative flex flex-col items-center gap-1"
            >
              {/* Thumbnail */}
              <div className="relative w-24 h-24 rounded-md overflow-hidden border border-border-subtle bg-surface-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={entry.preview}
                  alt={`Page ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                {/* Upload progress pulse */}
                {entry.status === "uploading" && (
                  <div className="absolute inset-0 bg-black/40 animate-pulse flex items-center justify-center">
                    <span className="sr-only">Uploading…</span>
                  </div>
                )}
                {/* Error overlay */}
                {entry.status === "error" && (
                  <div className="absolute inset-0 bg-red-500/40 flex items-center justify-center">
                    <span className="text-white text-10 font-medium">Error</span>
                  </div>
                )}
                {/* Remove button */}
                <button
                  type="button"
                  aria-label={`Remove page ${index + 1}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    removeEntry(entry.id);
                  }}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-black/80 transition-colors text-10 leading-none"
                >
                  ✕
                </button>
              </div>

              {/* Page label */}
              <span className="font-mono text-[11px] text-[var(--text-secondary)]">
                Page {index + 1}
              </span>

              {/* Reorder chevrons */}
              <div className="flex gap-1">
                <button
                  type="button"
                  aria-label={`Move page ${index + 1} up`}
                  onClick={() => moveUp(index)}
                  disabled={index === 0}
                  className="w-5 h-5 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 flex items-center justify-center text-10"
                >
                  ‹
                </button>
                <button
                  type="button"
                  aria-label={`Move page ${index + 1} down`}
                  onClick={() => moveDown(index)}
                  disabled={index === entries.length - 1}
                  className="w-5 h-5 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 flex items-center justify-center text-10"
                >
                  ›
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Submit */}
      {hasFiles && (
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isUploading || entries.length === 0}
          className="mt-2 px-5 py-2.5 rounded-md bg-[var(--color-primary)] text-white text-14 font-medium disabled:opacity-50 transition-opacity"
        >
          {isUploading
            ? "Uploading…"
            : `Submit ${entries.length} page${entries.length !== 1 ? "s" : ""}`}
        </button>
      )}
    </div>
  );
}
