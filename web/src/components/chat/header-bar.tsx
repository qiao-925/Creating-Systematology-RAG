"use client";

import { RotateCcw, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { useChatStore } from "@/stores/chat-store";
import type { AppMode } from "@/types";

interface Props {
  onSettingsClick?: () => void;
  mode?: AppMode;
  onModeChange?: (mode: AppMode) => void;
}

const modes: { key: AppMode; label: string }[] = [
  { key: "chat", label: "Chat" },
  { key: "research", label: "Research" },
  { key: "cldflow", label: "CLDFlow" },
];

export function HeaderBar({ onSettingsClick, mode = "chat", onModeChange }: Props) {
  const resetChat = useChatStore((s) => s.resetChat);
  const hasMessages = useChatStore((s) => s.messages.length > 0);

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border/40 bg-background/90 backdrop-blur-md px-6 py-3">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-semibold tracking-tight text-foreground/90">
          Creating Systematology
        </h2>
        {onModeChange && (
          <nav className="flex items-center gap-0.5 rounded-md bg-muted p-0.5">
            {modes.map((m) => (
              <button
                key={m.key}
                onClick={() => onModeChange(m.key)}
                className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                  mode === m.key
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {m.label}
              </button>
            ))}
          </nav>
        )}
      </div>
      <div className="flex items-center gap-0.5">
        {hasMessages && mode !== "cldflow" && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={resetChat}
            title="Reset conversation"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        )}
        <ThemeToggle />
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-foreground"
          onClick={onSettingsClick}
          title="Settings"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
