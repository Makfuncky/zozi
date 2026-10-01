"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Layers3, Plus, RefreshCw, Search, Trash2, X,
} from "@/lib/icons";
import { useToastStore } from "@/stores/toastStore";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useAdminCountry } from "@/lib/useAdminCountry";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";

interface CatalogCategory {
  id: number;
  name: string;
  slug: string;
  parent_id?: number | null;
  sort_order?: number;
  is_active?: boolean;
  description?: string | null;
  icon?: string | null;
}

interface ListResponse {
  items?: CatalogCategory[];
  data?: CatalogCategory[];
  total?: number;
}

const COUNTRY_OPTIONS = ["AE", "SA"] as const;
type CountryCode = (typeof COUNTRY_OPTIONS)[number];

function AdminCatalogInner() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const { assignedCountries } = useAdminCountry();
  const addToast = useToastStore((s) => s.addToast);

  const initialCountry = (assignedCountries?.[0]?.code as CountryCode) ?? "AE";
  const [country, setCountry] = useState<CountryCode>(initialCountry);
  const [items, setItems] = useState<CatalogCategory[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [archiveId, setArchiveId] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", slug: "", description: "", sort_order: "0" });

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin", "moderator"].includes(role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, role, router]);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", "1");
      params.set("page_size", "100");
      if (search.trim()) params.set("search", search.trim());
      const res = await apiFetch(`/admin/catalog/categories/${country}?${params.toString()}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed (${res.status})`);
      }
      const json = (await res.json()) as ListResponse;
      const list = json.items ?? json.data ?? [];
      setItems(list);
      setTotal(json.total ?? list.length);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unable to load categories.";
      addToast(msg, "error");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [country, search, addToast]);

  useEffect(() => {
    if (isLoggedIn) fetchCategories();
  }, [fetchCategories, isLoggedIn]);

  const createCategory = async () => {
    if (!form.name || !form.slug) return;
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        name: form.name,
        slug: form.slug,
        sort_order: Number(form.sort_order || 0),
      };
      if (form.description) body.description = form.description;
      const res = await apiFetch(`/admin/catalog/categories/${country}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        addToast("Category created", "success");
        setShowForm(false);
        setForm({ name: "", slug: "", description: "", sort_order: "0" });
        fetchCategories();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to create category", "error");
      }
    } finally {
      setSaving(false);
    }
  };

  const archiveCategory = async (id: number) => {
    setArchiveId(id);
    try {
      const res = await apiFetch(`/admin/catalog/categories/${country}/${id}/archive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Admin archived from Catalog page" }),
      });
      if (res.ok) {
        addToast("Category archived", "success");
        fetchCategories();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to archive", "error");
      }
    } finally {
      setArchiveId(null);
    }
  };

  if (authLoading) {
    return (
      <AdminLayout title="Catalog">
        <PanelLoadingState count={3} />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Catalog" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs text-text-muted">
              Manage the Chart of Categories (Levels 1-3). Country-scoped per architecture.
            </p>
          </div>
          <div className="inline-flex overflow-hidden rounded-xl border border-border bg-surface-1 shadow-sm">
            {COUNTRY_OPTIONS.map((cc) => (
              <button
                key={cc}
                type="button"
                onClick={() => setCountry(cc)}
                aria-pressed={country === cc}
                className={`border-l border-border px-3 py-2 text-xs font-medium transition-colors first:border-l-0 ${
                  country === cc ? "bg-primary/10 text-primary" : "text-text-muted hover:bg-surface-2 hover:text-text"
                }`}
              >
                {cc}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-[16rem] flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search categories"
              className="h-9 w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
            />
          </div>
          <button
            type="button"
            onClick={fetchCategories}
            disabled={loading}
            className="flex h-9 items-center justify-center rounded-lg border border-border bg-surface-1 px-3 text-xs text-text-muted transition-colors hover:bg-surface-2 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-xs font-semibold text-on-brand hover:bg-primary/90"
          >
            <Plus className="h-3.5 w-3.5" />
            New Category
          </button>
        </div>

        {loading ? (
          <PanelLoadingState count={5} blockClassName="h-10 rounded-xl bg-surface-2 animate-pulse" />
        ) : items.length === 0 ? (
          <div className="rounded-2xl border border-border bg-surface-1 px-6 py-12 text-center">
            <Layers3 className="mx-auto h-8 w-8 text-text-faint" />
            <p className="mt-3 text-sm font-semibold text-text">No categories for {country}</p>
            <p className="mt-2 text-xs text-text-faint">
              {search.trim() ? "Try clearing the search filter." : "Create the first category for this country."}
            </p>
          </div>
        ) : (
          <div className="theme-card overflow-hidden rounded-xl border">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-2 text-[11px] uppercase tracking-wide text-text-faint">
                <tr>
                  <th className="px-3 py-2 font-semibold">#</th>
                  <th className="px-3 py-2 font-semibold">Name</th>
                  <th className="px-3 py-2 font-semibold">Slug</th>
                  <th className="px-3 py-2 font-semibold">Parent</th>
                  <th className="px-3 py-2 font-semibold text-right">Order</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                  <th className="px-3 py-2 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {items.map((c) => (
                  <tr key={c.id} className="bg-surface-1">
                    <td className="px-3 py-2 tabular-nums text-text-faint">{c.id}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        {c.icon ? <span>{c.icon}</span> : null}
                        <span className="font-medium text-text">{c.name}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-text-muted">{c.slug}</td>
                    <td className="px-3 py-2 text-text-faint">{c.parent_id ? `#${c.parent_id}` : "—"}</td>
                    <td className="px-3 py-2 text-right tabular-nums text-text-muted">{c.sort_order ?? 0}</td>
                    <td className="px-3 py-2">
                      {c.is_active === false ? (
                        <span className="rounded-full bg-warning/10 px-2 py-0.5 text-[11px] font-semibold text-warning">Inactive</span>
                      ) : (
                        <span className="rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">Active</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => archiveCategory(c.id)}
                        disabled={archiveId === c.id}
                        className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface-1 px-2 py-1 text-[11px] text-text-muted hover:bg-surface-2 hover:text-text disabled:opacity-50"
                      >
                        <Trash2 className="h-3 w-3" />
                        Archive
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="border-t border-border bg-surface-1 px-3 py-2 text-[11px] text-text-faint">
              {total} categories in {country}
            </div>
          </div>
        )}
      </PanelContent>

      {showForm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4">
          <div className="theme-card w-full max-w-md rounded-xl border p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-text">New Category ({country})</h2>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-4 space-y-3">
              <div>
                <label className="text-xs font-medium text-text-muted">Name *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Category name"
                  className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-muted">Slug *</label>
                <input
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  placeholder="category-slug"
                  className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-muted">Description</label>
                <input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Optional"
                  className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-muted">Sort order</label>
                <input
                  type="number"
                  value={form.sort_order}
                  onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                  className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
                />
              </div>
            </div>
            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="flex-1 rounded-xl border border-border py-2 text-xs text-text-muted hover:bg-surface-2"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={createCategory}
                disabled={saving || !form.name || !form.slug}
                className="flex-1 rounded-xl bg-primary py-2 text-xs font-semibold text-on-brand hover:bg-primary/90 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </AdminLayout>
  );
}

export default function AdminCatalogPage() {
  return (
    <Suspense>
      <AdminCatalogInner />
    </Suspense>
  );
}