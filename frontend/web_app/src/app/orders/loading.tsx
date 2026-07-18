export default function OrdersLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="h-8 w-40 rounded-lg bg-muted animate-pulse mb-6" />
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="rounded-2xl bg-muted animate-pulse h-28" />
          ))}
        </div>
      </div>
    </div>
  );
}


