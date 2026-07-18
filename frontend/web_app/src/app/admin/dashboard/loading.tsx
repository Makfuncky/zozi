import { PanelContent } from "@/components/PanelPage";

export default function AdminDashboardLoading() {
  return (
    <div className="min-h-screen bg-surface-base">
      <PanelContent className="mx-auto max-w-7xl px-4 py-8">
        {/* Header skeleton */}
        <div className="h-10 w-52 rounded-lg bg-surface-2 animate-pulse mb-8" />
        {/* Tab bar skeleton */}
        <div className="flex gap-2 mb-6 overflow-hidden">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-9 w-28 rounded-full bg-surface-2 animate-pulse shrink-0" />
          ))}
        </div>
        {/* KPI cards skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl bg-surface-2 animate-pulse h-28" />
          ))}
        </div>
        {/* Table skeleton */}
        <div className="rounded-xl bg-surface-2 animate-pulse h-64" />
      </PanelContent>
    </div>
  );
}


