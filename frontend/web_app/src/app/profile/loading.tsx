export default function ProfileLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="h-8 w-36 rounded-lg bg-muted animate-pulse mb-8" />
        <div className="rounded-2xl border border-border p-6 space-y-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-muted animate-pulse" />
            <div className="space-y-2 flex-1">
              <div className="h-5 w-40 rounded bg-muted animate-pulse" />
              <div className="h-3 w-56 rounded bg-muted animate-pulse" />
            </div>
          </div>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}


