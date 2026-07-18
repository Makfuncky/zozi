"use client";

export default function RootError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      <div className="max-w-md rounded-2xl border border-danger/40 bg-danger/10 p-8 text-center">
        <h2 className="text-xl font-bold text-danger">Something went wrong</h2>
        <p className="mt-3 text-sm text-muted-foreground">
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <button
          onClick={reset}
          className="mt-6 rounded-xl theme-btn-primary px-6 py-2.5 text-sm font-semibold"
        >
          Try again
        </button>
      </div>
    </div>
  );
}


