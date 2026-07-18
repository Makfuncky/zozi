import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (process.env.NODE_ENV === "production" && dsn) {
  Sentry.init({
    dsn,
    // Replay tracks user sessions on errors
    integrations: [Sentry.replayIntegration()],
    tracesSampleRate: 0.2,
    replaysSessionSampleRate: 0.05,
    replaysOnErrorSampleRate: 1.0,
    environment: process.env.NODE_ENV,
    sendDefaultPii: false,
  });
}
