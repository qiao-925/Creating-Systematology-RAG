"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="text-center space-y-4 animate-in fade-in duration-300">
        <div className="flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10">
            <AlertTriangle className="h-7 w-7 text-destructive" />
          </div>
        </div>
        <h1 className="text-2xl font-semibold text-foreground">出错了</h1>
        <p className="text-sm text-muted-foreground max-w-sm">
          页面发生了意外错误。请点击下方按钮重试。
        </p>
        {error.digest && (
          <p className="text-xs text-muted-foreground/60 font-mono">
            ID: {error.digest}
          </p>
        )}
        <Button variant="outline" size="sm" onClick={reset} className="gap-2">
          <RotateCcw className="h-4 w-4" />
          重试
        </Button>
      </div>
    </div>
  );
}
