"use client";

import { memo, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "@/lib/icons";
import { resolveImage } from "@/lib/utils";
import { isRtlLocale } from "@shared/localization";
import { useLocaleStore } from "@/lib/localeStore";
import { useEffectStore } from "@/lib/effectStore";
import { BannerCanvasView, type BannerLayout } from "@/components/BannerCanvasEditor";

interface Banner {
  id: number;
  title: string;
  subtitle?: string | null;
  image_url?: string | null;
  video_url?: string | null;
  cta_label?: string | null;
  cta_url?: string | null;
  bg_color?: string | null;
  text_color?: string | null;
  subtitle_color?: string | null;
  btn_bg_color?: string | null;
  btn_text_color?: string | null;
  badge_text?: string | null;
  badge_color?: string | null;
  effect?: string | null;
  layout_json?: string | null;
}

function BannerCarousel({
  position = "hero",
  autoPlay = true,
  interval = 5000,
  className = "",
}: {
  position?: string;
  autoPlay?: boolean;
  interval?: number;
  className?: string;
}) {
  const router = useRouter();
  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);
  const setEffect = useEffectStore((s) => s.setEffect);
  const [banners, setBanners] = useState<Banner[]>([]);
  const [active, setActive] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetchBanners = (url: string) =>
      import("@/lib/api")
        .then(({ apiFetch }) => apiFetch(url))
        .then((r) => (r.ok ? r.json() : []))
        .then((data: Banner[]) => (Array.isArray(data) ? data : []));

    const url = `/banners${position ? `?position=${encodeURIComponent(position)}` : ""}`;
    fetchBanners(url)
      .then((data) => (data.length === 0 && position ? fetchBanners("/banners") : data))
      .then((data) => { if (!cancelled) setBanners(data); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [position]);

  useEffect(() => {
    if (!autoPlay || banners.length <= 1) return;
    const t = setInterval(() => setActive((a) => (a + 1) % banners.length), interval);
    return () => clearInterval(t);
  }, [autoPlay, banners.length, interval]);

  const current = banners[active];

  // Optional free-form canvas layout (admin/employee-designed scene).
  let layout: BannerLayout | null = null;
  if (current?.layout_json) {
    try {
      const parsed = JSON.parse(current.layout_json);
      if (parsed && Array.isArray(parsed.elements)) layout = parsed as BannerLayout;
    } catch {
      layout = null;
    }
  }

  // Drive the global background-effect animation from the active banner's
  // celebration / season / occasion effect. Restore to "none" on unmount.
  useEffect(() => () => setEffect("none"), [setEffect]);
  useEffect(() => {
    setEffect(current?.effect || "none");
  }, [current?.effect, setEffect]);

  if (loading || banners.length === 0) return null;

  const go = (dir: number) => setActive((a) => (a + dir + banners.length) % banners.length);

  return (
    <section className={`relative overflow-hidden rounded-2xl border border-border ${className}`} dir={isRtl ? "rtl" : "ltr"}>
      <AnimatePresence mode="wait">
        <motion.div
          key={current.id}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
          className="relative min-h-[200px] sm:min-h-[260px] md:min-h-[320px] flex items-center"
          style={{ backgroundColor: layout ? "transparent" : current.bg_color || "var(--color-primary)" }}
        >
          {layout && <BannerCanvasView layout={layout} resolve={resolveImage} />}

          {!layout && current.video_url && (
            <video
              className="absolute inset-0 h-full w-full object-cover"
              autoPlay
              muted
              loop
              playsInline
              src={resolveImage(current.video_url)}
            />
          )}
          {!layout && current.image_url && (
            <Image
              src={resolveImage(current.image_url)}
              alt={current.title}
              fill
              sizes="100vw"
              className="absolute inset-0 h-full w-full object-cover opacity-30"
            />
          )}
          {!layout && <div className="absolute inset-0 bg-black/20" />}

          <div className="relative z-10 px-5 sm:px-8 md:px-10 max-w-2xl py-6 sm:py-8">
            {current.badge_text && (
              <span
                className="mb-2 inline-block rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider"
                style={{
                  backgroundColor: current.badge_color || "rgba(255,255,255,0.14)",
                  color: current.text_color || "#fff",
                }}
              >
                {current.badge_text}
              </span>
            )}
            <h3 className="text-lg sm:text-2xl font-bold" style={{ color: current.text_color || "#fff" }}>
              {current.title}
            </h3>
            {current.subtitle && (
              <p className="mt-1 text-xs sm:text-sm" style={{ color: current.subtitle_color || "rgba(255,255,255,0.86)" }}>
                {current.subtitle}
              </p>
            )}
             {current.cta_label && (
              <button
                type="button"
                onClick={() => current.cta_url && router.push(current.cta_url)}
                className={`mt-3 inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-xs sm:text-sm font-bold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary disabled:opacity-50 ${
                  current.btn_bg_color
                    ? ""
                    : "theme-btn-primary shadow-lg shadow-brand/25 hover:shadow-brand/40"
                }`}
                style={
                  current.btn_bg_color
                    ? {
                        backgroundColor: current.btn_bg_color,
                        color: current.btn_text_color || "#fff",
                      }
                    : undefined
                }
              >
                {current.cta_label}
              </button>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {banners.length > 1 && (
        <>
          <button
            type="button"
            onClick={() => go(isRtl ? 1 : -1)}
            className="absolute left-2 sm:left-3 top-1/2 z-20 -translate-y-1/2 rounded-full border border-glass-border bg-glass-panel p-2 text-text shadow-lg backdrop-blur transition-colors hover:bg-glass-panel-hover hover:text-primary"
            aria-label="Previous banner"
          >
            <ChevronLeft className="h-4 w-4 sm:h-5 sm:w-5" />
          </button>
          <button
            type="button"
            onClick={() => go(isRtl ? -1 : 1)}
            className="absolute right-2 sm:right-3 top-1/2 z-20 -translate-y-1/2 rounded-full border border-glass-border bg-glass-panel p-2 text-text shadow-lg backdrop-blur transition-colors hover:bg-glass-panel-hover hover:text-primary"
            aria-label="Next banner"
          >
            <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5" />
          </button>
          <div className="absolute bottom-2 left-1/2 z-20 flex -translate-x-1/2 gap-1.5">
            {banners.map((b, i) => (
              <button
                type="button"
                key={b.id}
                onClick={() => setActive(i)}
                aria-label={`Go to banner ${i + 1}`}
                className={`h-1.5 rounded-full bg-white/60 transition-all hover:bg-white ${
                  i === active ? "w-5 bg-white" : "w-1.5"
                }`}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

export default memo(BannerCarousel);
