"use client";

import { useEffect } from "react";
import { useLocaleStore } from "@/lib/localeStore";
import { logFrontendError } from "@shared/errorLogging";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const tr = useLocaleStore((s) => s.t);

  useEffect(() => {
    logFrontendError(error, "nextjs-global-error", { digest: error.digest });

    if (process.env.NODE_ENV !== "production") {
      console.error(error);
    }

    if (typeof window !== "undefined" && navigator.sendBeacon) {
      try {
        navigator.sendBeacon(
          "/api/frontend-errors",
          JSON.stringify({
            errors: [
              {
                message: error.message,
                source: "nextjs-global-error",
                stack: error.stack,
                context: { digest: error.digest },
                timestamp: new Date().toISOString(),
              },
            ],
            user_agent: navigator.userAgent,
            url: window.location.href,
          })
        );
      } catch {
        // best-effort beacon
      }
    }
  }, [error]);

  return (
    <html>
      <body className="flex min-h-screen items-center justify-center bg-[var(--color-surface-0)] p-6 text-[var(--color-text)]">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="mb-2 text-xl font-bold text-[var(--color-text)]">{tr("somethingWentWrong")}</h2>
          <p className="mb-6 text-sm text-[var(--color-text-muted)]">
            {tr("unexpectedErrorNotified")}
          </p>
          <button
            onClick={reset}
            className="theme-btn-primary px-6 py-2 rounded-lg text-sm font-semibold"
          >
            {tr("tryAgain")}
          </button>
        </div>
      </body>
    </html>
  );
}
