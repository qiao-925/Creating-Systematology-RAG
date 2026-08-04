"use client";

import { useEffect, useState, type ReactNode } from "react";

function MswActivator({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(
    process.env.NEXT_PUBLIC_MOCK !== "true"
  );

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_MOCK !== "true") {
      setReady(true);
      return;
    }
    async function start() {
      const { worker } = await import("@/mocks/browser");
      await worker.start({ onUnhandledRequest: "bypass" });
      setReady(true);
    }
    start();
  }, []);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <div className="h-8 w-8 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Loading mock server...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export function MswWrapper({ children }: { children: ReactNode }) {
  return <MswActivator>{children}</MswActivator>;
}
