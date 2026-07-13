"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface Segment {
  intent: string;
  topic: string;
  why: string;
  minutes: number;
  questions: number;
  sub_skills?: string[];
  learning_objective?: string;
}

interface SegmentCardsProps {
  segments: Segment[];
}

export function SegmentCards({ segments }: SegmentCardsProps) {
  return (
    <div className="flex gap-4">
      {segments.map((seg, i) => (
        <div
          key={i}
          className="flex-1 min-w-0 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-2)] p-4"
          style={{ width: "32%" }}
        >
          <Accordion type="single" collapsible>
            <AccordionItem value={`seg-${i}`} className="border-0">
              {/* Card summary — always visible */}
              <div className="mb-3">
                <span className="font-mono text-[11px] uppercase tracking-widest text-[var(--text-secondary)]">
                  {seg.intent}
                </span>
                <h3 className="font-sans text-[24px] font-semibold text-[var(--text-primary)] mt-1 leading-tight">
                  {seg.topic?.replace(/_/g, " ")}
                </h3>
                <p className="font-sans text-[14px] text-[var(--text-secondary)] mt-1 line-clamp-2">
                  {seg.why}
                </p>
                <p className="font-mono text-[12px] text-[var(--text-secondary)] mt-2">
                  {seg.minutes}m &middot; {seg.questions}q
                </p>
              </div>
              {/* Accordion trigger */}
              <AccordionTrigger className="text-[12px] text-[var(--text-secondary)] py-1 hover:no-underline">
                Details
              </AccordionTrigger>
              <AccordionContent className="pt-2">
                {seg.learning_objective && (
                  <p className="font-sans text-[13px] text-[var(--text-secondary)] mb-2">
                    {seg.learning_objective}
                  </p>
                )}
                {seg.sub_skills && seg.sub_skills.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {seg.sub_skills.map((skill) => (
                      <span
                        key={skill}
                        className="font-mono text-[11px] px-1.5 py-0.5 rounded border border-[var(--border-subtle)] text-[var(--text-secondary)]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      ))}
    </div>
  );
}
