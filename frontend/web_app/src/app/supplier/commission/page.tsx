"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BadgePercent, DollarSign, Globe2, Package, RefreshCw, Store, Tag } from "@/lib/icons";
import { Button } from "@/components/ui/Button";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/stores/toastStore";

interface CommissionRule {
  id: number;
  name: string;
  rate: number;
  category?: string | null;
  group?: string | null;
  brand?: string | null;
  product_type_id?: number | null;
  country_code?: string | null;
  priority: number;
  effective_from?: string | null;
  effective_to?: string | null;
  source: string;
}

interface CommissionProfile {
  id: number;
  name: string;
  is_default: boolean;
  country_code?: string | null;
}

interface SupplierCommissionData {
  profile: CommissionProfile;
  rules: CommissionRule[];
}

interface PreviewResult {
  gross_amount: number;
  commission_rate: number;
  commission_amount: number;
  net_to_supplier: number;
  rule_applied: string;
}

export default function SupplierCommissionPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((s) => s.addToast);

  const [data, setData] = useState<SupplierCommissionData[]>([]);
  const [loading, setLoading] = useState(true);

  // Preview calculator
  const [previewAmount, setPreviewAmount] = useState("");
  const [previewCocNode, setPreviewCocNode] = useState("");
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || user?.role !== "supplier") {
      router.push("/supplier/login");
    }
  }, [authLoading, isLoggedIn, user, router]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/supplier/coc/commission-rates");
      if (res.ok) {
        setData(await res.json());
      }
    } catch {
      addToast("Failed to load commission rates", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (isLoggedIn) fetchData();
  }, [fetchData, isLoggedIn]);

  const handlePreview = async () => {
    if (!previewAmount || !previewCocNode) {
      addToast("Enter amount and category", "error");
      return;
    }
    setPreviewLoading(true);
    try {
      const params = new URLSearchParams({
        coc_node_id: previewCocNode,
        gross_amount: previewAmount,
      });
      const res = await apiFetch(`/supplier/coc/order-commission-preview?${params}`);
      if (res.ok) {
        setPreviewResult(await res.json());
      } else {
        addToast("Preview failed", "error");
      }
    } catch {
      addToast("Preview failed", "error");
    } finally {
      setPreviewLoading(false);
    }
  };

  if (authLoading) return null;

  return (
    <AdminLayout title="Your Commission Rates" headerMode="compact">
      <PanelContent width="full" className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-text-muted">
            Your commission rates by category and country. Rates are determined by your supplier profile and applicable rules.
          </p>
          <Button variant="ghost" onClick={fetchData}>
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Commission Preview Calculator */}
        <div className="rounded-xl border border-border bg-surface-1 p-4">
          <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-primary" />
            Commission Calculator
          </h3>
          <div className="grid grid-cols-3 gap-3 items-end">
            <div>
              <label className="text-xs font-medium text-text-muted">Category ID (CoC Node)</label>
              <input
                value={previewCocNode}
                onChange={(e) => setPreviewCocNode(e.target.value)}
                type="number"
                placeholder="e.g. 5"
                className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-3 text-xs text-text"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-text-muted">Gross Amount (AED)</label>
              <input
                value={previewAmount}
                onChange={(e) => setPreviewAmount(e.target.value)}
                type="number"
                step="0.01"
                placeholder="5000"
                className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-3 text-xs text-text"
              />
            </div>
            <button
              onClick={handlePreview}
              disabled={previewLoading}
              className="h-9 rounded-lg bg-primary px-4 text-xs font-medium text-white hover:bg-primary/90 disabled:opacity-50"
            >
              {previewLoading ? "Calculating..." : "Calculate"}
            </button>
          </div>

          {previewResult && (
            <div className="mt-4 rounded-lg bg-surface-2 p-4">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-xs text-text-muted">Gross Amount</p>
                  <p className="text-lg font-bold text-text">{previewResult.gross_amount.toFixed(2)} AED</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted">Commission Rate</p>
                  <p className="text-lg font-bold text-primary">{previewResult.commission_rate}%</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted">Commission</p>
                  <p className="text-lg font-bold text-danger">-{previewResult.commission_amount.toFixed(2)} AED</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted">You Receive</p>
                  <p className="text-lg font-bold text-success">{previewResult.net_to_supplier.toFixed(2)} AED</p>
                </div>
              </div>
              <p className="mt-2 text-xs text-text-muted text-center">
                Rule Applied: {previewResult.rule_applied}
              </p>
            </div>
          )}
        </div>

        {/* Commission Rates by Profile */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 rounded-xl bg-surface-2 animate-pulse" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <div className="rounded-2xl border border-border bg-surface-1 px-6 py-12 text-center">
            <BadgePercent className="mx-auto h-8 w-8 text-text-faint" />
            <p className="mt-3 text-sm font-semibold text-text">No commission profiles found</p>
            <p className="mt-2 text-xs text-text-faint">Contact admin to set up your commission profile.</p>
          </div>
        ) : (
          data.map((sd) => (
            <div key={sd.profile.id} className="rounded-xl border border-border overflow-hidden">
              <div className="bg-surface-2 px-4 py-3 flex items-center gap-3">
                <Store className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold text-text">{sd.profile.name}</span>
                {sd.profile.is_default && (
                  <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">Default</span>
                )}
                {sd.profile.country_code && (
                  <span className="rounded-full bg-surface px-2 py-0.5 text-xs text-text-muted flex items-center gap-1">
                    <Globe2 className="h-3 w-3" />
                    {sd.profile.country_code}
                  </span>
                )}
                <span className="ml-auto text-xs text-text-muted">{sd.rules.length} rules</span>
              </div>

              {sd.rules.length === 0 ? (
                <div className="px-4 py-6 text-center text-xs text-text-faint">
                  No commission rules — default rates apply
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {sd.rules.map((rule) => (
                    <div key={rule.id} className="flex items-center gap-4 px-4 py-3 hover:bg-surface-2 transition-colors">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-text">{rule.name}</p>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {rule.category && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
                              <Tag className="h-3 w-3" />
                              {rule.category}
                            </span>
                          )}
                          {rule.group && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
                              <Package className="h-3 w-3" />
                              {rule.group}
                            </span>
                          )}
                          {rule.brand && (
                            <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
                              Brand: {rule.brand}
                            </span>
                          )}
                          {rule.country_code && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
                              <Globe2 className="h-3 w-3" />
                              {rule.country_code}
                            </span>
                          )}
                          {rule.effective_from && (
                            <span className="text-xs text-text-faint">
                              From: {rule.effective_from}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-primary">{rule.rate}%</p>
                        <p className="text-xs text-text-muted">{rule.source}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </PanelContent>
    </AdminLayout>
  );
}
