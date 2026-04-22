"use client";

import { useState, useRef, useCallback } from "react";
import { ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  variant?: "docked" | "inline";
  autoFocus?: boolean;
}

export function ChatInput({ onSend, disabled, placeholder = "输入问题...", variant = "docked", autoFocus = false }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const isDocked = variant === "docked";

  return (
    <div className={isDocked ? "border-t border-border/40 bg-background/80 backdrop-blur-sm px-4 py-4" : "px-0 py-0"}>
      <div className={isDocked ? "mx-auto max-w-4xl" : ""}>
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={placeholder}
            disabled={disabled}
            autoFocus={autoFocus}
            rows={1}
            className={`w-full resize-none rounded-2xl border px-5 py-3.5 pr-14 text-[15px] leading-relaxed placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500/30 disabled:opacity-50 transition-all ${
              isDocked
                ? "border-border/60 bg-muted/20"
                : "border-border/50 bg-card/40 shadow-lg shadow-black/5"
            }`}
          />
          <Button
            size="icon"
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="absolute right-3 bottom-3 h-8 w-8 rounded-xl bg-emerald-500 text-white shadow-sm hover:bg-emerald-600 disabled:opacity-20 disabled:bg-muted-foreground/20 transition-all"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>
        <p className="mt-2 text-center text-[11px] text-muted-foreground/40">
          Enter 发送 · Shift+Enter 换行
        </p>
      </div>
    </div>
  );
}
