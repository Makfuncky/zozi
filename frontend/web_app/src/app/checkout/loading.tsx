export default function CheckoutLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="h-8 w-48 rounded-lg bg-muted animate-pulse mb-8" />
        <div className="space-y-6">
          {/* Address section skeleton */}
          <div className="rounded-2xl border border-border p-6 space-y-4">
            <div className="h-5 w-32 rounded bg-muted animate-pulse" />
            <div className="h-10 w-full rounded-xl bg-muted animate-pulse" />
            <div className="h-10 w-full rounded-xl bg-muted animate-pulse" />
          </div>
          {/* Order summary skeleton */}
          <div className="rounded-2xl border border-border p-6 space-y-4">
            <div className="h-5 w-40 rounded bg-muted animate-pulse" />
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <div className="h-16 w-16 rounded-xl bg-muted animate-pulse shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-muted animate-pulse" />
                  <div className="h-4 w-1/4 rounded bg-muted animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


