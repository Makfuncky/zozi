"use client";

import { Button } from "@/components/ui/Button";

export default function SupplierError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-md rounded-xl border border-warning/40 bg-warning/10 p-6 text-center">
        <h2 className="text-lg font-bold text-warning">Supplier panel crashed</h2>
        <p className="mt-2 text-sm text-warning/90">{error.message || "Something went wrong."}</p>
        <Button variant="warning" onClick={reset}>
          Retry
        </Button>
      </div>
    </div>
  );
}


