"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Package, AlertTriangle, TrendingDown, Globe } from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";

interface Product {
  id: number;
  name: string;
  stock: number;
  low_stock_threshold?: number;
  supplier_id?: number;
  is_active?: boolean;
}

interface StockSummary {
  total_products: number;
  low_stock: number;
  out_of_stock: number;
}

export default function AdminInventoryAlertsPage() {
  const router = useRouter();
  const { isLoggedIn, user } = useAuth();
  const role = user?.role ?? null;
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<Product[]>([]);
  const [summary, setSummary] = useState<StockSummary | null>(null);

  useEffect(() => {
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        const productsPath =
          countryCode && countryCode !== "*"
            ? `/admin/products/${countryCode}?limit=500`
            : `/admin/products?limit=500`;
        const res = await apiFetch(productsPath);
        if (res.ok) {
          const data = await res.json();
          const allProducts = Array.isArray(data) ? data : (data?.data || []);
          setProducts(allProducts);
          
          const lowStock = allProducts.filter((p: Product) => 
            (p.stock ?? 0) < (p.low_stock_threshold ?? 5) && (p.is_active ?? true)
          );
          const outOfStock = allProducts.filter((p: Product) => (p.stock ?? 0) === 0);
          
          setSummary({
            total_products: allProducts.length,
            low_stock: lowStock.length,
            out_of_stock: outOfStock.length,
          });
        }
      } catch (error) {
        console.error("Failed to load inventory:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isLoggedIn, role, router, countryCode]);

  if (!isLoggedIn || !isAdminStaffRole(role)) {
    return <PanelLoadingState count={3} blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse" />;
  }

  const lowStockProducts = products.filter(
    (p) => (p.stock ?? 0) < (p.low_stock_threshold ?? 5) && (p.is_active ?? true)
  );

  return (
    <AdminLayout title="Inventory Alerts" headerMode="compact">
      <PanelContent className="space-y-4">
        {selectedCountry && selectedCountry.code !== "*" && (
          <div className="flex items-center gap-2 rounded-lg border border-glass-border bg-glass-panel px-3 py-2">
            <Globe className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium text-text">{selectedCountry.name}</span>
            <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-primary">{selectedCountry.code}</span>
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-3">
            <div className="flex items-center gap-2 mb-1">
              <Package className="h-4 w-4 text-primary" />
              <span className="text-[11px] font-semibold text-text-faint uppercase">Total Products</span>
            </div>
            <p className="text-2xl font-bold text-text">{summary?.total_products ?? 0}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-warning" />
              <span className="text-[11px] font-semibold text-text-faint uppercase">Low Stock</span>
            </div>
            <p className="text-2xl font-bold text-text">{summary?.low_stock ?? 0}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="h-4 w-4 text-danger" />
              <span className="text-[11px] font-semibold text-text-faint uppercase">Out of Stock</span>
            </div>
            <p className="text-2xl font-bold text-text">{summary?.out_of_stock ?? 0}</p>
          </div>
        </div>

        <div className="theme-card rounded-xl border p-3">
          <h3 className="text-sm font-bold text-text mb-3">Products with Low Stock</h3>
          
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 rounded bg-surface-2 animate-pulse" />
              ))}
            </div>
          ) : lowStockProducts.length > 0 ? (
            <div className="space-y-2">
              {lowStockProducts.slice(0, 20).map((product) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between gap-2 rounded-lg border border-border bg-surface-2 px-3 py-2"
                >
                  <div>
                    <p className="font-semibold text-text">{product.name}</p>
                    <p className="text-[11px] text-text-faint">
                      Stock: {product.stock} · Threshold: {product.low_stock_threshold ?? 5}
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-warning/10 text-warning">
                    Low Stock
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-text-faint text-sm">No products with low stock.</p>
          )}
        </div>
      </PanelContent>
    </AdminLayout>
  );
}


