"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Combobox } from "@/components/ui/combobox";
import { ModeCard } from "./mode-card";
import { DrillResumeCard } from "./drill-resume-card";
import { practiceApi } from "@/lib/api/practice";
import type { PracticeLandingData, DrillResumeData } from "@/lib/api/practice";

export interface TopicOption {
  id: string;
  label: string;
}

interface PracticeLandingProps {
  data: PracticeLandingData;
  /** Topics available for the Drill-In picker.
   *  TODO(task-17): wire this to GET /practice/topics once the hook is ready.
   *  Pass [] to disable the picker (Start button stays disabled). */
  topics: TopicOption[];
}

export function PracticeLanding({ data, topics }: PracticeLandingProps) {
  const router = useRouter();
  const [drillTopic, setDrillTopic] = useState<string | null>(null);
  const [drillResume, setDrillResume] = useState<DrillResumeData | null>(null);

  const comboboxOptions = topics.map((t) => ({ value: t.id, label: t.label }));

  // Fetch resume data when a drill topic is selected
  useEffect(() => {
    if (!drillTopic) {
      setDrillResume(null);
      return;
    }
    practiceApi.getDrillResume(drillTopic).then((res) => {
      setDrillResume(res ?? null);
    }).catch(() => setDrillResume(null));
  }, [drillTopic]);

  return (
    <div className="max-w-[1120px] mx-auto pt-12 px-6 space-y-8">
      {/* Alex narration — left border in readiness-2 color */}
      <div className="text-[14px] text-white/70 border-l-2 border-[var(--readiness-2)] pl-3">
        {data.narration}
      </div>

      {/* Header question */}
      <h1 className="text-[32px] font-sans">How do you want to practice today?</h1>

      {/* Three mode cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Quick Practice */}
        <ModeCard
          testId="mode-card-quick-practice"
          mode="Quick Practice"
          header='"I have ten minutes."'
          description="A short session across recent weak areas."
          meta="~10 min · 5 questions"
          outcome="Best when time is limited — keeps readiness stable."
          impact="Expected readiness · stable"
          action={
            <Button
              variant="primary"
              onClick={() => router.push("/practice/plan?mode=quick_practice")}
            >
              Start
            </Button>
          }
        />

        {/* Weak Areas */}
        <ModeCard
          testId="mode-card-weak-areas"
          mode="Weak Areas"
          header='"I want to improve."'
          description="Focused work on the topics slipping this week."
          meta="~15 min · dynamic length"
          outcome="Best for pushing readiness up — targets highest-impact weakness."
          impact="Expected readiness · +2% (est.)"
          extraContent={
            data.weak_topics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {data.weak_topics.slice(0, 2).map((t) => (
                  <Badge key={t.id} variant="secondary">
                    {t.label}
                  </Badge>
                ))}
              </div>
            ) : undefined
          }
          action={
            <Button
              variant="primary"
              onClick={() => router.push("/practice/plan?mode=weak_areas")}
            >
              Start
            </Button>
          }
        />

        {/* Drill-In */}
        <ModeCard
          testId="mode-card-drill-in"
          mode="Drill-In"
          header='"I keep getting this wrong."'
          description="Deep-focus on one topic — you choose."
          meta={drillTopic ? "~12 min · targeted" : "Choose a topic"}
          outcome="Best when one concept won't stick — mastery over breadth."
          impact="Expected mastery · +1 band on this topic"
          metaSlot={
            <Combobox
              options={comboboxOptions}
              value={drillTopic ?? undefined}
              onValueChange={(val) => setDrillTopic(val || null)}
              placeholder="Search topics…"
              searchPlaceholder="Search topics…"
              emptyMessage="No topics found."
            />
          }
          extraContent={
            drillResume ? (
              <DrillResumeCard
                data={drillResume}
                onResume={(sessionId) => router.push(`/session/${sessionId}`)}
                onStartOver={() =>
                  router.push(`/practice/plan?mode=drill_in&topic=${drillTopic}`)
                }
              />
            ) : undefined
          }
          action={
            <Button
              variant="primary"
              disabled={!drillTopic}
              onClick={() =>
                router.push(`/practice/plan?mode=drill_in&topic=${drillTopic}`)
              }
            >
              Start
            </Button>
          }
        />
      </div>
    </div>
  );
}
