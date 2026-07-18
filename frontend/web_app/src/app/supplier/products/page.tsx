"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Package, Plus, RefreshCw, Search, Eye, Edit3 } from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { dc, useDensity } from "@/lib/densityContext";

interface SupplierProduct {
  id: number;
  name: string;
  price: number;
  currency: string;
  stock: number;
  status: string;
  created_at: string;
  image_url?: string;
}

export default function SupplierProductsPage() {
  const router = useRouter();
  const { density } = useDensity();
  const formatMoney = useCurrencyStore((s) => s.format);
  const [products, setProducts] = useState<SupplierProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", "100");
      if (search.trim()) params.set("search", search.trim());
      const res = await apiFetch(`/supplier/products?${params}`);
      if (res.ok) {
        const json = await res.json();
        setProducts(json.data ?? []);
        setTotal(json.total ?? 0);
      } else {
        setLoadError("Failed to load products");
      }
    } catch {
      setLoadError("Network error while loading products");
    }
    setLoading(false);
  }, [search]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");

  const columns: EnterpriseColumn<SupplierProduct>[] = [
    { key: "id", label: "#", width: "64px", sortable: true, render: (p) => <span className={`${bodyText} font-mono tabular-nums text-text-faint`}>#{p.id}</span> },
    { key: "name", label: "Name", sortable: true, render: (p) => (
      <div className="flex items-center gap-2">
        {p.image_url && <img src={p.image_url} alt="" className="h-8 w-8 rounded-lg object-cover bg-surface-2" />}
        <span className={`${bodyText} font-medium text-text`}>{p.name}</span>
      </div>
    )},
    { key: "price", label: "Price", width: "120px", align: "right", sortable: true, render: (p) => <span className={`${bodyText} font-semibold tabular-nums text-text`}>{formatMoney(p.price)}</span> },
    { key: "stock", label: "Stock", width: "80px", align: "right", sortable: true, render: (p) => <span className={`${bodyText} tabular-nums ${p.stock <= 5 ? "text-danger font-semibold" : "text-text"}`}>{p.stock}</span> },
    { key: "status", label: "Status", width: "100px", render: (p) => (
      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
        p.status === "active" ? "bg-success/10 text-success" : p.status === "pending" ? "bg-warning/10 text-warning" : "bg-surface-2 text-text-muted"
      }`}>{p.status}</span>
    )},
    { key: "created_at", label: "Created", width: "100px", render: (p) => <span className={`${bodyText} text-text-faint tabular-nums`}>{p.created_at?.slice(0, 10)}</span> },
    { key: "actions", label: "", width: "80px", render: (p) => (
      <div className="flex items-center gap-1">
        <button onClick={() => router.push(`/supplier/products/${p.id}`)} className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2 hover:text-text">
          <Eye className="h-3.5 w-3.5" />
        </button>
        <button onClick={() => router.push(`/supplier/products/${p.id}`)} className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2 hover:text-text">
          <Edit3 className="h-3.5 w-3.5" />
        </button>
      </div>
    )},
  ];

  return (
    <SupplierLayout title="Products">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-text">Products</h1>
          <p className="text-sm text-text-muted">Manage your catalog, inventory and pricing.</p>
        </div>
      </div>
      <PanelContent className="space-y-4">
        {loadError && !loading ? (
          <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
            <p className="text-sm font-semibold text-text">{loadError}</p>
            <button onClick={fetchProducts} className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold">Retry</button>
          </div>
        ) : null}
        <EnterpriseDataTable
          columns={columns}
          rows={products}
          rowKey={(p) => p.id}
          densityMode={density}
          enableBulkActions
          enableExport
          initialRowsPerPage={25}
          emptyState={loading ? undefined : "No products found"}
          toolbarSlot={
            <div className="flex items-center gap-2 flex-1">
              <div className="relative min-w-[14rem] flex-1 xl:w-64 xl:flex-none">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                <input value={search} onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && fetchProducts()}
                  placeholder="Search products…"
                  className="h-9 w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
              <Button variant="primary" className="flex h-9 items-center gap-1.5 rounded-xl px-4 text-xs font-semibold" onClick={() => router.push("/supplier/products/add")}>
                <Plus className="h-3.5 w-3.5" />Add
              </Button>
              <button onClick={fetchProducts} disabled={loading}
                className="flex h-9 items-center justify-center rounded-xl border border-border bg-surface-1 px-3 text-xs text-text-muted hover:bg-surface-2 disabled:opacity-50">
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
              <span className="text-[10px] text-text-faint tabular-nums">{total} total</span>
            </div>
          }
        />
      </PanelContent>
    </SupplierLayout>
  );
}
