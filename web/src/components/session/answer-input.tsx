"use client";

import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { hasEquationPattern } from "@/lib/detect-equation";
import { cn } from "@/lib/utils";

export function AnswerInput({
  onSubmit,
}: {
  onSubmit: (text: string) => void;
}) {
  const [value, setValue] = useState("");
  const mono = hasEquationPattern(value);

  return (
    <div className="space-y-2">
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            onSubmit(value);
          }
        }}
        placeholder="Type your answer, showing working…"
        className={cn("min-h-[120px] text-16 font-sans", mono && "font-mono")}
      />
      {value === "" && (
        <p className="text-12 text-white/50">
          Show working. Alex marks method as well as answer.
        </p>
      )}
    </div>
  );
}
