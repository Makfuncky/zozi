"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { PLACEHOLDER_IMAGE_PATH, resolveImage } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";

interface ArchivedProduct {
  id: number;
  name: string;
  price: number;
  image_url: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
  supplier_id?: number;
}

export default function ArchivePage() {
  const { isLoggedIn, user, isLoading } = useAuth();
  const router = useRouter();
  const formatPrice = useCurrencyStore((s) => s.format);

  const [products, setProducts] = useState<ArchivedProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [failedToLoadArchivedProductsLabel, failedToRestoreProductLabel, restoreRequestFailedLabel, archivedProductsLabel, noArchivedProductsLabel, archivedProductsDescriptionLabel, backToProductsLabel, archivedBadgeLabel, restoringLabel, restoreLabel] = useTranslateTexts([
    "Failed to load archived products",
    "Failed to restore product",
    "Restore request failed",
    "Archived Products",
    "No archived products",
    "Products you delete will appear here.",
    "← Back to Products",
    "ARCHIVED",
    "Restoring…",
    "Restore",
  ]);
  const translatedProductNames = useTranslateTexts(products.map((product) => product.name));

  const isAdmin = ["admin", "sub_admin", "moderator"].includes(user?.role ?? "");
  const isSupplier = user?.role === "supplier";

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || (!isAdmin && !isSupplier)) {
      router.replace("/products");
      return;
    }

    const endpoint = isAdmin ? "/admin/products?is_deleted=true&limit=200" : "/supplier/products?is_deleted=true";
    apiFetch(endpoint)
      .then((r) => r.json())
      .then((data) => setProducts(Array.isArray(data) ? data.filter((p: ArchivedProduct) => p.is_deleted) : []))
      .catch(() => setError(failedToLoadArchivedProductsLabel))
      .finally(() => setLoading(false));
  }, [failedToLoadArchivedProductsLabel, isLoggedIn, isLoading, isAdmin, isSupplier, router]);

  const handleRestore = async (id: number) => {
    setRestoring(id);
    try {
      const res = await apiFetch(`/admin/products/${id}/restore`, { method: "POST" });
      if (res.ok) {
        setProducts((prev) => prev.filter((p) => p.id !== id));
      } else {
        setError(failedToRestoreProductLabel);
      }
    } catch {
      setError(restoreRequestFailedLabel);
    } finally {
      setRestoring(null);
    }
  };

  if (isLoading || loading) {
    return (
      <main className="min-h-screen p-8">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-64 rounded-2xl bg-surface-2 animate-pulse" />
          ))}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <h1 className="text-2xl font-bold text-text">{archivedProductsLabel}</h1>
        <span className="px-2 py-0.5 rounded-full bg-danger/10 text-danger text-xs font-semibold">
          {products.length}
        </span>
      </div>

      {error && (
        <p className="mb-4 text-sm text-danger border border-danger/30 rounded-xl px-4 py-2">{error}</p>
      )}

      {products.length === 0 && !error && (
        <div className="text-center py-16 text-text-faint">
          <p className="text-4xl mb-3">🗂️</p>
          <p className="font-medium">{noArchivedProductsLabel}</p>
          <p className="text-sm mt-1">{archivedProductsDescriptionLabel}</p>
          <Link href="/products" className="mt-4 inline-block text-primary text-sm font-semibold hover:underline">
            {backToProductsLabel}
          </Link>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {products.map((product, index) => (
          <div
            key={product.id}
            className="relative rounded-2xl border border-border bg-surface-1 overflow-hidden opacity-75 hover:opacity-100 transition-opacity"
          >
            <div className="relative aspect-square bg-surface-2">
              <Image
                src={resolveImage(product.image_url ?? undefined)}
                alt={translatedProductNames[index] || product.name}
                fill
                className="object-cover grayscale"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = PLACEHOLDER_IMAGE_PATH;
                }}
              />
              <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-danger/80 text-white text-[10px] font-bold">
                {archivedBadgeLabel}
              </span>
            </div>
            <div className="p-3">
              <p className="text-xs font-semibold text-text line-clamp-2 mb-1">{translatedProductNames[index] || product.name}</p>
              <p className="text-xs text-text-faint mb-3">{formatPrice(product.price)}</p>
              {isAdmin && (
                <Button variant="primary" className="w-full text-xs font-semibold py-1.5 rounded-xl text-success transition-colors disabled:opacity-50" onClick={() => handleRestore(product.id)}
                  disabled={restoring === product.id}
                >
                  {restoring === product.id ? restoringLabel : restoreLabel}
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}



