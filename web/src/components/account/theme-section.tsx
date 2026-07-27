"use client";

import { useTheme } from "@/lib/theme-provider";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

const THEME_OPTIONS = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "system", label: "System" },
] as const;

export function ThemeSection() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Theme
      </h2>

      <RadioGroup
        value={theme ?? "system"}
        onValueChange={setTheme}
        className="gap-3"
      >
        {THEME_OPTIONS.map(({ value, label }) => (
          <label
            key={value}
            className="flex items-center gap-3 cursor-pointer"
          >
            <RadioGroupItem value={value} id={`theme-${value}`} />
            <span className="text-[14px] text-[var(--text-primary)]">
              {label}
            </span>
          </label>
        ))}
      </RadioGroup>

      <p className="text-[12px] text-[var(--text-secondary)]">
        Theme applies immediately with no save required.
      </p>
    </div>
  );
}
