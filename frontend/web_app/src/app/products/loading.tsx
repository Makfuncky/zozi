export default function ProductsLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-11xl mx-auto px-4 sm:px-6 py-4">
        {/* Search bar skeleton */}
        <div className="h-12 w-full max-w-xl mx-auto rounded-xl bg-muted animate-pulse mb-8" />
        {/* Category chips skeleton */}
        <div className="flex gap-3 mb-8 overflow-hidden">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-9 w-24 rounded-full bg-muted animate-pulse shrink-0" />
          ))}
        </div>
        {/* Product grid skeleton */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="aspect-square rounded-2xl bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}


