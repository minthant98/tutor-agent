"use client";

interface AlexNarrationProps {
  text: string;
  /** 0-4 color index from the API's band_color_index field.
   *  0 = Cool Blue, 1 = Indigo, 2 = Lavender, 3 = Soft Gold, 4 = Amber. */
  bandColorIndex: number;
}

export function AlexNarration({ text, bandColorIndex }: AlexNarrationProps) {
  // Clamp to valid range in case the API returns an unexpected value
  const idx = Math.min(4, Math.max(0, bandColorIndex));
  return (
    <div
      className="pl-4 font-sans text-[16px] text-[var(--text-primary)] leading-relaxed"
      style={{ borderLeft: `1px solid var(--readiness-${idx})` }}
    >
      {text}
    </div>
  );
}
