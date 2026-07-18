type SentryModule = {
  init: (options: Record<string, unknown>) => void;
};

async function loadSentry(): Promise<SentryModule | null> {
  try {
    const dynamicImport = new Function("specifier", "return import(specifier);") as (
      specifier: string,
    ) => Promise<SentryModule>;
    return await dynamicImport("@sentry/nextjs");
  } catch {
    return null;
  }
}

export async function register() {
  if (process.env.NODE_ENV !== "production") {
    return;
  }

  if (process.env.NEXT_RUNTIME === "nodejs") {
    const dsn = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (dsn) {
      const sentry = await loadSentry();
      if (!sentry) {
        return;
      }

      sentry.init({
        dsn,
        tracesSampleRate: 0.2,
        environment: process.env.NODE_ENV,
        sendDefaultPii: false,
      });
    }
  }

  if (process.env.NEXT_RUNTIME === "edge") {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (dsn) {
      const sentry = await loadSentry();
      if (!sentry) {
        return;
      }

      sentry.init({ dsn, tracesSampleRate: 0.2 });
    }
  }
}
