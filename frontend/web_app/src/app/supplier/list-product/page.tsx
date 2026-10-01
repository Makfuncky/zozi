"use client";

import { Button } from "@/components/ui/Button";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronRight, Search, DollarSign, Info } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/stores/toastStore";

interface CoCCategory {
  id: number;
  name: string;
  slug: string;
  level: number;
  icon?: string | null;
  children?: CoCCategory[];
}

interface ProductType {
  id: number;
  name: string;
  slug: string;
}

interface CommissionPreview {
  rate: number;
  amount: number;
  net_amount: number;
  rule_name: string;
}

export default function SupplierListProductPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((s) => s.addToast);

  const [tree, setTree] = useState<CoCCategory[]>([]);
  const [selectedPath, setSelectedPath] = useState<CoCCategory[]>([]);
  const [productTypes, setProductTypes] = useState<ProductType[]>([]);
  const [selectedProductType, setSelectedProductType] = useState<ProductType | null>(null);
  const [loading, setLoading] = useState(true);
  const [grossAmount, setGrossAmount] = useState("");
  const [brand, setBrand] = useState("");
  const [commissionPreview, setCommissionPreview] = useState<CommissionPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
    }
  }, [authLoading, isLoggedIn, router]);

  const fetchTree = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/supplier/coc/tree?max_depth=3");
      if (res.ok) {
        setTree(await res.json());
      }
    } catch {
      addToast("Failed to load categories", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (isLoggedIn) fetchTree();
  }, [fetchTree, isLoggedIn]);

  const handleCategoryClick = async (category: CoCCategory, depth: number) => {
    const newPath = selectedPath.slice(0, depth);
    newPath[depth] = category;
    setSelectedPath(newPath);
    setSelectedProductType(null);
    setCommissionPreview(null);

    // Fetch product types for Level 3 categories
    if (category.level === 3) {
      try {
        const res = await apiFetch(`/api/v1/supplier/coc/categories/${category.id}/product-types`);
        if (res.ok) {
          setProductTypes(await res.json());
        }
      } catch {
        setProductTypes([]);
      }
    } else {
      setProductTypes([]);
    }
  };

  const handlePreviewCommission = async () => {
    if (selectedPath.length === 0 || !grossAmount) return;
    setPreviewLoading(true);
    try {
      const leafCategory = selectedPath[selectedPath.length - 1];
      const res = await apiFetch("/api/v1/supplier/coc/commission/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supplier_id: user?.id || 1,
          coc_node_id: leafCategory.id,
          gross_amount: parseFloat(grossAmount),
          product_type_id: selectedProductType?.id,
          brand: brand || undefined,
        }),
      });
      if (res.ok) {
        setCommissionPreview(await res.json());
      }
    } catch {
      addToast("Failed to preview commission", "error");
    } finally {
      setPreviewLoading(false);
    }
  };

  const renderCategories = (categories: CoCCategory[], depth: number) => {
    return categories.map((cat) => {
      const isSelected = selectedPath[depth]?.id === cat.id;
      const hasChildren = cat.children && cat.children.length > 0;

      return (
        <div key={cat.id}>
          <button
            onClick={() => handleCategoryClick(cat, depth)}
            className={`w-full flex items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors ${
              isSelected ? "bg-primary/10 text-primary" : "hover:bg-surface-2 text-text"
            }`}
            style={{ paddingLeft: `${depth * 16 + 12}px` }}
          >
            {cat.icon && <span className="text-base">{cat.icon}</span>}
            <span className="flex-1 text-sm">{cat.name}</span>
            {hasChildren && <ChevronRight className="h-3 w-3 text-text-muted" />}
          </button>
          {isSelected && hasChildren && renderCategories(cat.children!, depth + 1)}
        </div>
      );
    });
  };

  if (authLoading) return null;

  return (
    <AdminLayout title="List Product" headerMode="compact">
      <PanelContent width="full">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Category Picker */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-semibold text-text">Select Category</h2>

            {/* Breadcrumb */}
            {selectedPath.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-text-muted">
                {selectedPath.map((cat, i) => (
                  <span key={cat.id} className="flex items-center gap-1">
                    {i > 0 && <ChevronRight className="h-3 w-3" />}
                    <button
                      onClick={() => handleCategoryClick(cat, i)}
                      className="hover:text-primary"
                    >
                      {cat.name}
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Category Tree */}
            <div className="rounded-xl border border-border overflow-hidden max-h-96 overflow-y-auto">
              {loading ? (
                <div className="p-4 space-y-2">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="h-8 rounded bg-surface-2 animate-pulse" />
                  ))}
                </div>
              ) : (
                <div className="p-2">{renderCategories(tree, 0)}</div>
              )}
            </div>

            {/* Product Types */}
            {productTypes.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-text mb-2">Product Type</h3>
                <div className="grid grid-cols-2 gap-2">
                  {productTypes.map((pt) => (
                    <button
                      key={pt.id}
                      onClick={() => setSelectedProductType(pt)}
                      className={`rounded-lg border p-3 text-left text-sm transition-colors ${
                        selectedProductType?.id === pt.id
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:bg-surface-2"
                      }`}
                    >
                      {pt.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Product Details */}
            {selectedPath.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-text">Product Details</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-text-muted">Brand</label>
                    <input
                      value={brand}
                      onChange={(e) => setBrand(e.target.value)}
                      placeholder="e.g. Apple, Samsung"
                      className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-text-muted">Price (AED) *</label>
                    <input
                      value={grossAmount}
                      onChange={(e) => setGrossAmount(e.target.value)}
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      className="mt-1 h-9 w-full rounded-lg border border-border bg-surface-1 px-3 text-xs text-text"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Commission Preview */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-text">Commission Preview</h2>

            <div className="theme-card rounded-xl border p-4 space-y-4">
              <div className="flex items-center gap-2 text-text-muted">
                <Info className="h-4 w-4" />
                <span className="text-xs">Commission is calculated based on category and supplier rules.</span>
              </div>

              {selectedPath.length > 0 ? (
                <>
                  <div className="space-y-2">
                    <p className="text-xs text-text-muted">Selected Category:</p>
                    <p className="text-sm font-medium text-text">
                      {selectedPath.map((c) => c.name).join(" > ")}
                    </p>
                  </div>

                  {selectedProductType && (
                    <div className="space-y-2">
                      <p className="text-xs text-text-muted">Product Type:</p>
                      <p className="text-sm font-medium text-text">{selectedProductType.name}</p>
                    </div>
                  )}

                  <Button
                    variant="secondary"
                    onClick={handlePreviewCommission}
                    disabled={!grossAmount || previewLoading}
                    className="w-full"
                  >
                    {previewLoading ? "Calculating..." : "Calculate Commission"}
                  </Button>

                  {commissionPreview && (
                    <div className="rounded-lg bg-surface-2 p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-muted">Commission Rate</span>
                        <span className="text-sm font-bold text-primary">{commissionPreview.rate}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-muted">Commission Amount</span>
                        <span className="text-sm font-bold text-danger">{commissionPreview.amount} AED</span>
                      </div>
                      <div className="flex items-center justify-between border-t border-border pt-2">
                        <span className="text-xs font-medium text-text-muted">You Receive</span>
                        <span className="text-lg font-bold text-success">{commissionPreview.net_amount} AED</span>
                      </div>
                      <p className="text-xs text-text-faint">Rule: {commissionPreview.rule_name}</p>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-text-muted text-center py-4">
                  Select a category to see commission preview
                </p>
              )}
            </div>
          </div>
        </div>
      </PanelContent>
    </AdminLayout>
  );
}
