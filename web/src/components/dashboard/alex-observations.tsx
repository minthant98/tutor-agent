"use client";

import { useObservations } from "@/hooks/use-observations";

interface AlexObservationsProps {
  subject: string;
}

/**
 * Renders up to 3 bullet-point observations from Alex about this week.
 * Returns null (renders nothing) when the list is empty, loading, or errored.
 */
export function AlexObservations({ subject }: AlexObservationsProps) {
  const { observations, isLoading, error } = useObservations(subject);

  if (isLoading || error || observations.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <p className="font-sans text-[14px] text-white/60">
        What Alex noticed this week
      </p>
      <ul className="space-y-3">
        {observations.slice(0, 3).map((obs) => (
          <li
            key={obs.id}
            className="font-sans text-[14px] text-white/80 flex gap-2"
          >
            <span className="shrink-0 text-white/40">•</span>
            <span>{obs.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
