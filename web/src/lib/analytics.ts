/**
 * Minimal analytics capture wrapper.
 * Delegates to PostHog if it has been initialised (see lib/posthog.ts).
 */
export function capture(event: string, props: Record<string, unknown> = {}): void {
  if (typeof window !== "undefined" && (window as unknown as { posthog?: { capture: (e: string, p: Record<string, unknown>) => void } }).posthog) {
    (window as unknown as { posthog: { capture: (e: string, p: Record<string, unknown>) => void } }).posthog.capture(event, props);
  }
}
