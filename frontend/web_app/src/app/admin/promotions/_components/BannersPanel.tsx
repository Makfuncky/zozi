"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import {
  Loader2,
  Megaphone,
  Plus,
  RefreshCw,
  X,
  Edit3,
  ImageIcon,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import BannerCanvasEditor, { DEFAULT_LAYOUT, type BannerLayout } from "@/components/BannerCanvasEditor";

interface Banner {
  id: number;
  title: string;
  subtitle: string | null;
  image_url: string | null;
  cta_label: string;
  cta_url: string;
  banner_type: string;
  is_active: boolean;
  sort_order: number;
  link?: string | null;
  country_code?: string | null;
  layout_json?: string | null;
  mobile_image_url?: string | null;
  created_at: string | null;
}

interface BannerForm {
  title: string;
  subtitle: string;
  cta_label: string;
  cta_url: string;
  banner_type: string;
  is_active: boolean;
  sort_order: string;
  image_url?: string | null;
  mobile_image_url?: string | null;
  layout: BannerLayout;
}

const parseLayout = (raw?: string | null): BannerLayout => {
  if (!raw) return JSON.parse(JSON.stringify(DEFAULT_LAYOUT));
  try {
    const p = JSON.parse(raw);
    if (p && Array.isArray(p.elements) && p.bg) return p as BannerLayout;
  } catch {
    /* ignore */
  }
  return JSON.parse(JSON.stringify(DEFAULT_LAYOUT));
};

const EMPTY_FORM: BannerForm = {
  title: "",
  subtitle: "",
  cta_label: "Shop Now",
  cta_url: "/products",
  banner_type: "hero",
  is_active: true,
  sort_order: "0",
  layout: JSON.parse(JSON.stringify(DEFAULT_LAYOUT)),
};

const BANNER_TYPES = ["hero", "flash", "seasonal", "promotional", "category"];

export default function BannersPanel() {
  const { addToast } = useToastStore();
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";

  const [banners, setBanners] = useState<Banner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<BannerForm>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;

  const buildUrl = useCallback(
    (path: string) => {
      const base = countryCode && countryCode !== "*" ? `/admin/${countryCode}/promotions` : "/admin/promotions";
      return `${base}${path}`;
    },
    [countryCode]
  );

  const loadBanners = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`${buildUrl("/banners")}?page=${page}&page_size=${pageSize}`);
      if (!res.ok) throw new Error("Failed to load banners");
      const body = await res.json();
      setBanners(body.data ?? []);
      setTotal(body.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load banners");
    } finally {
      setLoading(false);
    }
  }, [page, buildUrl]);

  useEffect(() => {
    loadBanners();
  }, [loadBanners]);

  function openCreateModal() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setShowModal(true);
  }

  function openEditModal(banner: Banner) {
    setEditingId(banner.id);
    setForm({
      title: banner.title,
      subtitle: banner.subtitle ?? "",
      cta_label: banner.cta_label ?? "Shop Now",
      cta_url: banner.cta_url ?? "/products",
      banner_type: banner.banner_type,
      is_active: banner.is_active,
      sort_order: String(banner.sort_order),
      image_url: banner.image_url ?? null,
      mobile_image_url: banner.mobile_image_url ?? null,
      layout: parseLayout(banner.layout_json),
    });
    setShowModal(true);
  }

  async function saveBanner() {
    if (!form.title.trim()) {
      addToast("Title is required", "error");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        subtitle: form.subtitle.trim() || null,
        cta_label: form.cta_label || "Shop Now",
        cta_url: form.cta_url || "/products",
        banner_type: form.banner_type || "hero",
        is_active: form.is_active,
        sort_order: parseInt(form.sort_order, 10) || 0,
        bg_color: form.layout?.bg.color || null,
        effect: form.layout?.effect || null,
        video_url: form.layout?.bg.videoUrl || null,
        image_url: form.layout?.bg.imageUrl || null,
        mobile_image_url: form.mobile_image_url || null,
        layout_json: JSON.stringify(form.layout),
      };

      if (editingId) {
        const res = await apiFetch(`${buildUrl("/banners")}/${editingId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Failed to update banner");
        addToast("Banner updated", "success");
      } else {
        const res = await apiFetch(buildUrl("/banners"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Failed to create banner");
        addToast("Banner created", "success");
      }

      setShowModal(false);
      loadBanners();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to save banner", "error");
    } finally {
      setSaving(false);
    }
  }

  async function deleteBanner(id: number) {
    if (!confirm("Delete this banner?")) return;
    try {
      const res = await apiFetch(`${buildUrl("/banners")}/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete banner");
      setBanners((prev) => prev.filter((b) => b.id !== id));
      addToast("Banner deleted", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to delete banner", "error");
    }
  }

  async function toggleActive(banner: Banner) {
    try {
      const res = await apiFetch(`${buildUrl("/banners")}/${banner.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !banner.is_active }),
      });
      if (!res.ok) throw new Error("Failed to toggle banner");
      setBanners((prev) =>
        prev.map((b) => (b.id === banner.id ? { ...b, is_active: !banner.is_active } : b))
      );
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to toggle banner", "error");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text">Banners</h3>
        <div className="flex items-center gap-2">
          {selectedCountry && selectedCountry.code !== "*" && (
            <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {selectedCountry.code}
            </span>
          )}
          <button
            onClick={loadBanners}
            className="rounded-lg border border-border bg-surface p-2 text-text-muted hover:bg-surface-hover"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <Button variant="primary" onClick={openCreateModal}>
            <Plus className="h-3.5 w-3.5" />
            Add Banner
          </Button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-danger bg-surface p-4 text-sm text-danger">
          {error}
        </div>
      )}

      {!loading && !error && banners.length === 0 && (
        <div className="flex flex-col items-center py-12 text-text-muted">
          <Megaphone className="mb-2 h-8 w-8" />
          <p className="text-sm">No banners found. Create your first banner.</p>
        </div>
      )}

      {!loading && banners.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-border bg-surface">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-xs font-semibold uppercase text-text-muted">
                <th className="px-4 py-3">Order</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">CTA</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {banners.map((banner) => (
                <tr key={banner.id} className="border-b border-border last:border-0 hover:bg-surface-2/50">
                  <td className="px-4 py-3 text-xs text-text-muted">{banner.sort_order}</td>
                  <td className="px-4 py-3 font-medium text-text">
                    <div>{banner.title}</div>
                    {banner.subtitle && (
                      <div className="mt-0.5 text-xs text-text-muted line-clamp-1">{banner.subtitle}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-surface-2 px-2 py-0.5 text-xs capitalize text-text-muted">
                      {banner.banner_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleActive(banner)}
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        banner.is_active
                          ? "theme-chip-success"
                          : "theme-chip-muted"
                      }`}
                    >
                      {banner.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-xs text-text-muted">
                    {banner.cta_label ? (
                      <span className="font-mono">{banner.cta_label}: {banner.cta_url}</span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEditModal(banner)}
                        className="rounded p-1.5 text-text-muted hover:bg-surface-2 hover:text-text"
                        title="Edit"
                      >
                        <Edit3 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => deleteBanner(banner.id)}
                        className="rounded p-1.5 text-text-muted hover:bg-surface-2 hover:text-danger"
                        title="Delete"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {total > pageSize && (
            <div className="flex items-center justify-between border-t border-border px-4 py-3">
              <span className="text-xs text-text-muted">{total} total</span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded px-3 py-1 text-xs font-medium text-text-muted hover:bg-surface-2 disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-xs text-text-muted">Page {page}</span>
                <button
                  disabled={page * pageSize >= total}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded px-3 py-1 text-xs font-medium text-text-muted hover:bg-surface-2 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay">
          <div className="max-h-[95vh] w-full max-w-4xl overflow-y-auto rounded-xl bg-surface p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold text-text">
              {editingId ? "Edit Banner" : "Create Banner"}
            </h3>

            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-text-muted">Title *</label>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-primary"
                  placeholder="Banner title"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-text-muted">Subtitle</label>
                <input
                  value={form.subtitle}
                  onChange={(e) => setForm({ ...form, subtitle: e.target.value })}
                  className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-primary"
                  placeholder="Optional subtitle"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-text-muted">CTA Label</label>
                  <input
                    value={form.cta_label}
                    onChange={(e) => setForm({ ...form, cta_label: e.target.value })}
                    className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-primary"
                    placeholder="Shop Now"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-text-muted">CTA URL</label>
                  <input
                    value={form.cta_url}
                    onChange={(e) => setForm({ ...form, cta_url: e.target.value })}
                    className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-primary"
                    placeholder="/products"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-text-muted">Banner Type</label>
                  <select
                    value={form.banner_type}
                    onChange={(e) => setForm({ ...form, banner_type: e.target.value })}
                    className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-primary"
                  >
                    {BANNER_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
              <label className="mb-1 block text-xs font-medium text-text-muted">Sort Order</label>
              <input
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-primary"
              />
              </div>
              </div>

              <div className="rounded-xl border border-border/70 bg-surface-2/40 p-3">
                <p className="mb-2 text-xs font-semibold text-text">Design Canvas</p>
                <p className="mb-3 text-[11px] text-text-muted">
                  Build any kind of banner: add shapes, text, images, video, buttons or icons and place them anywhere. Group elements, set z-order, flip, copy/paste, align/distribute, use grid+snap, gradients, shadows, blend modes and undo/redo. Start from a template and export/import the design as JSON. Pick a celebration / season background effect below.
                </p>
                <BannerCanvasEditor value={form.layout} onChange={(l) => setForm({ ...form, layout: l })} />
              </div>

              {/* Mobile-specific creative — designed separately for small screens */}
              <div className="rounded-xl border border-border/70 bg-surface-2/40 p-3">
                <p className="mb-1 text-xs font-semibold text-text">Mobile Banner Image</p>
                <p className="mb-3 text-[11px] text-text-muted">
                  Upload a separate, compact creative for the mobile app (smaller space, less crowding).
                  If left empty, the mobile app falls back to the desktop image above.
                </p>
                {form.mobile_image_url ? (
                  <div className="mb-2 flex items-center gap-3">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={form.mobile_image_url}
                      alt="Mobile banner preview"
                      className="h-16 w-28 rounded-lg border border-border object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => setForm({ ...form, mobile_image_url: null })}
                      className="rounded-lg border border-border bg-surface px-2 py-1 text-xs text-text-muted hover:text-danger"
                    >
                      Remove
                    </button>
                  </div>
                ) : null}
                <input
                  type="file"
                  accept="image/*"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file || !editingId) {
                      addToast("Save the banner before uploading an image", "error");
                      e.target.value = "";
                      return;
                    }
                    try {
                      const fd = new FormData();
                      fd.append("file", file);
                      const res = await apiFetch(
                        `${buildUrl("/banners")}/${editingId}/image?slot=mobile`,
                        { method: "POST", body: fd }
                      );
                      if (!res.ok) throw new Error("Upload failed");
                      const data = await res.json();
                      setForm({ ...form, mobile_image_url: data.mobile_image_url ?? data.image_url });
                      addToast("Mobile banner image uploaded", "success");
                    } catch (err) {
                      addToast(err instanceof Error ? err.message : "Upload failed", "error");
                    } finally {
                      e.target.value = "";
                    }
                  }}
                  className="block w-full text-xs text-text-muted file:mr-2 file:rounded-lg file:border-0 file:bg-primary/10 file:px-3 file:py-1.5 file:text-primary"
                />
              </div>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <span className="text-sm text-text">Active</span>
              </label>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowModal(false)}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:bg-surface-2"
              >
                Cancel
              </button>
              <Button variant="primary" onClick={saveBanner}
                disabled={saving}>
                {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                {editingId ? "Update" : "Create"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
