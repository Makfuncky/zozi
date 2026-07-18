"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw, Sparkles, Save, Upload, Image as ImageIcon } from "lucide-react";
import { apiFetch } from "@/lib/api";
import TranslatedText from "@/components/TranslatedText";
import BannerCanvasEditor, { DEFAULT_LAYOUT, type BannerLayout } from "@/components/BannerCanvasEditor";

type BannerForm = {
  id: string;
  title: string;
  subtitle: string;
  badge_text: string;
  cta_text: string;
  cta_url: string;
  image_url: string;
  is_active: boolean;
  sort_order: number;
  effect: string;
  video_url: string;
  country_code: string;
  layout: BannerLayout | null;
};

const createBanner = (id: string, overrides: Partial<BannerForm> = {}): BannerForm => ({
  id,
  title: "Summer Sale is Here!",
  subtitle: "Up to 60% off on thousands of products. Limited time deals updated daily.",
  badge_text: "Seasonal Offers",
  cta_text: "Shop Now",
  cta_url: "/products",
  image_url: "",
  is_active: true,
  sort_order: 0,
  effect: "balloons",
  video_url: "",
  country_code: "",
  layout: JSON.parse(JSON.stringify(DEFAULT_LAYOUT)),
  ...overrides,
});

// Build a starter canvas layout from legacy appearance fields so the editor
// reflects the banner's current color / effect when no canvas was saved yet.
function layoutFromLegacy(b: any): BannerLayout {
  return {
    bg: {
      color: b.bg_color || "#0f172a",
      gradientFrom: "",
      gradientVia: "",
      gradientTo: "",
      imageUrl: b.image_url || "",
      videoUrl: b.video_url || "",
    },
    effect: b.effect || "",
    elements: [],
  };
}

const safeParseLayout = (raw: any): BannerLayout | null => {
  if (!raw) return null;
  try {
    const p = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (p && Array.isArray(p.elements) && p.bg) return p as BannerLayout;
  } catch {
    /* ignore */
  }
  return null;
};

export default function BannerTab() {
  const [initialBannerId] = useState(() => `banner-${Date.now()}`);
  const [bannerForms, setBannerForms] = useState<BannerForm[]>(() => [createBanner(initialBannerId)]);
  const [activeBannerId, setActiveBannerId] = useState(() => initialBannerId);
  const [bannerLoading, setBannerLoading] = useState(false);
  const [bannerSaved, setBannerSaved] = useState(false);
  const [bannerImageUploading, setBannerImageUploading] = useState(false);
  const bannerImageRef = useRef<HTMLInputElement>(null);
  const [countries, setCountries] = useState<{ code: string; name: string }[]>([]);

  const activeBannerIndex = Math.max(0, bannerForms.findIndex((b) => b.id === activeBannerId));
  const activeBanner = bannerForms[activeBannerIndex] ?? bannerForms[0];

  const updateActiveBanner = (patch: Partial<BannerForm>) =>
    setBannerForms((prev) => prev.map((b, i) => (i === activeBannerIndex ? { ...b, ...patch } : b)));

  const updateLayout = (layout: BannerLayout) => updateActiveBanner({ layout });

  const handleAddBanner = () => {
    const id = `banner-${Date.now()}`;
    const newBanner = createBanner(id, {
      title: `New Banner ${bannerForms.length + 1}`,
      subtitle: "Add your promotion details here.",
      badge_text: "New Drop",
      is_active: true,
    });
    setBannerForms((prev) => [...prev, newBanner]);
    setActiveBannerId(id);
  };

  const handleRemoveBanner = async () => {
    if (bannerForms.length <= 1) return;
    const bannerId = activeBanner?.id;
    if (bannerId && !isNaN(Number(bannerId))) {
      try {
        await apiFetch(`/admin/banners/${bannerId}`, { method: "DELETE" });
      } catch {
        /* ignore */
      }
    }
    setBannerForms((prev) => {
      const next = prev.filter((_, i) => i !== activeBannerIndex);
      const nextIndex = Math.max(0, activeBannerIndex - 1);
      setActiveBannerId(next[nextIndex]?.id ?? next[0]?.id);
      return next;
    });
  };

  // Load banners on mount
  useEffect(() => {
    apiFetch("/admin/banners")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        const list = Array.isArray(data) ? data : [];
        const normalized = list.length > 0 ? list : [createBanner(`banner-${Date.now()}`)];
        const withIds = normalized.map((b: any) => ({
          ...createBanner(String(b.id ?? `banner-${Date.now()}`)),
          id: String(b.id ?? `banner-${Date.now()}`),
          title: b.title ?? "",
          subtitle: b.subtitle ?? "",
          badge_text: b.badge_text ?? "",
          cta_text: b.cta_label ?? "Shop Now",
          cta_url: b.cta_url ?? "/products",
          image_url: b.image_url ?? "",
          is_active: b.is_active ?? true,
          sort_order: b.sort_order ?? 0,
          effect: b.effect ?? "",
          video_url: b.video_url ?? "",
          country_code: b.country_code ?? "",
          layout: safeParseLayout(b.layout_json) ?? layoutFromLegacy(b),
        }));
        setBannerForms(withIds);
        setActiveBannerId(String(withIds[0]?.id ?? `banner-${Date.now()}`));
      })
      .catch(() => {});
  }, []);

  // Load available countries for per-country banner targeting
  useEffect(() => {
    apiFetch("/countries")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => (Array.isArray(data) ? setCountries(data) : []))
      .catch(() => {});
  }, []);

  const handleSaveBanners = useCallback(async () => {
    setBannerLoading(true);
    try {
      const newIds: Record<string, number> = {};
      for (const banner of bannerForms) {
        const bid = banner.id;
        const layout = banner.layout ? JSON.stringify(banner.layout) : null;
        const payload = {
          title: banner.title,
          subtitle: banner.subtitle,
          image_url: banner.image_url || null,
          cta_label: banner.cta_text || "Shop Now",
          cta_url: banner.cta_url || "/products",
          banner_type: "hero",
          is_active: banner.is_active ?? true,
          sort_order: banner.sort_order ?? 0,
          bg_color: banner.layout?.bg.color || null,
          text_color: null,
          subtitle_color: null,
          btn_bg_color: null,
          btn_text_color: null,
          badge_text: banner.badge_text || null,
          badge_color: null,
          effect: banner.layout?.effect || banner.effect || null,
          video_url: banner.layout?.bg.videoUrl || banner.video_url || null,
          country_code: banner.country_code || null,
          layout_json: layout,
        };
        if (bid && !isNaN(Number(bid))) {
          await apiFetch(`/admin/banners/${bid}`, { method: "PUT", body: JSON.stringify(payload) });
        } else {
          const res = await apiFetch("/admin/banners", { method: "POST", body: JSON.stringify(payload) });
          if (res.ok) {
            const created = await res.json();
            newIds[bid] = created.id;
          }
        }
      }
      if (Object.keys(newIds).length > 0) {
        setBannerForms((prev) => prev.map((b) => (newIds[b.id] ? { ...b, id: String(newIds[b.id]) } : b)));
      }
      setBannerSaved(true);
      setTimeout(() => setBannerSaved(false), 2500);
    } catch {
      /* ignore */
    }
    setBannerLoading(false);
  }, [bannerForms]);

  return (
    <div className="max-w-3xl space-y-5">
      <div className="theme-card rounded-2xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-text flex items-center gap-2">
            <Sparkles className="w-4 h-4 theme-status-warning" /> Banner Canvas Editor
          </h3>
          <div className="flex items-center gap-2">
            <button type="button" onClick={handleAddBanner} className="theme-btn-secondary rounded-xl px-3 py-1.5 text-xs font-semibold">
              Add Banner
            </button>
            <button type="button" onClick={handleRemoveBanner} disabled={bannerForms.length <= 1} className="theme-action-danger rounded-xl px-3 py-1.5 text-xs font-semibold disabled:opacity-50">
              Remove
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          {bannerForms.map((b, idx) => (
            <button
              key={b.id ?? idx}
              type="button"
              onClick={() => setActiveBannerId(b.id)}
              className={`rounded-full border px-3 py-1 text-[10px] font-semibold transition-colors ${
                b.id === activeBannerId
                  ? "bg-primary/20 text-primary border-primary/40"
                  : "bg-surface-2/60 text-text-faint border-border hover:text-text"
              }`}
            >
              {b.title?.slice(0, 28) || `Banner ${idx + 1}`}
            </button>
          ))}
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">Banner Title</label>
            <input
              value={activeBanner?.title ?? ""}
              onChange={(e) => updateActiveBanner({ title: e.target.value })}
              className="w-full px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Subtitle</label>
            <textarea
              rows={2}
              value={activeBanner?.subtitle ?? ""}
              onChange={(e) => updateActiveBanner({ subtitle: e.target.value })}
              className="w-full px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent resize-none"
            />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Badge Text</label>
            <input
              value={activeBanner?.badge_text ?? ""}
              onChange={(e) => updateActiveBanner({ badge_text: e.target.value })}
              className="w-full px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-muted mb-1">CTA Button Text</label>
              <input
                value={activeBanner?.cta_text ?? ""}
                onChange={(e) => updateActiveBanner({ cta_text: e.target.value })}
                placeholder="e.g. Shop Now"
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">CTA URL</label>
              <input
                value={activeBanner?.cta_url ?? ""}
                onChange={(e) => updateActiveBanner({ cta_url: e.target.value })}
                placeholder="e.g. /products?newArrivals=1"
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1">Background Image (legacy)</label>
            <div className="flex items-center gap-3">
              <input
                value={activeBanner?.image_url ?? ""}
                onChange={(e) => updateActiveBanner({ image_url: e.target.value })}
                placeholder="https://... or upload below"
                className="flex-1 px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent"
              />
              <button
                type="button"
                onClick={() => bannerImageRef.current?.click()}
                disabled={bannerImageUploading}
                className="theme-chip-brand flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {bannerImageUploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                Upload
              </button>
              <input
                ref={bannerImageRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setBannerImageUploading(true);
                  try {
                    const form = new FormData();
                    form.append("file", file);
                    const bid = activeBanner?.id;
                    const cc = activeBanner?.country_code || "";
                    const res = await apiFetch(`/admin/banners/${cc}/${bid}/image`, { method: "POST", body: form });
                    if (res.ok) {
                      const data = await res.json();
                      updateActiveBanner({ image_url: data.image_url });
                    }
                  } catch {
                    /* ignore */
                  }
                  setBannerImageUploading(false);
                  e.target.value = "";
                }}
              />
            </div>
            {activeBanner?.image_url && (
              <div className="mt-2 flex items-center gap-2">
                <ImageIcon className="w-3.5 h-3.5 text-text-faint" />
                <span className="text-[11px] text-text-faint truncate max-w-xs">{activeBanner.image_url}</span>
                <button type="button" onClick={() => updateActiveBanner({ image_url: "" })} className="text-danger text-[11px] hover:underline shrink-0">
                  Remove
                </button>
              </div>
            )}
          </div>

          {/* ── Free-form canvas editor ───────────────────────────────── */}
          <div>
            <label className="block text-xs text-text-muted mb-2">
              Design Canvas — add & reshape any element (shapes, text, images, video, buttons)
            </label>
            <BannerCanvasEditor value={activeBanner?.layout ?? null} onChange={updateLayout} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-muted mb-1">Background Video URL (legacy)</label>
              <input
                value={activeBanner?.video_url ?? ""}
                onChange={(e) => updateActiveBanner({ video_url: e.target.value })}
                placeholder="https://...mp4 (optional, plays behind banner)"
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-sm focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-text-muted">Country</label>
              <select
                value={activeBanner?.country_code ?? ""}
                onChange={(e) => updateActiveBanner({ country_code: e.target.value })}
                className="theme-input w-full rounded-xl border px-2 py-1.5 text-xs focus:border-accent focus:outline-none"
              >
                <option value="">Global (all countries)</option>
                {countries.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => updateActiveBanner({ is_active: !activeBanner?.is_active })}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                activeBanner?.is_active ? "bg-warning" : "bg-surface-3"
              }`}
            >
              <span className={`inline-block h-3.5 w-3.5 rounded-full bg-surface-base shadow transition-transform ${activeBanner?.is_active ? "translate-x-4" : "translate-x-1"}`} />
            </button>
            <span className="text-xs text-text-muted">{activeBanner?.is_active ? "Banner is live" : "Banner is hidden"}</span>
          </div>

          <button
            onClick={handleSaveBanners}
            disabled={bannerLoading}
            className="theme-btn-admin flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold disabled:opacity-50"
          >
            {bannerLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            {bannerSaved ? "Saved!" : "Save Banners"}
          </button>
        </div>
      </div>
    </div>
  );
}
