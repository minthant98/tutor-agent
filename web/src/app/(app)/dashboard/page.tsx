"use client";
import { useEffect, useState } from "react";
import { dashboardApi } from "@/lib/api/dashboard";
import { useFeatureFlag } from "@/lib/feature-flags";
import { useStudent } from "@/lib/auth";
import { LegacyDashboard } from "./_legacy";
import { SubjectSwitcher } from "@/components/dashboard/subject-switcher";
import { CountdownBand } from "@/components/dashboard/countdown-band";
import { ReadinessCard } from "@/components/dashboard/readiness-card";
import { ResumeSessionCard } from "@/components/dashboard/resume-session-card";
import { TodayFocusCard } from "@/components/dashboard/today-focus-card";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { TopicsList } from "@/components/dashboard/topics-list";
import { PracticeCard } from "@/components/dashboard/practice-card";
import { MarkMyWorkCard } from "@/components/marker/mark-my-work-card";
import { FeatureFlag } from "@/components/shell/feature-flag";
import type { DashboardPayload } from "@/lib/types";

export default function DashboardPage() {
  const v2 = useFeatureFlag("dashboard_v2", true);
  const student = useStudent();
  const [subject, setSubject] = useState("pure_mathematics");
  const [data, setData] = useState<DashboardPayload | null>(null);

  useEffect(() => {
    dashboardApi.get(subject).then(setData).catch(() => {});
  }, [subject]);

  if (!v2) return <LegacyDashboard />;

  if (!data) return <p className="p-6">Loading…</p>;

  const firstName = student?.name?.split(" ")[0] ?? "there";

  return (
    <div className="space-y-6 max-w-2xl mx-auto px-4 py-8">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Good morning, {firstName}.</h1>
        {(data.subject_options?.length ?? 0) > 1 && (
          <SubjectSwitcher
            current={subject}
            options={data.subject_options}
            onChange={setSubject}
          />
        )}
      </header>

      <CountdownBand data={data} />
      <ReadinessCard data={data} />

      {data.resume_session ? (
        <ResumeSessionCard data={data.resume_session} />
      ) : (
        <TodayFocusCard data={data.today_focus} />
      )}

      <FeatureFlag flag="practice_v2" fallback={null}>
        <PracticeCard subject={subject} />
      </FeatureFlag>

      <FeatureFlag flag="marker_v2" fallback={null}>
        <MarkMyWorkCard subject={subject} />
      </FeatureFlag>

      {data.recent_activity && <RecentActivity data={data.recent_activity} />}

      <TopicsList
        strong={data.strong_topics ?? []}
        weak={data.weak_topics ?? []}
        subject={subject}
      />
    </div>
  );
}
