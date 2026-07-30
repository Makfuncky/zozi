"use client";

import Link from "next/link";
import { useLocaleStore } from "@/lib/localeStore";
import type { TranslationKey } from "@/lib/i18n";

interface BreadcrumbsProps {
  category?: string;
  search?: string;
}

export default function Breadcrumbs({ category, search }: BreadcrumbsProps) {
  const tr = useLocaleStore((s) => s.t);
  const segs: { label: string; href: string }[] = [];

  const categoryKeyMap: Record<string, TranslationKey> = {
    electronics: "electronics",
    fashion: "fashion",
    accessories: "accessories",
    furniture: "furniture",
    baby: "babyKids",
    books: "books",
    sports: "sports",
    automotive: "automotive",
    crafts: "crafts",
    home: "homeLiving",
    beauty: "beauty",
    grocery: "grocery",
  };

  segs.push({ label: tr("home"), href: "/" });
  segs.push({ label: tr("products"), href: "/products" });

  if (category && category !== "all") {
    const qs = new URLSearchParams();
    qs.set("category", category);
    const href = `/products?${qs.toString()}`;
    segs.push({ label: tr(categoryKeyMap[category] ?? "category"), href });
  }

  if (search) {
    const qs = new URLSearchParams();
    if (category && category !== "all") qs.set("category", category);
    qs.set("search", search);
    const href = `/products?${qs.toString()}`;
    segs.push({ label: `${tr("search")}: "${search}"`, href });
  }

  return (
    <nav aria-label="Breadcrumb" className="text-xs text-text-faint mb-2">
      <ol className="flex flex-wrap items-center gap-1">
        {segs.map((s, idx) => (
          <li key={idx} className="flex items-center gap-1">
            <Link href={s.href} className="hover:underline text-text-muted hover:text-text transition-colors">
              {s.label}
            </Link>
            {idx < segs.length - 1 && <span className="select-none text-border-light">›</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}


