"use client";
import { ChevronDown, Check } from "lucide-react";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { cn } from "@/lib/utils";
import { useState } from "react";

export function SubjectSwitcher() {
  const { subject, subjects, setSubject } = useCurrentSubject();
  const [open, setOpen] = useState(false);

  const currentLabel =
    subjects.find((s) => s.id === subject)?.label ?? subjects[0]?.label ?? "";

  function handleSelect(id: string) {
    setSubject(id);
    setOpen(false);
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Change subject"
          aria-haspopup="listbox"
          aria-expanded={open}
          className="gap-1.5 max-w-[180px]"
        >
          <span className="truncate">{currentLabel}</span>
          <ChevronDown
            className={cn(
              "h-3.5 w-3.5 shrink-0 text-[var(--text-muted)] transition-transform duration-fast",
              open && "rotate-180"
            )}
            aria-hidden
          />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        className="w-52 p-1"
      >
        <ul role="listbox" aria-label="Subjects">
          {subjects.map((s) => (
            <li key={s.id}>
              <button
                className={cn(
                  "flex w-full items-center justify-between rounded-input px-3 py-2",
                  "font-sans text-[14px] text-[var(--text-primary)]",
                  "hover:bg-[var(--surface-1)] transition-colors duration-fast",
                  s.id === subject && "font-medium"
                )}
                aria-pressed={s.id === subject}
                onClick={() => handleSelect(s.id)}
              >
                {s.label}
                {s.id === subject && (
                  <Check className="h-3.5 w-3.5 text-[var(--primary)]" aria-hidden />
                )}
              </button>
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
