export function SegmentProgress({ plan, currentIdx }: { plan: any[]; currentIdx: number }) {
  return (
    <ol className="flex items-center gap-2">
      {plan.map((s, i) => (
        <li key={s.idx} className="flex items-center gap-2">
          <span className={`grid h-5 w-5 place-items-center rounded-full text-[10px]
            ${i < currentIdx ? "bg-[var(--blue)] text-white"
              : i === currentIdx ? "border-2 border-[var(--blue)]"
              : "border border-gray-300"}`}>
            {i < currentIdx ? "✓" : i + 1}
          </span>
          <span className="text-xs text-[var(--text-secondary)]">{s.intent}</span>
          {i < plan.length - 1 && <span className="text-gray-300">·</span>}
        </li>
      ))}
    </ol>
  );
}
