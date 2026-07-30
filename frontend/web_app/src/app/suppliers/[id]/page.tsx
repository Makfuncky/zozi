"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  Star, MapPin, Globe, Calendar, Award, ShoppingBag,
  CheckCircle, Shield, Play, ExternalLink,
  Instagram, Facebook, Twitter, Linkedin, Youtube,
  ArrowLeft, MessageSquare, BookOpen, Package, AlertCircle, RefreshCw,
  Video, TrendingUp,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useEffectStore } from "@/lib/effectStore";
import { SupplierPublicProfile, Product } from "@/lib/types";
import { resolveImage, supplierStorefrontPath } from "@/lib/utils";
import { useCurrencyStore } from "@/lib/currencyStore";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { getProductBadges } from "@shared/productHelpers";
import { getPartnerBadgeStyle } from "@shared/statusColors";

// ── Badge pill ────────────────────────────────────────────────────────────────

function SupplierBadge({ level, large = false }: { level: string; large?: boolean }) {
  const badge = getPartnerBadgeStyle(level);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-bold shadow-sm shadow-black/5 ${badge.toneClass} ${large ? "px-4 py-1.5 text-sm" : "px-3 py-1 text-xs"}`}>
      <span className={large ? "text-base" : "text-sm"}>{badge.emoji}</span>
      {badge.label}
    </span>
  );
}

// ── Rating stars ─────────────────────────────────────────────────────────────

function Stars({ rating, count }: { rating: number; count: number }) {
  const hasReviews = count > 0;
  return (
    <span className="flex items-center gap-1 text-sm">
      {Array.from({ length: 5 }, (_, i) => (
        <Star key={i} className={`w-4 h-4 ${hasReviews && i < Math.round(rating) ? "fill-warning text-warning" : "text-border"}`} />
      ))}
      <span className="ml-1 text-text-muted">
        {hasReviews ? `${rating.toFixed(1)} (${count} review${count === 1 ? "" : "s"})` : "No reviews yet"}
      </span>
    </span>
  );
}

// ── Inline stat item ──────────────────────────────────────────────────────────

function StatItem({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string | number }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon className="h-4 w-4 text-primary/60 shrink-0" />
      <span className="font-bold text-text">{value}</span>
      <span className="text-text-faint">{label}</span>
    </div>
  );
}

// ── Mini product card ─────────────────────────────────────────────────────────

function MiniProductCard({ product, formatPrice }: { product: Product; formatPrice: (n: number) => string }) {
  const router = useRouter();
  const badges = getProductBadges(product);
  const img = resolveImage(product.image_url);
  const shortDescription = (product.ai_description || product.description || "").trim();
  const discount = product.compare_price && Number(product.compare_price) > Number(product.price)
    ? Math.round((1 - Number(product.price) / Number(product.compare_price)) * 100)
    : 0;
  return (
    <div
      onClick={() => router.push(`/products/${product.id}`)}
      className="group glass-product-card cursor-pointer overflow-hidden rounded-2xl border border-glass-border bg-glass-base transition-all duration-200 hover:border-primary/40 hover:shadow-card-lg hover:shadow-primary/10 hover:-translate-y-0.5"
    >
      <div className="relative aspect-square bg-surface-2 overflow-hidden">
        <Image src={img} alt={product.name} fill sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw" className="object-cover transition-transform duration-500 group-hover:scale-110" />
        <div className="absolute inset-0 bg-linear-to-t from-black/20 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
        {badges.length > 0 && (
          <span className={`absolute top-2 left-2 text-[9px] sm:text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm ${badges[0].cls}`}>
            {badges[0].label}
          </span>
        )}
        {discount > 0 && (
          <span className="absolute top-2 right-2 rounded-full bg-danger/90 px-2 py-0.5 text-[9px] sm:text-[10px] font-bold text-white shadow-sm">
            -{discount}%
          </span>
        )}
      </div>
      <div className="p-2.5 sm:p-3">
        <p className="mb-1 text-[12px] sm:text-[13px] font-semibold text-text line-clamp-2 group-hover:text-primary transition-colors">{product.name}</p>
        {shortDescription && (
          <p className="mb-1.5 line-clamp-2 text-[10px] leading-[1.4] text-text-faint">{shortDescription}</p>
        )}
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-sm sm:text-base font-extrabold tracking-tight text-text">{formatPrice(Number(product.price))}</span>
          {product.compare_price && Number(product.compare_price) > Number(product.price) && (
            <span className="text-[11px] sm:text-xs text-text-faint line-through">{formatPrice(Number(product.compare_price))}</span>
          )}
        </div>
        {product.rating != null && Number(product.rating) > 0 && (
          <div className="mt-1.5 flex items-center gap-1">
            <Star className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-warning fill-warning" />
            <span className="text-[10px] sm:text-[11px] font-medium text-text-muted">{Number(product.rating).toFixed(1)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Certification card ────────────────────────────────────────────────────────

function CertCard({ cert }: { cert: { title: string; issuer?: string; year?: number; image_url?: string } }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-surface-2 border border-border">
      {cert.image_url ? (
        <Image src={resolveImage(cert.image_url)} alt={cert.title} width={40} height={40} className="rounded object-contain" />
      ) : (
        <Shield className="w-9 h-9 text-primary shrink-0" />
      )}
      <div>
        <p className="text-sm font-semibold text-text">{cert.title}</p>
        {cert.issuer && <p className="text-xs text-text-muted">{cert.issuer}</p>}
        {cert.year && <p className="text-xs text-text-faint">{cert.year}</p>}
      </div>
    </div>
  );
}

function ReviewCard({
  review,
}: {
  review: NonNullable<SupplierPublicProfile["recent_reviews"]>[number];
}) {
  const name = review.customer_name || review.username || "Verified customer";
  const initials = name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div className="group rounded-2xl border border-border bg-surface p-4 transition-all hover:border-primary/20 hover:shadow-md hover:shadow-primary/5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 via-accent/10 to-primary/15 text-sm font-bold text-primary">
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-text">{name}</p>
                {review.is_verified_purchase && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-success/12 px-2 py-0.5 text-[10px] font-semibold text-success">
                    <CheckCircle className="h-3 w-3" />
                    Verified
                  </span>
                )}
              </div>
              {review.product_name && <p className="mt-0.5 text-xs text-text-faint">on {review.product_name}</p>}
            </div>
            <div className="flex items-center gap-1 rounded-lg bg-warning/10 px-2 py-1">
              <Star className="w-3.5 h-3.5 fill-warning text-warning" />
              <span className="text-sm font-bold text-warning">{review.rating.toFixed(1)}</span>
            </div>
          </div>
          <p className="mt-2.5 text-sm leading-relaxed text-text-muted">
            {review.comment || "Customer left a rating without a written review."}
          </p>
          <p className="mt-2.5 text-[11px] text-text-faint">{new Date(review.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}</p>
        </div>
      </div>
    </div>
  );
}

// ── Social link helper ────────────────────────────────────────────────────────

const SOCIAL_ICONS: Record<string, { Icon: React.ElementType; label: string; hoverClass: string }> = {
  instagram: { Icon: Instagram, label: "Instagram", hoverClass: "hover:text-pink-500 hover:border-pink-500/30" },
  facebook:  { Icon: Facebook,  label: "Facebook",  hoverClass: "hover:text-info hover:border-info/30" },
  twitter:   { Icon: Twitter,   label: "Twitter/X", hoverClass: "hover:text-sky-400 hover:border-sky-400/30" },
  linkedin:  { Icon: Linkedin,  label: "LinkedIn",  hoverClass: "hover:text-info hover:border-info/30" },
  youtube:   { Icon: Youtube,   label: "YouTube",   hoverClass: "hover:text-danger hover:border-danger/30" },
  tiktok:    { Icon: ExternalLink, label: "TikTok", hoverClass: "hover:text-text hover:border-border" },
};

function getEmbeddableVideoUrl(url?: string | null): string | null {
  if (!url) return null;

  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.replace(/^www\./, "").toLowerCase();

    if (hostname === "youtube.com" || hostname === "m.youtube.com" || hostname === "youtu.be") {
      const videoId = hostname === "youtu.be"
        ? parsed.pathname.replace(/^\//, "")
        : parsed.searchParams?.get("v") || parsed.pathname.split("/").filter(Boolean).pop();
      return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
    }

    if (hostname === "vimeo.com" || hostname.endsWith(".vimeo.com")) {
      const match = parsed.pathname.match(/\/(\d+)/);
      return match ? `https://player.vimeo.com/video/${match[1]}` : null;
    }
  } catch {
    return null;
  }

  return null;
}

function isHostedVideoFile(url?: string | null): boolean {
  return Boolean(url && /\.(mp4|webm|ogg)(?:$|[?#])/i.test(url));
}

function formatSupplierNarrative(text?: string | null): {
  intro: string | null;
  paragraphs: string[];
  bulletPoints: string[];
} {
  if (!text) {
    return { intro: null, paragraphs: [], bulletPoints: [] };
  }

  const paragraphs: string[] = [];
  const bulletPoints: string[] = [];

  const blocks = text
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .filter(Boolean);

  for (const block of blocks) {
    const lines = block
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    const isBulletBlock = lines.length > 1 && lines.every((line) => /^(?:[-*•]|\d+[.)])\s+/.test(line));

    if (isBulletBlock) {
      bulletPoints.push(...lines.map((line) => line.replace(/^(?:[-*•]|\d+[.)])\s+/, "").trim()).filter(Boolean));
      continue;
    }

    paragraphs.push(lines.join(" "));
  }

  if (paragraphs.length === 0 && bulletPoints.length === 0) {
    return { intro: text.trim(), paragraphs: [], bulletPoints: [] };
  }

  const [intro, ...restParagraphs] = paragraphs;
  return {
    intro: intro ?? null,
    paragraphs: restParagraphs,
    bulletPoints,
  };
}

function getWebsiteHostname(url?: string | null): string | null {
  if (!url) return null;
  try { return new URL(url).hostname.replace(/^www\./, ""); }
  catch { return url.replace(/^https?:\/\//, "").split("/")[0] || null; }
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function SupplierAboutPage() {
  const params = useParams<{ id?: string | string[]; slug?: string | string[] }>();
  const rawSupplierParam = params?.slug ?? params?.id;
  const supplierParam = Array.isArray(rawSupplierParam) ? rawSupplierParam[0] : (rawSupplierParam ?? "");
  const router = useRouter();
  const formatPrice = useCurrencyStore(s => s.format);
  const setBackgroundEffect = useEffectStore(s => s.setEffect);

  const [resolvedSupplierId, setResolvedSupplierId] = useState<string | null>(null);
  const [resolvingSupplierId, setResolvingSupplierId] = useState(true);
  const [supplier, setSupplier] = useState<SupplierPublicProfile | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [totalProducts, setTotalProducts] = useState(0);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [productPage, setProductPage] = useState(0);
  const [videoOpen, setVideoOpen] = useState(false);
  const [videoLoading, setVideoLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [productsError, setProductsError] = useState<string | null>(null);

  type TabId = "about" | "catalog" | "reviews" | "video";
  const [activeTab, setActiveTab] = useState<TabId>("about");
  const productsSectionRef = useRef<HTMLDivElement | null>(null);
  const LIMIT = 8;

  useEffect(() => {
    const previousEffect = useEffectStore.getState().effect;
    if (previousEffect !== "none") setBackgroundEffect("none");
    return () => { useEffectStore.getState().setEffect(previousEffect); };
  }, [setBackgroundEffect]);

  useEffect(() => {
    let cancelled = false;
    if (!supplierParam) {
      setResolvedSupplierId(null); setResolvingSupplierId(false); setLookupError(null); return;
    }
    if (/^\d+$/.test(supplierParam)) {
      setResolvedSupplierId(supplierParam); setResolvingSupplierId(false); setLookupError(null); return;
    }
    setResolvingSupplierId(true);
    setLookupError(null);
    apiFetch(`/suppliers/resolve/${encodeURIComponent(supplierParam)}`)
      .then(async r => {
        if (r.ok) return { kind: "ok" as const, data: await r.json() };
        if (r.status === 404) return { kind: "missing" as const, data: null };
        return { kind: "error" as const, data: null };
      })
      .then(result => {
        if (cancelled) return;
        setResolvedSupplierId(result.data?.id ? String(result.data.id) : null);
        if (result.kind === "error") setLookupError("We could not load this supplier storefront right now.");
      })
      .catch(() => { if (!cancelled) { setResolvedSupplierId(null); setLookupError("We could not load this supplier storefront right now."); } })
      .finally(() => { if (!cancelled) setResolvingSupplierId(false); });
    return () => { cancelled = true; };
  }, [supplierParam]);

  useEffect(() => {
    if (!resolvedSupplierId) {
      setSupplier(null); setProfileError(null);
      if (!resolvingSupplierId) setLoadingProfile(false);
      return;
    }
    setLoadingProfile(true);
    setProfileError(null);
    apiFetch(`/suppliers/${resolvedSupplierId}`)
      .then(async r => {
        if (r.ok) return { kind: "ok" as const, data: await r.json() };
        if (r.status === 404) return { kind: "missing" as const, data: null };
        return { kind: "error" as const, data: null };
      })
      .then(result => {
        setSupplier(result.data);
        setProfileError(result.kind === "error" ? "Supplier profile is temporarily unavailable." : null);
        setLoadingProfile(false);
      })
      .catch(() => { setSupplier(null); setProfileError("Supplier profile is temporarily unavailable."); setLoadingProfile(false); });
  }, [resolvedSupplierId, resolvingSupplierId]);

  useEffect(() => {
    if (!supplier?.slug || !supplierParam) return;
    if (supplierParam === supplier.slug) return;
    router.replace(supplierStorefrontPath(supplier), { scroll: false });
  }, [router, supplier, supplierParam]);

  const loadProducts = useCallback((page: number) => {
    if (!resolvedSupplierId) return;
    setLoadingProducts(true);
    setProductsError(null);
    apiFetch(`/suppliers/${resolvedSupplierId}/products?limit=${LIMIT}&offset=${page * LIMIT}`)
      .then(async r => { if (r.ok) return r.json(); throw new Error("catalog-error"); })
      .then(data => { setProducts(data.items ?? []); setTotalProducts(data.total ?? 0); setLoadingProducts(false); })
      .catch(() => { setProducts([]); setTotalProducts(0); setProductsError("We could not load this supplier catalog right now."); setLoadingProducts(false); });
  }, [resolvedSupplierId]);

  useEffect(() => { setVideoOpen(false); setVideoLoading(false); setProductPage(0); setProductsError(null); }, [resolvedSupplierId]);

  useEffect(() => {
    if (!resolvedSupplierId) { setProducts([]); setTotalProducts(0); setLoadingProducts(false); return; }
    loadProducts(productPage);
  }, [loadProducts, productPage, resolvedSupplierId]);

  const handleRetryPage = () => window.location.reload();
  const handleRetryProducts = () => loadProducts(productPage);
  const handleProductPageChange = (nextPage: number) => {
    setProductPage(nextPage);
    productsSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const handleTabChange = (tab: TabId) => setActiveTab(tab);

  if (resolvingSupplierId || loadingProfile) return <LoadingSkeleton />;

  const blockingErrorMessage = lookupError || profileError;
  if (blockingErrorMessage) return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md rounded-3xl border border-border bg-surface p-6 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-danger/10 text-danger">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-text mb-2">Supplier storefront unavailable</h2>
        <p className="text-sm leading-6 text-text-muted">{blockingErrorMessage}</p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Button variant="primary" onClick={handleRetryPage}>
            <RefreshCw className="h-4 w-4" /> Retry
          </Button>
          <button onClick={() => router.back()} className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-text transition-colors hover:bg-surface-2">
            Go back
          </button>
        </div>
      </div>
    </div>
  );

  if (!supplier) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-text mb-2">Supplier not found</h2>
        <button onClick={() => router.back()} className="theme-btn-primary px-6 py-2 text-sm mt-4">Go back</button>
      </div>
    </div>
  );

  // ── Derived values ────────────────────────────────────────────────────────
  const memberYear        = new Date(supplier.member_since).getFullYear();
  const hasBanner         = Boolean(supplier.banner_url);
  const hasLogo           = Boolean(supplier.logo_url);
  const hasCerts          = Boolean(supplier.certifications?.length);
  const hasSocial         = Boolean(supplier.social_links && Object.values(supplier.social_links).some(Boolean));
  const hasVideo          = Boolean(supplier.video_url);
  const hasRecentReviews  = Array.isArray(supplier.recent_reviews) && supplier.recent_reviews.length > 0;
  const displayName       = supplier.business_name || supplier.username;
  const location          = [supplier.city, supplier.region, supplier.country].filter(Boolean).join(", ");
  const totalPages        = Math.ceil(totalProducts / LIMIT);
  const resolvedVideoUrl  = supplier.video_url ? resolveImage(supplier.video_url) : "";
  const embeddedVideoUrl  = getEmbeddableVideoUrl(supplier.video_url);
  const hostedVideoFile   = isHostedVideoFile(resolvedVideoUrl);
  const narrative         = formatSupplierNarrative(supplier.about_us || supplier.bio);
  const websiteHostname   = getWebsiteHostname(supplier.website);
  const averageRatingValue = supplier.total_reviews > 0 ? supplier.avg_rating.toFixed(1) : "New";
  const badgeInfo         = getPartnerBadgeStyle(supplier.badge_level);
  const credScore         = supplier.credibility_score ?? 0;

  // Navigation tabs
  const tabs: Array<{ id: TabId; label: string; icon: React.ElementType; count?: number }> = [
    { id: "about",   label: "About",    icon: BookOpen },
    { id: "catalog", label: "Products", icon: Package,  count: totalProducts > 0 ? totalProducts : undefined },
    { id: "reviews", label: "Reviews",  icon: Star,     count: supplier.total_reviews > 0 ? supplier.total_reviews : undefined },
    ...(hasVideo ? [{ id: "video" as TabId, label: "Video", icon: Video }] : []),
  ];

  return (
    <div className="min-h-screen bg-background pb-16">

      {/* ─── 1. HERO COVER PHOTO ─────────────────────────────────────────── */}
      {hasBanner ? (
        <div className="relative h-52 w-full overflow-hidden sm:h-64 lg:h-80">
          <>
            <Image
              src={resolveImage(supplier.banner_url!)}
              alt={`${displayName} cover photo`}
              fill
              className="object-cover"
              priority
            />
            <div className="absolute inset-0 bg-linear-to-t from-black/55 via-black/10 to-transparent" />
          </>

          <button
            onClick={() => router.back()}
            className="absolute top-4 left-4 z-10 flex items-center gap-2 rounded-full bg-black/40 px-3.5 py-2 text-xs font-semibold text-white shadow-md backdrop-blur-sm transition-all hover:bg-black/60"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back
          </button>
        </div>
      ) : (
        <div className="mx-auto flex max-w-5xl px-4 pt-4 sm:px-6 lg:px-8">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-2 text-xs font-semibold text-text shadow-sm transition-all hover:bg-surface-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back
          </button>
        </div>
      )}

      {/* ─── 2. PROFILE IDENTITY CARD ────────────────────────────────────── */}
      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className={`${hasBanner ? "-mt-10 sm:-mt-14" : "mt-4"} overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl shadow-black/10`}>
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/[0.04] via-transparent to-primary/[0.03]" />

          <div className="relative px-5 pt-4 pb-5 sm:px-8 sm:pt-5 sm:pb-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">

              {/* Avatar — overlaps the cover */}
              <div className={`relative ${hasBanner ? "-mt-14 sm:-mt-18" : "mt-0"} shrink-0 h-22 w-22 sm:h-28 sm:w-28 overflow-hidden rounded-2xl border-4 border-surface bg-surface-2 shadow-xl ring-2 ring-primary/10`}>
                {hasLogo ? (
                  <Image
                    src={resolveImage(supplier.logo_url!)}
                    alt={displayName}
                    width={112}
                    height={112}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-primary/25 via-surface to-primary/20 text-3xl font-extrabold text-primary sm:text-4xl">
                    {displayName.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              {/* Identity info */}
              <div className="flex-1 min-w-0 sm:pb-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h1 className="wrap-break-word text-[1.6rem] font-extrabold leading-tight text-text sm:text-[2rem]">
                    {displayName}
                  </h1>
                  {supplier.is_verified && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-info/12 px-2.5 py-1 text-xs font-bold text-info">
                      <CheckCircle className="h-3.5 w-3.5" />
                      Verified
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-3 mb-2.5">
                  <SupplierBadge level={supplier.badge_level} large />
                  <Stars rating={supplier.avg_rating} count={supplier.total_reviews} />
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-text-muted">
                  {location && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-primary/60 shrink-0" />
                      {location}
                    </span>
                  )}
                  {websiteHostname && supplier.website && (
                    <a href={supplier.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-primary hover:underline">
                      <Globe className="h-3.5 w-3.5 shrink-0" />
                      {websiteHostname}
                    </a>
                  )}
                  {(supplier.established_year || memberYear) && (
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-primary/60 shrink-0" />
                      Est. {supplier.established_year || memberYear}
                    </span>
                  )}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex shrink-0 flex-wrap gap-2">
                <Link
                  href={`/chatbot?supplier=${supplier.id}`}
                  className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/35"
                >
                  <MessageSquare className="h-4 w-4" />
                  Chat
                </Link>
                {supplier.website && (
                  <a
                    href={supplier.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-text transition-all hover:border-primary/30 hover:bg-surface-2"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Website
                  </a>
                )}
              </div>
            </div>

            {/* Stats divider row */}
            <div className="relative mt-5 flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-border pt-4">
              <StatItem icon={Package}     label="Products"     value={supplier.product_count.toLocaleString()} />
              <StatItem icon={ShoppingBag} label="Sales"        value={supplier.total_sales.toLocaleString()} />
              <StatItem icon={TrendingUp}  label="Trust Score"  value={`${credScore}/100`} />
              <StatItem icon={Calendar}    label="Member since" value={String(memberYear)} />
              {hasCerts && <StatItem icon={Award} label="Certifications" value={supplier.certifications.length} />}
            </div>
          </div>

          {/* Credibility progress bar at card bottom */}
          {credScore > 0 && (
            <div className="h-1 w-full bg-surface-2">
              <div
                className="h-full bg-gradient-to-r from-primary via-primary to-accent transition-all duration-700"
                style={{ width: `${credScore}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {/* ─── 3. TAB NAVIGATION ───────────────────────────────────────────── */}
      <div className="sticky top-0 z-30 mt-3 border-b border-border bg-background/95 backdrop-blur-md">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="flex gap-0 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {tabs.map(tab => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`relative flex items-center gap-2 px-4 py-3.5 text-sm font-semibold whitespace-nowrap transition-colors ${isActive ? "text-primary" : "text-text-muted hover:text-text"}`}
                >
                  <tab.icon className={`h-4 w-4 ${isActive ? "text-primary" : ""}`} />
                  {tab.label}
                  {tab.count !== undefined && (
                    <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold leading-none ${isActive ? "bg-primary/12 text-primary" : "bg-surface-2 text-text-faint"}`}>
                      {tab.count}
                    </span>
                  )}
                  {isActive && <span className="absolute bottom-0 inset-x-0 h-0.5 bg-primary rounded-t-full" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ─── 4. TAB CONTENT ──────────────────────────────────────────────── */}
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 pt-6">

        {/* ── ABOUT TAB ── */}
        {activeTab === "about" && (
          <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">

            {/* ── Left sidebar ── */}
            <div className="space-y-4">

              {/* Business Info card */}
              <div className="overflow-hidden rounded-2xl border border-border bg-surface p-4 space-y-3">
                <h2 className="text-sm font-bold text-text">Business Info</h2>
                {supplier.business_type && (
                  <div className="flex items-center gap-3 rounded-xl bg-surface-2/60 px-3 py-2.5 text-sm text-text-muted">
                    <Shield className="w-4 h-4 text-primary shrink-0" />
                    <span className="capitalize">{supplier.business_type.replace(/_/g, " ")}</span>
                  </div>
                )}
                {location && (
                  <div className="flex items-center gap-3 rounded-xl bg-surface-2/60 px-3 py-2.5 text-sm text-text-muted">
                    <MapPin className="w-4 h-4 text-primary shrink-0" />
                    <span>{location}</span>
                  </div>
                )}
                {supplier.website && (
                  <div className="flex items-center gap-3 rounded-xl bg-surface-2/60 px-3 py-2.5 text-sm text-text-muted">
                    <Globe className="w-4 h-4 text-primary shrink-0" />
                    <a href={supplier.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline truncate">
                      {websiteHostname}
                    </a>
                  </div>
                )}
                {(supplier.established_year || memberYear) && (
                  <div className="flex items-center gap-3 rounded-xl bg-surface-2/60 px-3 py-2.5 text-sm text-text-muted">
                    <Calendar className="w-4 h-4 text-primary shrink-0" />
                    <span>Est. {supplier.established_year || memberYear}</span>
                  </div>
                )}
                {credScore > 0 && (
                  <div className="pt-1">
                    <div className="flex items-center justify-between text-xs text-text-muted mb-2">
                      <span className="font-semibold">Credibility Score</span>
                      <span className="font-extrabold text-text">{credScore}/100</span>
                    </div>
                    <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-primary via-primary to-accent"
                        style={{ width: `${credScore}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Badge spotlight */}
              {supplier.badge_level && supplier.badge_level !== "none" && (
                <div className={`overflow-hidden rounded-2xl border p-4 ${badgeInfo.toneClass}`}>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-60 mb-3">Partner Status</p>
                  <div className="flex items-center gap-3.5">
                    <span className="text-4xl leading-none">{badgeInfo.emoji}</span>
                    <div>
                      <p className="text-lg font-extrabold leading-none">{badgeInfo.label}</p>
                      <p className="mt-1 text-xs opacity-60 leading-5">Based on performance &amp; customer reviews</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Certifications */}
              {hasCerts && (
                <div className="overflow-hidden rounded-2xl border border-border bg-surface p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-sm font-bold text-text">Certifications</h2>
                    <span className="theme-chip-success rounded-full px-2.5 py-1 text-[10px] font-bold">{supplier.certifications.length}</span>
                  </div>
                  <div className="space-y-2.5">
                    {supplier.certifications.map((cert, i) => <CertCard key={i} cert={cert} />)}
                  </div>
                </div>
              )}

              {/* Social links */}
              {hasSocial && (
                <div className="overflow-hidden rounded-2xl border border-border bg-surface p-4">
                  <h2 className="mb-3 text-sm font-bold text-text">Follow Us</h2>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(supplier.social_links).map(([platform, url]) => {
                      if (!url) return null;
                      const entry = SOCIAL_ICONS[platform];
                      if (!entry) return null;
                      const { Icon, label, hoverClass } = entry;
                      return (
                        <a
                          key={platform}
                          href={url as string}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-text-muted transition-all ${hoverClass}`}
                          aria-label={label}
                        >
                          <Icon className="w-4 h-4" />
                          <span>{label}</span>
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Chat CTA */}
              <div className="overflow-hidden rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/8 via-surface to-accent/8 p-4">
                <div className="mb-3 flex items-start gap-3">
                  <div className="shrink-0 rounded-xl bg-primary/10 p-2 text-primary">
                    <MessageSquare className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-text text-sm">Have a Question?</h3>
                    <p className="text-xs text-text-muted mt-0.5 leading-5">Chat directly — your details are never shared.</p>
                  </div>
                </div>
                <Link
                  href={`/chatbot?supplier=${supplier.id}`}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
                >
                  <MessageSquare className="w-4 h-4" />
                  Start Chat
                </Link>
              </div>
            </div>

            {/* ── Right: Brand Story + quick-nav ── */}
            <div className="space-y-5">
              <section className="overflow-hidden rounded-2xl border border-border bg-surface">
                <div className="border-b border-border bg-gradient-to-br from-primary/10 via-transparent to-accent/8 px-5 py-5">
                  <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-primary/80">Brand Story</p>
                  <h2 className="mt-2 text-[1.7rem] font-extrabold text-text">About {displayName}</h2>
                  {narrative.intro ? (
                    <p className="mt-2.5 text-sm leading-7 text-text-muted sm:text-base">{narrative.intro}</p>
                  ) : (
                    <p className="mt-2.5 text-sm leading-6 text-text-muted">
                      Explore this supplier&apos;s business background, certifications, and trust profile.
                    </p>
                  )}
                </div>

                {(narrative.paragraphs.length > 0 || narrative.bulletPoints.length > 0) ? (
                  <div className="px-5 py-5 space-y-4">
                    {narrative.paragraphs.length > 0 && (
                      <div className="space-y-3 text-sm leading-7 text-text-muted sm:text-[15px]">
                        {narrative.paragraphs.map((p, i) => <p key={i}>{p}</p>)}
                      </div>
                    )}
                    {narrative.bulletPoints.length > 0 && (
                      <div className="rounded-xl border border-border bg-surface-2/60 p-4">
                        <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-text-faint">What We Offer</h3>
                        <ul className="grid gap-2.5 sm:grid-cols-2">
                          {narrative.bulletPoints.map((point, i) => (
                            <li key={i} className="flex items-start gap-3 rounded-xl border border-border bg-background/60 px-3.5 py-3 text-sm leading-6 text-text-muted">
                              <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="px-5 py-5">
                    <div className="flex items-start gap-3 rounded-xl border border-dashed border-border bg-surface-2/40 p-3.5">
                      <BookOpen className="h-8 w-8 text-primary/40 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-semibold text-text-muted">No brand story yet</p>
                        <p className="text-xs text-text-faint mt-1 leading-5">
                          This supplier has not published their brand story. You can still explore their catalog and reviews.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </section>

              {/* Tab shortcut cards */}
              <div className="grid gap-3 sm:grid-cols-3">
                <button
                  onClick={() => handleTabChange("catalog")}
                  className="group flex items-center gap-3 rounded-2xl border border-border bg-surface p-4 text-left transition-all hover:border-primary/30 hover:shadow-md hover:shadow-primary/5"
                >
                  <div className="rounded-xl bg-primary/10 p-2.5 text-primary transition-colors group-hover:bg-primary/18">
                    <Package className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text">{supplier.product_count} Products</p>
                    <p className="text-xs text-text-faint">Browse catalog →</p>
                  </div>
                </button>
                <button
                  onClick={() => handleTabChange("reviews")}
                  className="group flex items-center gap-3 rounded-2xl border border-border bg-surface p-4 text-left transition-all hover:border-warning/30 hover:shadow-md hover:shadow-warning/6"
                >
                  <div className="rounded-xl bg-warning/10 p-2.5 text-warning transition-colors group-hover:bg-warning/18">
                    <Star className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text">{averageRatingValue} Rating</p>
                    <p className="text-xs text-text-faint">{supplier.total_reviews} reviews →</p>
                  </div>
                </button>
                {hasVideo && (
                  <button
                    onClick={() => handleTabChange("video")}
                    className="group flex items-center gap-3 rounded-2xl border border-border bg-surface p-4 text-left transition-all hover:border-primary/30 hover:shadow-md hover:shadow-primary/6"
                  >
                    <div className="rounded-xl bg-primary/10 p-2.5 text-primary transition-colors group-hover:bg-primary/18">
                      <Video className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-text">Brand Video</p>
                      <p className="text-xs text-text-faint">Watch now →</p>
                    </div>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── CATALOG TAB ── */}
        {activeTab === "catalog" && (
          <div ref={productsSectionRef}>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">Storefront Catalog</p>
                <h2 className="flex items-center gap-2 text-xl font-bold text-text">
                  Products
                  <span className="theme-chip-info rounded-xl px-2.5 py-0.5 text-sm font-bold">{totalProducts}</span>
                </h2>
              </div>
            </div>

            {productsError ? (
              <div className="rounded-2xl border border-danger/20 bg-danger/8 px-4 py-5">
                <div className="flex items-start gap-3">
                  <div className="rounded-xl bg-danger/10 p-2 text-danger"><AlertCircle className="h-4 w-4" /></div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-text">Catalog temporarily unavailable</p>
                    <p className="mt-1 text-sm text-text-muted">{productsError}</p>
                  </div>
                  <Button variant="danger" onClick={handleRetryProducts}>
                    <RefreshCw className="h-3.5 w-3.5" /> Retry
                  </Button>
                </div>
              </div>
            ) : loadingProducts ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="animate-pulse bg-surface-2 rounded-xl aspect-square" />
                ))}
              </div>
            ) : products.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="rounded-2xl bg-surface-2 p-6 mb-4">
                  <ShoppingBag className="w-12 h-12 text-primary/30" />
                </div>
                <p className="text-lg font-semibold text-text-muted">No products listed yet</p>
                <p className="text-sm text-text-faint mt-1">This supplier hasn&apos;t added products yet.</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {products.map(p => <MiniProductCard key={p.id} product={p} formatPrice={formatPrice} />)}
                </div>
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-3 mt-8">
                    <button
                      onClick={() => handleProductPageChange(Math.max(0, productPage - 1))}
                      disabled={productPage === 0}
                      className="px-5 py-2.5 rounded-xl border border-border text-sm font-semibold text-text transition-all hover:border-primary/30 hover:bg-surface-2 disabled:opacity-40 disabled:pointer-events-none"
                    >
                      Previous
                    </button>
                    <span className="text-sm font-semibold text-text-muted px-2">
                      Page {productPage + 1} of {totalPages}
                    </span>
                    <button
                      onClick={() => handleProductPageChange(Math.min(totalPages - 1, productPage + 1))}
                      disabled={productPage >= totalPages - 1}
                      className="px-5 py-2.5 rounded-xl border border-border text-sm font-semibold text-text transition-all hover:border-primary/30 hover:bg-surface-2 disabled:opacity-40 disabled:pointer-events-none"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── REVIEWS TAB ── */}
        {activeTab === "reviews" && (
          <div>
            <div className="mb-6 overflow-hidden rounded-2xl border border-border bg-surface">
              <div className="border-b border-border bg-gradient-to-r from-warning/12 via-transparent to-primary/10 px-5 py-5 sm:px-6">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-text-faint">Customer Reviews</p>
                <h2 className="mt-2 text-[1.7rem] font-extrabold text-text">What customers say about {displayName}</h2>
                <p className="mt-1.5 text-sm text-text-muted">
                  Badge level and trust score reflect order fulfilment history, document verifications, and customer review quality.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-3 px-5 py-5 sm:px-6">
                <div className="relative overflow-hidden rounded-2xl border border-border bg-surface-2/60 p-4 transition-all hover:border-warning/25 hover:shadow-md">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">Average Rating</p>
                  <p className="mt-2 text-4xl font-extrabold tracking-tight text-text">{averageRatingValue}</p>
                  <p className="mt-1.5 text-sm text-text-muted">
                    {supplier.total_reviews > 0 ? `${supplier.total_reviews} review${supplier.total_reviews === 1 ? "" : "s"}` : "No reviews yet"}
                  </p>
                  {supplier.total_reviews > 0 && (
                    <div className="mt-2.5 flex gap-0.5">
                      {Array.from({ length: 5 }, (_, i) => (
                        <Star key={i} className={`h-4 w-4 ${i < Math.round(supplier.avg_rating) ? "fill-warning text-warning" : "text-border"}`} />
                      ))}
                    </div>
                  )}
                </div>

                <div className="relative overflow-hidden rounded-2xl border border-border bg-surface-2/60 p-4 transition-all hover:border-primary/25 hover:shadow-md">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">Trust Score</p>
                  <p className="mt-2 text-4xl font-extrabold tracking-tight text-text">
                    {credScore}<span className="text-xl font-bold text-text-muted">/100</span>
                  </p>
                  <p className="mt-1.5 text-sm text-text-muted">{badgeInfo.emoji} {badgeInfo.label}</p>
                  <div className="mt-2.5 h-1.5 rounded-full bg-surface overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-primary to-primary" style={{ width: `${credScore}%` }} />
                  </div>
                </div>

                <div className="relative overflow-hidden rounded-2xl border border-border bg-surface-2/60 p-4 transition-all hover:border-success/25 hover:shadow-md">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">Store Activity</p>
                  <p className="mt-2 text-4xl font-extrabold tracking-tight text-text">{supplier.total_sales.toLocaleString()}</p>
                  <p className="mt-1.5 text-sm text-text-muted">
                    {supplier.product_count.toLocaleString()} product{supplier.product_count === 1 ? "" : "s"} listed
                  </p>
                </div>
              </div>
            </div>

            {hasRecentReviews ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {supplier.recent_reviews!.map(review => (
                  <ReviewCard key={review.id} review={review} />
                ))}
              </div>
            ) : (
              <div className="flex items-start gap-4 rounded-2xl border border-dashed border-border bg-surface-2/40 px-5 py-6">
                <div className="rounded-xl bg-warning/10 p-3 text-warning shrink-0">
                  <Star className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-text-muted">No customer reviews yet</p>
                  <p className="mt-1.5 text-sm leading-6 text-text-muted">
                    This storefront is live, but customers haven&apos;t posted written reviews yet.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── VIDEO TAB ── */}
        {activeTab === "video" && hasVideo && (
          <div>
            <div className="mb-5">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">Brand Video</p>
              <h2 className="text-xl font-bold text-text">{displayName} — Official Video</h2>
            </div>

            {embeddedVideoUrl ? (
              <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
                {!videoOpen ? (
                  <button
                    onClick={() => { setVideoOpen(true); setVideoLoading(true); }}
                    className="group relative flex aspect-video w-full items-center justify-center overflow-hidden bg-surface-2"
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-accent/15" />
                    <div className="relative z-10 flex flex-col items-center gap-4">
                      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/90 shadow-2xl shadow-primary/40 transition-all group-hover:scale-110 group-hover:shadow-primary/60">
                        <Play className="h-8 w-8 text-white ml-1" />
                      </div>
                      <span className="rounded-full border border-white/20 bg-black/35 px-4 py-1.5 text-sm font-semibold text-white backdrop-blur-sm">
                        Play Brand Video
                      </span>
                    </div>
                  </button>
                ) : (
                  <div className="relative aspect-video w-full overflow-hidden">
                    {videoLoading && (
                      <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/75 backdrop-blur-sm">
                        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-text-muted">
                          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          Loading video…
                        </div>
                      </div>
                    )}
                    <iframe
                      src={embeddedVideoUrl}
                      title={`${displayName} brand video`}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      onLoad={() => setVideoLoading(false)}
                      className="absolute inset-0 h-full w-full"
                    />
                  </div>
                )}
                <div className="border-t border-border px-5 py-4">
                  <p className="text-sm font-semibold text-text">{displayName} — Brand Showcase</p>
                  <p className="mt-1 text-xs text-text-faint">Official supplier video. Content is the responsibility of the supplier.</p>
                </div>
              </div>
            ) : hostedVideoFile ? (
              <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
                <video controls className="w-full">
                  <source src={resolvedVideoUrl} />
                </video>
                <div className="border-t border-border px-5 py-4">
                  <p className="text-sm font-semibold text-text">{displayName} — Brand Showcase</p>
                </div>
              </div>
            ) : (
              <a
                href={resolvedVideoUrl || supplier.video_url!}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl border border-border px-5 py-3 text-sm font-semibold text-primary transition-colors hover:border-primary/30"
              >
                <ExternalLink className="h-4 w-4" />
                Open supplier video
              </a>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
