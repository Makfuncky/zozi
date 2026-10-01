"use client";

import { motion } from "framer-motion";
import { cn } from "../../utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <motion.div
      className={cn(
        "rounded-lg theme-bg-shimmer bg-size-[200%_100%]",
        className
      )}
      animate={{
        backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
        opacity: [0.6, 1, 0.6],
      }}
      transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="theme-card overflow-hidden rounded-3xl border">
      <Skeleton className="aspect-square w-full" />
      <div className="space-y-1.5 p-2">
        <Skeleton className="h-2.5 w-1/4" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-1/2" />
        <div className="flex items-center justify-between pt-1">
          <Skeleton className="h-3.5 w-14" />
          <Skeleton className="h-3.5 w-9" />
        </div>
      </div>
    </div>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-8 xl:gap-2.5">
      {Array.from({ length: count }).map((_, index) => (
        <ProductCardSkeleton key={index} />
      ))}
    </div>
  );
}

/* ---------- Table Skeleton ----------------------------------- */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="theme-card overflow-hidden rounded-xl border">
      <div className="border-b border-border p-3">
        <Skeleton className="w-1/3 h-4" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-3 border-b border-glass-border-soft p-3 last:border-0"
        >
          <Skeleton className="w-6 h-6 rounded-full" />
          <Skeleton className="flex-1 h-3" />
          <Skeleton className="w-16 h-3" />
        </div>
      ))}
    </div>
  );
}

/* ---------- Full-Page Loader --------------------------------- */
export default function LoadingSkeleton() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-base">
      <motion.div
        className="flex flex-col items-center gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="relative h-12 w-12">
          <motion.div
            className="absolute inset-0 rounded-xl bg-primary/20 border border-primary/30"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          />
          <motion.div
            className="absolute inset-2 rounded-lg bg-primary/40"
            animate={{ rotate: -360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
          />
        </div>
        <p className="text-sm font-medium text-text-muted">Loading…</p>
      </motion.div>
    </div>
  );
}