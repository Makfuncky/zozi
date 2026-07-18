"use client";

import { useRecentlyViewedStore } from "@/lib/recentlyViewedStore";
import Link from "next/link";
import Image from "next/image";
import { useMemo } from "react";
import { Carousel } from "@/components/Carousel";

type RecentlyViewedProps = {
  excludeId?: number;
};

export default function RecentlyViewed({ excludeId }: RecentlyViewedProps) {
  const items = useRecentlyViewedStore((s) => s.products);
  const filtered = useMemo(() => items.filter((p) => p.id !== excludeId), [items, excludeId]);

  if (filtered.length === 0) return null;

  return (
    <div className="mt-8">
      <h3 className="text-sm font-semibold text-text-muted mb-3">Recently Viewed</h3>
      <Carousel ariaLabel="Recently viewed products" itemClassName="w-24">
        {filtered.map((p) => (
          <Link
            key={p.id}
            href={`/products/${p.id}`}
            className="block text-center group"
          >
            <div className="bg-surface-2 rounded-lg overflow-hidden mb-1">
              {p.image_url && (
                <Image src={p.image_url} alt={p.name} width={96} height={80} className="w-full h-20 object-cover" />
              )}
            </div>
            <p className="text-[10px] text-text-muted group-hover:text-text line-clamp-2">
              {p.name}
            </p>
          </Link>
        ))}
      </Carousel>
    </div>
  );
}

