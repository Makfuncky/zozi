export default function NotificationsLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="h-8 w-44 rounded-lg bg-muted animate-pulse mb-6" />
        <div className="space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-2xl bg-muted animate-pulse h-20" />
          ))}
        </div>
      </div>
    </div>
  );
}


