"use client";

import { cn } from "@/lib/utils";

export interface SkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton = ({ className, count = 1 }: SkeletonProps) => {
  const items = Array.from({ length: count }, (_, i) => (
    <div key={i} className={cn("animate-pulse rounded bg-surface-2", className)} />
  ));
  return count > 1 ? <>{items}</> : items[0];
};

export const ProductCardSkeleton = () => (
  <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-3">
    <div className="h-48 animate-pulse rounded-lg bg-surface-2" />
    <div className="h-4 animate-pulse rounded bg-surface-2 w-3/4" />
    <div className="h-4 animate-pulse rounded bg-surface-2 w-1/2" />
  </div>
);

export const ProductGridSkeleton = ({ count = 4 }: { count?: number }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    {Array.from({ length: count }, (_, i) => (
      <ProductCardSkeleton key={i} />
    ))}
  </div>
);

export const TableSkeleton = ({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) => (
  <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
    {Array.from({ length: rows }, (_, row) => (
      <div key={row} className="flex items-center gap-4 p-4 border-b border-border last:border-0">
        {Array.from({ length: cols }, (_, col) => (
          <div key={col} className="h-4 animate-pulse rounded bg-surface-2 flex-1" />
        ))}
      </div>
    ))}
  </div>
);

// Page-specific skeletons
export const AuthFormSkeleton = () => (
  <div className="space-y-4">
    <div className="h-10 animate-pulse rounded-xl bg-surface-2" />
    <div className="h-10 animate-pulse rounded-xl bg-surface-2" />
    <div className="h-10 animate-pulse rounded-xl bg-surface-2" />
    <div className="h-12 animate-pulse rounded-xl bg-surface-2" />
  </div>
);

export const DashboardSkeleton = ({ tiles = 4, rows = 3 }: { tiles?: number; rows?: number }) => (
  <div className="space-y-4">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: tiles }, (_, i) => (
        <div key={i} className="h-24 animate-pulse rounded-xl bg-surface-2" />
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-64 animate-pulse rounded-xl bg-surface-2" />
      ))}
    </div>
  </div>
);

export const ProfileSkeleton = () => (
  <div className="space-y-6">
    <div className="flex items-center gap-4">
      <div className="w-20 h-20 animate-pulse rounded-full bg-surface-2" />
      <div className="space-y-2">
        <div className="h-5 animate-pulse rounded bg-surface-2 w-40" />
        <div className="h-4 animate-pulse rounded bg-surface-2 w-60" />
      </div>
    </div>
    <div className="space-y-4">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 animate-pulse rounded bg-surface-2 w-24" />
          <div className="h-10 animate-pulse rounded-xl bg-surface-2" />
        </div>
      ))}
    </div>
  </div>
);

export const OrdersListSkeleton = ({ count = 5 }: { count?: number }) => (
  <div className="space-y-4">
    {Array.from({ length: count }, (_, i) => (
      <div key={i} className="rounded-xl border border-border p-4 space-y-3">
        <div className="flex justify-between items-center">
          <div className="h-5 animate-pulse rounded bg-surface-2 w-32" />
          <div className="h-5 animate-pulse rounded bg-surface-2 w-20" />
        </div>
        <div className="flex gap-4">
          <div className="h-20 animate-pulse rounded-lg bg-surface-2 w-20" />
          <div className="space-y-2 flex-1">
            <div className="h-4 animate-pulse rounded bg-surface-2 w-3/4" />
            <div className="h-4 animate-pulse rounded bg-surface-2 w-1/2" />
            <div className="h-4 animate-pulse rounded bg-surface-2 w-full" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

export default Skeleton;


