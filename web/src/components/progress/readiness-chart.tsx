"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { tokens } from "@/lib/design-tokens";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Skeleton } from "@/components/ui/skeleton";

export interface ChartSeries {
  date: string;       // YYYY-MM-DD
  readiness: number;  // 0..100
}

interface ReadinessChartProps {
  series: ChartSeries[];
  days?: 30 | 90;
  onDaysChange?: (days: 30 | 90) => void;
  loading?: boolean;
}

// Gradient stops from tokens.color.readiness — Cool Blue → Amber.
// NO GREEN. The 5 stops map linearly left-to-right across the line.
const READINESS_STOPS = tokens.color.readiness;

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const readiness = payload[0].value;
  return (
    <div className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-2)] px-3 py-2 shadow-md">
      <p className="font-sans text-[11px] text-[var(--text-secondary)]">{label}</p>
      <p className="font-mono text-[16px] font-semibold text-[var(--text-primary)]">
        {readiness}%
      </p>
    </div>
  );
}

export function ReadinessChart({
  series,
  days = 30,
  onDaysChange,
  loading = false,
}: ReadinessChartProps) {
  // ── Empty state ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-[280px] w-full" />
      </div>
    );
  }

  if (series.length === 0) {
    return (
      <div className="flex h-[320px] flex-col items-center justify-center gap-3 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)]">
        <p className="font-sans text-[14px] text-[var(--text-secondary)] text-center px-4">
          Your readiness graph will fill in after a few sessions.
        </p>
      </div>
    );
  }

  // ── Trim labels: show only first, last, and today ─────────────────────────
  const firstDate = series[0]?.date ?? "";
  const lastDate = series[series.length - 1]?.date ?? "";

  const tickFormatter = (value: string) => {
    if (value === firstDate || value === lastDate) {
      // Format as "Jun 10"
      try {
        return new Date(value + "T00:00:00").toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
        });
      } catch {
        return value;
      }
    }
    return "";
  };

  return (
    <div className="space-y-3">
      {/* 30/90-day toggle */}
      <div className="flex justify-end">
        <ToggleGroup
          type="single"
          value={String(days)}
          onValueChange={(v) => {
            if (v === "30" || v === "90") onDaysChange?.(Number(v) as 30 | 90);
          }}
        >
          <ToggleGroupItem value="30" aria-label="30 days">
            30d
          </ToggleGroupItem>
          <ToggleGroupItem value="90" aria-label="90 days">
            90d
          </ToggleGroupItem>
        </ToggleGroup>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            {/* Horizontal gradient for the line — Cool Blue → Amber */}
            <linearGradient id="readiness-line" x1="0" y1="0" x2="1" y2="0">
              {READINESS_STOPS.map((color, i) => (
                <stop
                  key={i}
                  offset={`${(i / (READINESS_STOPS.length - 1)) * 100}%`}
                  stopColor={color}
                />
              ))}
            </linearGradient>
            {/* Vertical gradient for the area fill */}
            <linearGradient id="readiness-fill" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor={READINESS_STOPS[1]}
                stopOpacity={0.24}
              />
              <stop
                offset="100%"
                stopColor={READINESS_STOPS[1]}
                stopOpacity={0.02}
              />
            </linearGradient>
          </defs>

          <XAxis
            dataKey="date"
            tickFormatter={tickFormatter}
            tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tickCount={3}
            tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={32}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="readiness"
            stroke="url(#readiness-line)"
            strokeWidth={2}
            fill="url(#readiness-fill)"
            dot={false}
            activeDot={{
              r: 4,
              fill: READINESS_STOPS[1],
              stroke: "var(--surface-2)",
              strokeWidth: 2,
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
