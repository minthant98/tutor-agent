"use client";

import { useRef, useCallback } from "react";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

interface MarkSchemeAccordionProps {
  scheme: string;
  firstNotAwardedRef: string | null;
}

export function MarkSchemeAccordion({ scheme, firstNotAwardedRef }: MarkSchemeAccordionProps) {
  const contentRef = useRef<HTMLPreElement>(null);

  const handleOpenChange = useCallback(
    (value: string) => {
      // value is the open item value, or "" when closed
      if (!value) return;
      if (!firstNotAwardedRef) return; // no auto-scroll when null

      // Use setTimeout(0) so DOM is settled after Radix animation frame
      setTimeout(() => {
        const pre = contentRef.current;
        if (!pre) return;

        // Walk text nodes to find the first occurrence of the criterion code
        const walker = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT);
        let found = false;
        let node: Node | null = walker.nextNode();
        while (node) {
          if (node.textContent && node.textContent.includes(firstNotAwardedRef)) {
            const parent = node.parentElement ?? pre;
            parent.scrollIntoView({ behavior: "smooth", block: "start" });
            found = true;
            break;
          }
          node = walker.nextNode();
        }
        if (!found) {
          // Fallback: scroll to top of content
          pre.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 0);
    },
    [firstNotAwardedRef]
  );

  return (
    <Accordion type="single" collapsible onValueChange={handleOpenChange}>
      <AccordionItem value="mark-scheme">
        <AccordionTrigger className="text-[14px] font-sans">
          Mark scheme
        </AccordionTrigger>
        <AccordionContent>
          <pre
            ref={contentRef}
            className="whitespace-pre-wrap font-mono text-[var(--color-mark-scheme)] text-[13px] leading-relaxed"
          >
            {scheme}
          </pre>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
