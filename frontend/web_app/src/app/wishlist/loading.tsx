export default function WishlistLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="h-8 w-36 rounded-lg bg-muted animate-pulse mb-6" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-2xl bg-muted animate-pulse aspect-[3/4]" />
          ))}
        </div>
      </div>
    </div>
  );
}


