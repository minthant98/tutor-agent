/**
 * hasEquationPattern — returns true if the given text contains LaTeX-like
 * equation patterns such as superscripts (^), subscripts (_), backslash
 * commands (\frac, \sqrt, etc.), or other TeX notation.
 *
 * Used by Task 11 AnswerInput to switch to monospace input mode.
 */
export function hasEquationPattern(text: string): boolean {
  return /[\^_\\]|\\(?:frac|sqrt|int|sum|alpha|beta|gamma|delta|theta|pi|sigma|omega|infty|lim|log|sin|cos|tan)/.test(
    text
  );
}
