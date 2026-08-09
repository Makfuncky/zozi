import { PanelContent } from "@/components/PanelPage";

export default function SupplierDashboardLoading() {
  return (
    <div className="min-h-screen bg-surface-base">
      <PanelContent className="mx-auto max-w-7xl px-4 py-8 space-y-5">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-surface-2" />
          ))}
        </div>
        <div className="h-48 animate-pulse rounded-xl bg-surface-2" />
      </PanelContent>
    </div>
  );
}
