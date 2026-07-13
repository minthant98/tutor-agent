"use client";

type Band = "A*" | "A" | "B" | "C";

const BAND_TO_READINESS_IDX: Record<Band, number> = {
  "A*": 0,
  A: 1,
  B: 3,
  C: 4,
};

interface AlexNarrationProps {
  text: string;
  band: Band;
}

export function AlexNarration({ text, band }: AlexNarrationProps) {
  const idx = BAND_TO_READINESS_IDX[band] ?? 1;
  return (
    <div
      className="pl-4 font-sans text-[16px] text-[var(--text-primary)] leading-relaxed"
      style={{ borderLeft: `1px solid var(--readiness-${idx})` }}
    >
      {text}
    </div>
  );
}
