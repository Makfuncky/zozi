"use client";

import { Button } from "@/components/ui/Button";

export default function TicketsError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-md rounded-2xl border border-danger/40 bg-danger/10 p-6 text-center">
        <h2 className="text-lg font-bold text-danger">Failed to load tickets</h2>
        <p className="mt-2 text-sm text-danger/90">{error.message || "Something went wrong."}</p>
        <Button variant="danger" onClick={reset} className="mt-4">Retry</Button>
      </div>
    </div>
  );
}


