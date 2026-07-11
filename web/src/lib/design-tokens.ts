export const tokens = {
  color: {
    primary: "#6268F2",
    primaryDark: "#7B7FF0",
    surface: {
      dark: { 0: "#0E0E11", 1: "#151519", 2: "#1C1C21", 3: "#1C1C21" },
      light: { 0: "#FCFCFD", 1: "#F8F8FA", 2: "#FFFFFF", 3: "#FFFFFF" },
    },
    border: {
      dark: "rgba(255, 255, 255, 0.06)",
      light: "rgba(0, 0, 0, 0.08)",
    },
    readiness: ["#5B7CE0", "#6268F2", "#A889F0", "#E8C070", "#F5A356"],
    semantic: {
      success: { text: "#8FB88C", bg: "rgba(143, 184, 140, 0.08)" },
      warning: { text: "#D4B26E", bg: "rgba(212, 178, 110, 0.08)" },
      danger:  { text: "#D48A8A", bg: "rgba(212, 138, 138, 0.08)" },
    },
    educational: {
      question: "#7B7FF0",
      answer: "#6268F2",
      hint: "#A889F0",
      markScheme: "#E8C070",
      teacherFeedback: "#8FB88C",
      alexFeedback: "#6268F2",
      readiness: "#6268F2",
    },
  },
  type: {
    scale: [11, 12, 14, 16, 20, 24, 32, 40] as const,
    family: {
      sans: "var(--font-geist-sans)",
      mono: "var(--font-geist-mono)",
    },
  },
  radius: { input: 8, button: 8, card: 10, dialog: 14 },
  motion: {
    duration: { fast: 120, base: 220, slow: 320 },
    ease: "cubic-bezier(.22, .61, .36, 1)",
  },
  spacing: { base: 4 },
} as const;

export type Tokens = typeof tokens;
