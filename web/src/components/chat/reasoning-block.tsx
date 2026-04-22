"use client";

import { useState } from "react";
import { ChevronRight, Brain } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

interface Props {
  reasoning: string;
}

export function ReasoningBlock({ reasoning }: Props) {
  const [open, setOpen] = useState(false);

  if (!reasoning) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-2">
      <CollapsibleTrigger className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
        <ChevronRight
          className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-90" : ""}`}
        />
        <Brain className="h-3.5 w-3.5" />
        Reasoning
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1.5 rounded-md border border-border/50 bg-muted/20 p-3 text-xs text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-y-auto">
          {reasoning}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
