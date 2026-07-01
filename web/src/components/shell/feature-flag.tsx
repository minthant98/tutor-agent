"use client";
import { ReactNode } from "react";
import { useFeatureFlag, StrideFlag } from "@/lib/feature-flags";

interface Props {
  flag: StrideFlag;
  fallback?: ReactNode;
  children: ReactNode;
}

export function FeatureFlag({ flag, fallback = null, children }: Props) {
  const enabled = useFeatureFlag(flag, true);
  return <>{enabled ? children : fallback}</>;
}
