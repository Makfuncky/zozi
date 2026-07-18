"use client";

export default function InvoiceError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-md rounded-2xl border border-border bg-surface-1 p-6 text-center">
        <h2 className="text-lg font-bold text-text">Invoice view failed</h2>
        <p className="mt-2 text-sm text-text-muted">{error.message || "Unable to render invoice."}</p>
        <button
          onClick={reset}
          className="mt-4 rounded-xl theme-btn-primary px-4 py-2 text-sm font-semibold"
        >
          Retry
        </button>
      </div>
    </div>
  );
}


