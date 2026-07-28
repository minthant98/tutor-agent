"use client";
import { useEffect, useState } from "react";
import posthog from "posthog-js";

export type StrideFlag =
  | "dashboard_v2"
  | "dashboard_v3"
  | "onboarding_v2"
  | "session_engine_v2"
  | "notifications_v2"
  | "account_v2"
  | "practice_v2"
  | "practice_v3"
  | "marker_v2"
  | "marker_v3"
  | "shell_v3"
  | "session_v3"
  | "topics_v3"
  | "progress_v3"
  | "account_v3"
  | "onboarding_v3";

const KNOWN_FLAGS: ReadonlyArray<StrideFlag> = [
  "dashboard_v2",
  "dashboard_v3",
  "onboarding_v2",
  "session_engine_v2",
  "notifications_v2",
  "account_v2",
  "practice_v2",
  "practice_v3",
  "marker_v2",
  "marker_v3",
  "shell_v3",
  "session_v3",
  "topics_v3",
  "progress_v3",
  "account_v3",
  "onboarding_v3",
];

export function useFeatureFlag(flag: StrideFlag, defaultValue = true): boolean {
  const [enabled, setEnabled] = useState<boolean>(defaultValue);

  useEffect(() => {
    if (!KNOWN_FLAGS.includes(flag)) return;
    const update = () => {
      const v = posthog.isFeatureEnabled(flag);
      setEnabled(v === undefined ? defaultValue : !!v);
    };
    update();
    posthog.onFeatureFlags(update);
  }, [flag, defaultValue]);

  return enabled;
}
