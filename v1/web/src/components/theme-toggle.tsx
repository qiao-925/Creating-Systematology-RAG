"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { Button } from "@/components/ui/button";

const icons = {
  light: Sun,
  dark: Moon,
  system: Monitor,
} as const;

const cycle = ["light", "dark", "system"] as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  const current = (theme ?? "system") as (typeof cycle)[number];
  const next = cycle[(cycle.indexOf(current) + 1) % cycle.length];
  const Icon = icons[current];

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-8 w-8 text-muted-foreground hover:text-foreground"
      onClick={() => setTheme(next)}
      title={`Theme: ${current}`}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
