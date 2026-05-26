"use client";

import { ArrowLeft, Settings, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

interface Props {
  onSettingsClick?: () => void;
  /** Show question title instead of "Systematology" */
  questionTitle?: string;
  /** Status indicator — "running" | "completed" | "idle" */
  status?: "running" | "completed" | "idle";
  /** New conversation callback */
  onNewConversation?: () => void;
  /** Back button callback */
  onBack?: () => void;
}

export function HeaderBar({ onSettingsClick, questionTitle, status, onNewConversation, onBack }: Props) {
  const statusDot =
    status === "running"
      ? "bg-primary animate-pulse"
      : status === "completed"
        ? "bg-positive"
        : "bg-muted-foreground/40";

  const statusLabel =
    status === "running" ? "分析中" : status === "completed" ? "分析完成" : "";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border/40 bg-background px-6">
      <div className="flex items-center gap-3 min-w-0">
        {onBack && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground -ml-2"
            onClick={onBack}
            title="返回首页"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
        )}
        <div className="flex h-6 w-6 items-center justify-center rounded bg-foreground shrink-0">
          <Layers className="h-3.5 w-3.5 text-background" />
        </div>
        {questionTitle ? (
          <h2 className="text-sm font-semibold tracking-tight text-foreground truncate">
            {questionTitle}
          </h2>
        ) : (
          <h2 className="text-sm font-semibold tracking-tight text-foreground">
            Systematology
          </h2>
        )}
      </div>
      <div className="flex items-center gap-3">
        {status && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={`h-2 w-2 rounded-full shrink-0 ${statusDot}`} />
            <span>{statusLabel}</span>
          </div>
        )}
        <div className="flex items-center gap-0.5">
          {onNewConversation && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs text-muted-foreground"
              onClick={onNewConversation}
            >
              + 新对话
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
      </div>
    </header>
  );
}
