"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Star,
  Heart,
  ShoppingCart,
  Minus,
  Plus,
  Shield,
  RotateCcw,
  ArrowLeft,
  ArrowRight,
  MessageSquare,
  Send,
  Tag,
  Share2,
  Check,
  Package,
  Globe,
  Calendar,
  Award,
  CheckCircle,
  MapPin,
  ExternalLink,
  Play,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { Product, Review, SupplierPublicProfile } from "@/lib/types";
import { resolveImage, parseProductId, supplierStorefrontPath } from "@/lib/utils";
import Image from "next/image";
import { useCartStore } from "@/lib/cartStore";
import { useRequireAuthAction } from "@/lib/useRequireAuthAction";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useToastStore } from "@/lib/toastStore";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import Recommendations from "@/components/Recommendations";
import RecentlyViewed from "@/components/RecentlyViewed";
import { useRecentlyViewedStore } from "@/lib/recentlyViewedStore";
import { useLocaleStore } from "@/lib/localeStore";
import TranslatedText from "@/components/TranslatedText";
import { useTranslateText, useTranslateTexts } from "@/lib/useTranslate";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";
import { getPartnerBadgeStyle } from "@shared/statusColors";

function isVideoAsset(value: string): boolean {
  return /\.(mp4|webm|ogg)(\?|#|$)/i.test(value);
}

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

function formatVerificationStatus(status?: string | null): string {
  if (!status) return "Public supplier profile";
  return status
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function normalizeVariantValue(value?: string | null): string {
  return (value || "").trim().toLowerCase();
}

function resolveSelectedVariant(variants: NonNullable<Product["variants"]>, selectedSize: string, selectedColor: string) {
  const normalizedSize = normalizeVariantValue(selectedSize);
  const normalizedColor = normalizeVariantValue(selectedColor);
  if (!normalizedSize && !normalizedColor) return null;

  return variants.find((variant) => {
    const variantSize = normalizeVariantValue(variant.size || variant.title || "");
    const variantColor = normalizeVariantValue(variant.color || "");
    const attributeValues = Object.values(variant.attributes || {}).map((value) => normalizeVariantValue(value));
    const sizeMatches = !normalizedSize || normalizedSize === variantSize || attributeValues.includes(normalizedSize);
    const colorMatches = !normalizedColor || normalizedColor === variantColor || attributeValues.includes(normalizedColor);
    return sizeMatches && colorMatches;
  }) || null;
}

export default function ProductDetailPage() {
  const params = useParams();
  const { id: rawId } = params ?? {};
  const router = useRouter();
  // Support both /products/42 and /products/42-product-name
  const id = Array.isArray(rawId) ? rawId[0] : (rawId ?? "");
  const numericId = parseProductId(id);
  // Opaque share/affiliate links use an 8-char hex slug_hash: /products/{hash}
  // (distinguished from a numeric id or a /products/{id}-{slug} fallback).
  const trimmedId = String(id).trim();
  const isHash = /^[0-9a-f]{8}$/i.test(trimmedId) && !/^\d+$/.test(trimmedId);
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [addedMsg, setAddedMsg] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [hoverRating, setHoverRating] = useState(0);
  const [shared, setShared] = useState(false);
  const [selectedSize, setSelectedSize] = useState<string>("");
  const [selectedColor, setSelectedColor] = useState<string>("");
  const [supplierProfile, setSupplierProfile] = useState<SupplierPublicProfile | null>(null);
  const [productVideos, setProductVideos] = useState<Array<{ video_url?: string | null; thumbnail_url?: string | null; title?: string | null }>>([]);
  const [activeImg, setActiveImg] = useState(0);

  const { isLoggedIn } = useAuth();
  const requireAuthAction = useRequireAuthAction();
  const locale = useLocaleStore((s) => s.locale);
  const tr = useLocaleStore((s) => s.t);
  const isRtl = isRtlLocale(locale);
  const trackRecent = useRecentlyViewedStore((s) => s.track);
  const formatPrice = useCurrencyStore((s) => s.format);
  const translatedProductName = useTranslateText(product?.name ?? "");
  const displayDescription = product?.ai_description || product?.description || "";
  const translatedDescription = useTranslateText(displayDescription);
  const [shareProductLabel, copiedLinkLabel, addedToCartLabel, reviewSubmittedLabel, reviewFailedLabel, soldByLabel, visitStoreLabel, productVideosLabel, productsLabel, customerLabel, selectColorLabel] = useTranslateTexts([
    "Share product",
    "Link copied to clipboard",
    "Added to cart",
    "Review submitted, thank you!",
    "Could not submit review",
    "Sold by",
    "Visit Store",
    "Product Videos",
    "products",
    "Customer",
    "Please select a color",
  ]);

  const addToCart = useCartStore((s) => s.addItem);
  const ids = useWishlistStore((s) => s.ids);
  const addWl = useWishlistStore((s) => s.add);
  const removeWl = useWishlistStore((s) => s.remove);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    if (!id) return;
    const productUrl = isHash ? `/products/h/${encodeURIComponent(trimmedId)}` : `/products/${numericId}`;
    setLoading(true);
    apiFetch(productUrl)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setProduct(data);
        setLoading(false);
        if (!data?.id) return;
        // Fetch public supplier summary in parallel
        if (data?.supplier_id) {
          apiFetch(`/suppliers/${data.supplier_id}`)
            .then((r) => (r.ok ? r.json() : null))
            .then((s) => s && setSupplierProfile(s))
            .catch(() => {});
        }
        trackRecent({
          id: data.id,
          name: data.name,
          price: data.price,
          image_url: data.image_url,
          category: data.category,
          rating: data.rating,
          viewedAt: Date.now(),
        });
        // Fetch linked product videos (ProductVideo records)
        apiFetch(`/product-videos/product/${data.id}`)
          .then((r) => (r.ok ? r.json() : null))
          .then((vdata) => { if (vdata?.videos?.length) setProductVideos(vdata.videos); })
          .catch(() => {});
        // Fetch reviews for this product
        apiFetch(`/reviews/products/${data.id}`)
          .then((r) => (r.ok ? r.json() : []))
          .then((rv) => { setReviews(rv); setReviewsLoading(false); })
          .catch(() => setReviewsLoading(false));
      })
      .catch(() => setLoading(false));
  }, [id, numericId, trackRecent]);

  // Dynamic SEO: update page title and meta description when product loads
  useEffect(() => {
    if (!product) return;
    const prevTitle = document.title;
    document.title = `${product.name} — ZOZI`;
    const productPrice = Number(product.price ?? 0);
    // Update meta description
    let metaDesc = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement("meta");
      metaDesc.name = "description";
      document.head.appendChild(metaDesc);
    }
    metaDesc.content = product.description
      ? product.description.slice(0, 160)
      : `Buy ${product.name} on ZOZI. ${formatPrice(productPrice)}.`;
    return () => {
      document.title = prevTitle;
    };
  }, [product, formatPrice]);

  if (loading) return <LoadingSkeleton />;
  if (!product)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-text mb-2">
            {tr("productNotFound")}
          </h2>
          <p className="text-text-muted mb-4">
            {tr("productRemoved")}
          </p>
          <button
            onClick={() => router.push("/products")}
            className="theme-btn-primary px-6 py-3 text-sm font-semibold"
          >
            {tr("browseProducts")}
          </button>
        </div>
      </div>
    );

  const variants = (product.variants || []).filter((variant) => variant.is_active !== false);
  const selectedVariant = variants.length > 0 ? resolveSelectedVariant(variants, selectedSize, selectedColor) : null;
  const imageUrl = resolveImage(selectedVariant?.media_url || product.image_url);
  const productVideoUrl = product.video_url ? resolveImage(product.video_url) : "";
  const productEmbeddedVideoUrl = getEmbeddableVideoUrl(product.video_url);

  // Build full image gallery (main + additional)
  const allImages: string[] = [imageUrl];
  const galleryVideos: string[] = [];
  if (product.additional_images) {
    try {
      const extras: string[] = JSON.parse(product.additional_images);
      extras.forEach((p) => {
        const resolved = resolveImage(p);
        if (isVideoAsset(p)) {
          galleryVideos.push(resolved);
          return;
        }
        allImages.push(resolved);
      });
    } catch {}
  }

  // Parse sizes
  const sizes: string[] = variants.length > 0
    ? Array.from(new Set(variants.map((variant) => (variant.size || variant.title || "").trim()).filter(Boolean)))
    : (() => {
    if (!product.sizes) return [];
    try { return JSON.parse(product.sizes); } catch { return []; }
  })();

  // Parse colors (comma-separated string)
  const colors: string[] = variants.length > 0
    ? Array.from(new Set(variants.map((variant) => (variant.color || "").trim()).filter(Boolean)))
    : (product.color
      ? product.color.split(",").map((c) => c.trim()).filter(Boolean)
      : []);

  // CSS color map for common color names → actual CSS value
  const colorMap: Record<string, string> = {
    red: "var(--color-red)", blue: "var(--color-blue)", green: "var(--color-green)", yellow: "var(--color-yellow)",
    orange: "var(--color-orange)", purple: "var(--color-purple)", pink: "var(--color-pink)", white: "var(--color-white)",
    black: "var(--color-black)", gray: "var(--color-gray)", grey: "var(--color-gray)", brown: "var(--color-brown)",
    navy: "var(--color-navy)", teal: "var(--color-teal)", coral: "var(--color-coral)", beige: "var(--color-beige)",
    cream: "var(--color-cream)", gold: "var(--color-gold)", silver: "var(--color-silver)", indigo: "var(--color-indigo)",
  };

  const inWishlist = ids.includes(product.id);
  const stock = selectedVariant?.stock ?? product.stock ?? 0;
  const outOfStock = stock === 0;
  const price = Number(selectedVariant?.price ?? product.price ?? 0);
  const rating =
    typeof product.rating === "number"
      ? product.rating
      : reviews.length > 0
      ? reviews.reduce((sum, review) => sum + Number(review.rating || 0), 0) / reviews.length
      : 0;
  const comparePriceValue = Number(product.compare_price ?? 0);
  const comparePrice = comparePriceValue > price ? comparePriceValue : null;
  const discount = comparePrice
    ? Math.round(((comparePrice - price) / comparePrice) * 100)
    : null;

  const handleAdd = () => {
    if (sizes.length > 0 && !selectedSize) {
      addToast(tr("pleaseSelectSize"), "error");
      return;
    }
    if (colors.length > 0 && !selectedColor) {
      addToast(selectColorLabel, "error");
      return;
    }
    // Guests may add to a local guest cart; checkout will prompt for sign-in.
    addToCart({
      ...product,
      price,
      stock,
      image_url: selectedVariant?.media_url || product.image_url,
    }, {
      quantity: qty,
      selectedSize: selectedVariant ? (selectedVariant.size || selectedVariant.title || selectedSize) : selectedSize,
      selectedColor: selectedVariant ? (selectedVariant.color || selectedColor) : selectedColor,
    });
    addToast(addedToCartLabel, "success");
    setAddedMsg(true);
    setTimeout(() => setAddedMsg(false), 2000);
  };

  const handleWishlist = () => {
    requireAuthAction(() => {
      if (inWishlist) {
        removeWl(product.id);
      } else {
        addWl(product.id);
      }
    });
  };

  const handleShare = () => {
    const url = window.location.href;
    if (navigator.share) {
      navigator.share({ title: translatedProductName || product.name, url });
    } else {
      navigator.clipboard.writeText(url);
      setShared(true);
      addToast(copiedLinkLabel, "success");
      setTimeout(() => setShared(false), 2000);
    }
  };

  const productTags = product.tags
    ? product.tags.split(",").map((t) => t.trim()).filter(Boolean)
    : [];

  const supplierStoreHref = supplierProfile ? supplierStorefrontPath(supplierProfile) : "/products";
  const supplierDisplayName = supplierProfile?.business_name || supplierProfile?.username || "";
  const supplierStory = supplierProfile?.about_us || supplierProfile?.bio || "";
  const supplierLocation = [supplierProfile?.city, supplierProfile?.region, supplierProfile?.country]
    .filter(Boolean)
    .join(", ");
  const supplierMemberYear = supplierProfile?.member_since
    ? new Date(supplierProfile.member_since).getFullYear()
    : null;
  const supplierVideoUrl = supplierProfile?.video_url ? resolveImage(supplierProfile.video_url) : "";
  const supplierEmbeddedVideoUrl = getEmbeddableVideoUrl(supplierProfile?.video_url);
  const supplierSocialEntries = supplierProfile
    ? (Object.entries(supplierProfile.social_links || {}).filter(([, value]) => Boolean(value)) as Array<[string, string]>)
    : [];
  const supplierCertifications = Array.isArray(supplierProfile?.certifications)
    ? supplierProfile.certifications
    : [];

  const submitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoggedIn) { router.push("/login"); return; }
    setReviewSubmitting(true);
    try {
      const res = await apiFetch(`/reviews/products/${product?.id ?? numericId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating: reviewRating, comment: reviewComment }),
      });
      if (res.ok) {
        const newReview = await res.json();
        setReviews((prev) => [newReview, ...prev]);
        setReviewComment("");
        setReviewRating(5);
        addToast(reviewSubmittedLabel, "success");
      } else {
        const err = await res.json();
        addToast(err.detail || reviewFailedLabel, "error");
      }
    } catch {
      addToast(reviewFailedLabel, "error");
    } finally {
      setReviewSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen" dir={isRtl ? "rtl" : "ltr"}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          {/* Back */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-xs text-text-muted hover:text-text mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 rtl:hidden" />
          <ArrowRight className="w-4 h-4 hidden rtl:block" />
          {tr("back")}
        </button>

          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,38vw)_minmax(0,1fr)_minmax(0,260px)] gap-5 xl:grid-cols-[minmax(0,40vw)_minmax(0,1fr)_minmax(0,300px)] xl:gap-6">
          {/* Image gallery */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex flex-col gap-3 lg:sticky lg:top-6 self-start lg:col-start-1 lg:row-start-1"
          >
            <div className="flex gap-3">
              {/* Thumbnail strip — only when multiple images */}
              {allImages.length > 1 && (
                <div className="flex flex-col gap-2 w-16 sm:w-20 shrink-0">
                  {allImages.slice(0, 5).map((img, i) => (
                    <button
                      key={i}
                      onClick={() => setActiveImg(i)}
                      className={`relative aspect-square w-full rounded-xl overflow-hidden border-2 transition-all ${
                        activeImg === i
                          ? "border-primary ring-2 ring-primary/20"
                          : "border-border hover:border-border-light"
                      }`}
                    >
                      <Image src={img} alt={`View ${i + 1}`} fill sizes="72px" className="object-cover" />
                    </button>
                  ))}
                </div>
              )}

              {/* Main image */}
              <div className="group relative flex-1 aspect-[4/5] min-h-[480px] rounded-2xl overflow-hidden bg-surface-2 border border-border cursor-zoom-in">
                <Image
                  src={allImages[activeImg] || imageUrl}
                  alt={product.name}
                  fill
                  sizes="(max-width: 1024px) 90vw, 38vw"
                  className="object-contain transition-all duration-500 ease-out group-hover:scale-125 group-hover:transition-transform group-hover:duration-500"
                  priority
                />
                {discount != null && discount > 0 && (
                  <span className="theme-chip-danger absolute top-4 start-4 rounded-lg px-2 py-1 text-[11px] font-bold">
                    -{discount}%
                  </span>
                )}
              </div>
            </div>

            {galleryVideos.length > 0 && (
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase tracking-wider text-text-muted">{productVideosLabel}</div>
                {galleryVideos.map((videoUrl, index) => (
                  <video key={`${videoUrl}-${index}`} controls className="w-full rounded-2xl border border-border bg-surface-2">
                    <source src={videoUrl} />
                  </video>
                ))}
              </div>
            )}
          </motion.div>

          {/* Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex flex-col min-w-0 lg:col-start-2 lg:row-start-1"
          >
            {/* Category + Share */}
            <div className="flex items-center justify-between mb-1">
              <TranslatedText
                text={product.category || "General"}
                as="p"
                className="theme-status-info text-[11px] font-bold uppercase tracking-[0.15em]"
              />
              <button
                onClick={handleShare}
                title={shareProductLabel}
                className="flex items-center gap-1 text-[11px] text-text-muted hover:text-text transition-colors"
              >
                {shared ? <Check className="theme-status-success h-3.5 w-3.5" /> : <Share2 className="w-3.5 h-3.5" />}
                {shared ? tr("copied") : tr("share")}
              </button>
            </div>

            <TranslatedText
              text={translatedProductName || product.name}
              as="h1"
              className="text-2xl font-bold text-text mb-2"
            />

            {/* Tags */}
            {productTags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                <Tag className="w-3 h-3 text-text-faint mt-0.5" />
                {productTags.map((tag) => (
                  <span
                    key={tag}
                    className="cursor-pointer rounded-full border border-border bg-surface-2 px-2 py-0.5 text-[10px] font-medium text-text-muted transition-colors hover:border-primary hover:bg-primary/20 hover:text-primary"
                    onClick={() => router.push(`/products?search=${encodeURIComponent(tag)}`)}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Rating */}
            <div className="flex items-center gap-2 mb-3">
              <div className="flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`w-3.5 h-3.5 ${
                      i < Math.round(rating)
                        ? "theme-status-warning fill-current"
                        : "text-text-faint"
                    }`}
                  />
                ))}
              </div>
              <span className="text-xs font-semibold text-text">
                {rating > 0 ? rating.toFixed(1) : "No ratings yet"}
              </span>
              <span className="text-[11px] text-text-faint">
                ({reviews.length} {tr("reviews").toLowerCase()} · {product.sales_count ?? 0} {tr("sold")})
              </span>
            </div>

            {/* Price */}
            <div className="flex items-baseline gap-3 mb-4">
              <span className="text-2xl font-bold text-text">
                {formatPrice(price)}
              </span>
              {comparePrice && (
                <>
                  <span className="text-base text-text-faint line-through">
                    {formatPrice(comparePrice)}
                  </span>
                  {discount !== null && (
                    <span className="theme-chip-success rounded-md px-1.5 py-0.5 text-[11px] font-semibold">
                      {tr("saveOff")} {discount}%
                    </span>
                  )}
                </>
              )}
            </div>

            {/* Supplier Product Description — sits in the center-right column, aligned with the buttons */}
            <section className="mb-5 rounded-2xl border border-border bg-surface-1 p-5 sm:p-6">
              <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-text-faint">Description</h2>
              <p className="mt-3 text-sm leading-relaxed text-text-muted max-w-none">
                {translatedDescription || displayDescription || "The supplier has not published a detailed description yet."}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text-muted">
                  Category: {product.category || "General"}
                </span>
                {product.materials && (
                  <span className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text-muted">
                    {tr("materials")}: {product.materials}
                  </span>
                )}
                {sizes.length > 0 && (
                  <span className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text-muted">
                    {sizes.length} size option{sizes.length === 1 ? "" : "s"}
                  </span>
                )}
                {colors.length > 0 && (
                  <span className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text-muted">
                    {colors.length} color option{colors.length === 1 ? "" : "s"}
                  </span>
                )}
                {selectedVariant && (
                  <span className="rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                    {selectedVariant.sku || selectedVariant.product_code || selectedVariant.title}
                  </span>
                )}
              </div>
            </section>

            {(productVideoUrl || galleryVideos.length > 0 || productVideos.length > 0) && (
              <div className="mb-4 rounded-2xl border border-border bg-surface-1 p-4">
                <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-text-faint">{productVideosLabel}</h2>
                <div className="mt-3 space-y-3">
                  {productVideoUrl && (
                    productEmbeddedVideoUrl ? (
                      <iframe
                        src={productEmbeddedVideoUrl}
                        title={`${product.name} video`}
                        className="aspect-video w-full rounded-2xl border border-border"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    ) : (
                      <video controls className="w-full rounded-2xl border border-border bg-surface-2">
                        <source src={productVideoUrl} />
                      </video>
                    )
                  )}
                  {galleryVideos.map((videoUrl, index) => (
                    <video key={`${videoUrl}-${index}`} controls className="w-full rounded-2xl border border-border bg-surface-2">
                      <source src={videoUrl} />
                    </video>
                  ))}
                  {productVideos.map((video, index) => {
                    const vUrl = video.video_url ? resolveImage(video.video_url) : "";
                    const embedded = getEmbeddableVideoUrl(video.video_url);
                    if (!vUrl) return null;
                    return embedded ? (
                      <iframe
                        key={`pv-${index}`}
                        src={embedded}
                        title={video.title || `${product.name} video`}
                        className="aspect-video w-full rounded-2xl border border-border"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    ) : (
                      <video key={`pv-${index}`} controls className="w-full rounded-2xl border border-border bg-surface-2">
                        <source src={vUrl} />
                      </video>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Size Selector */}
            {sizes.length > 0 && (
              <div className="mb-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                  {tr("sizes")}
                  {selectedSize && (
                    <span className="theme-status-info ml-2 normal-case font-normal">— {selectedSize} {tr("selectSize").includes("select") ? "" : ""}</span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2">
                  {sizes.map((size) => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(selectedSize === size ? "" : size)}
                      className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
                        selectedSize === size
                          ? "border-primary bg-primary text-on-brand shadow-primary/50"
                          : "border-border bg-surface-1 text-text-muted hover:border-border-light hover:text-text"
                      }`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Color Selector */}
            {colors.length > 0 && (
              <div className="mb-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                  {tr("color")}
                  {selectedColor && (
                    <span className="theme-status-info ml-2 font-normal capitalize">— {selectedColor}</span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2">
                  {colors.map((color) => {
                    const cssColor = colorMap[color.toLowerCase()] ?? color;
                    const isLight = ["white", "cream", "beige", "silver", "yellow", "gold"].includes(color.toLowerCase());
                    return (
                      <button
                        key={color}
                        title={color}
                        onClick={() => setSelectedColor(selectedColor === color ? "" : color)}
                        className={`relative w-8 h-8 rounded-full border-2 transition-all ${
                          selectedColor === color
                            ? "border-primary ring-2 ring-primary/20 scale-110"
                            : "border-border hover:border-primary hover:scale-105"
                        }`}
                        style={{ backgroundColor: cssColor }}
                      >
                        {selectedColor === color && (
                          <span
                            className={`absolute inset-0 flex items-center justify-center text-[10px] font-bold ${
                              isLight ? "text-text" : "text-white"
                            }`}
                          >
                            ✓
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Material (quick info if available) */}
            {product.materials && (
              <div className="mb-3 flex items-center gap-2 text-xs text-text-muted">
                <span className="font-semibold uppercase tracking-wider">{tr("materials")}:</span>
                <span className="text-text">{product.materials}</span>
              </div>
            )}

            {selectedVariant && (
              <div className="mb-4 grid grid-cols-1 gap-2 rounded-2xl border border-border bg-surface-1 p-3 text-xs text-text-muted sm:grid-cols-3">
                <div>
                  <p className="font-semibold uppercase tracking-wider text-text-faint">SKU</p>
                  <p className="mt-1 text-text">{selectedVariant.sku || "-"}</p>
                </div>
                <div>
                  <p className="font-semibold uppercase tracking-wider text-text-faint">Product Code</p>
                  <p className="mt-1 text-text">{selectedVariant.product_code || "-"}</p>
                </div>
                <div>
                  <p className="font-semibold uppercase tracking-wider text-text-faint">Barcode</p>
                  <p className="mt-1 text-text">{selectedVariant.barcode || "-"}</p>
                </div>
              </div>
            )}

            {/* Stock + Brand row */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    outOfStock ? "bg-danger" : stock < 10 ? "bg-warning" : "bg-success"
                  }`}
                />
                <span
                  className={`text-xs font-medium ${
                    outOfStock
                      ? "theme-status-danger"
                      : stock < 10
                      ? "theme-status-warning"
                      : "theme-status-success"
                  }`}
                >
                  {outOfStock
                    ? tr("outOfStock")
                    : stock < 10
                    ? `${tr("only")} ${stock} ${tr("left")}`
                    : `${tr("inStock")} (${stock} ${tr("units")})`}
                </span>
              </div>
              {product.brand && (
                <span className="flex items-center gap-1 text-[11px] text-text-faint">
                  <Package className="w-3 h-3 text-primary/60" />
                  {product.brand}
                </span>
              )}
            </div>

            {/* Quantity + Actions */}
            <div className="flex flex-wrap items-stretch gap-3 mb-6">
              <div className="theme-elevated flex items-center overflow-hidden rounded-2xl border border-border/80 p-1 shadow-card-sm">
                <button
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="rounded-xl p-2.5 text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <span className="w-10 text-center text-xs font-semibold text-text">
                  {qty}
                </span>
                <button
                  onClick={() => setQty((q) => q + 1)}

                  className="rounded-xl p-2.5 text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <div className="flex flex-1 min-w-[220px] gap-3">
                <button
                  onClick={handleAdd}
                  disabled={outOfStock}
                  className={`flex-1 px-6 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                    outOfStock
                      ? "bg-surface-2 text-text-faint cursor-not-allowed"
                      : "btn-place-order"
                  }`}
                >
                  <ShoppingCart className="w-4 h-4" />
                  {addedMsg ? tr("addedMsg") : outOfStock ? tr("soldOut") : tr("addToCart")}
                </button>

                <Button variant="accent" onClick={handleShare}>
                  {shared ? <Check className="w-3.5 h-3.5" /> : <Share2 className="w-3.5 h-3.5" />}
                  {shared ? tr("copied") : tr("share")}
                </Button>
              </div>

              <button
                onClick={() =>
                  handleWishlist()
                }
                className={`p-2.5 rounded-xl border transition-colors ${
                  inWishlist
                    ? "theme-chip-danger shadow-danger/20"
                    : "theme-elevated border-border-light text-text-muted hover:border-danger hover:text-danger"
                }`}
              >
                <Heart
                  className="w-4 h-4"
                  fill={inWishlist ? "currentColor" : "none"}
                />
              </button>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap gap-2">
              {(() => {
                const returnWindowDays = Math.max(10, Number(product.return_window_days ?? 10) || 10);
                return [
                  { icon: RotateCcw, label: `${returnWindowDays}-day returns after delivery` },
                ];
              })().map((badge) => (
                <span
                  key={badge.label}
                  className="theme-elevated inline-flex items-center gap-1.5 rounded-full border border-border/80 px-3 py-1.5 text-[11px] font-semibold text-text-muted shadow-card-sm"
                >
                  <badge.icon className="theme-status-info h-3.5 w-3.5" />
                  {badge.label}
                </span>
              ))}
            </div>

            {/* Supplier storefront profile */}
            {supplierProfile && (
              <section className="theme-panel relative mt-5 overflow-hidden rounded-[1.7rem] border border-border/80 p-4 shadow-card-lg">
                <div className="pointer-events-none absolute -right-8 -top-10 h-28 w-28 rounded-full bg-primary/10 blur-3xl" />
                <div className="flex items-start gap-4">
                  <div className="theme-elevated flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-border/80 shadow-card-sm">
                    {supplierProfile.logo_url ? (
                      <Image
                        src={resolveImage(supplierProfile.logo_url)}
                        alt={supplierDisplayName}
                        width={56}
                        height={56}
                        className="object-cover h-full w-full"
                      />
                    ) : (
                      <span className="text-brand font-bold text-base">
                        {supplierDisplayName.slice(0, 2).toUpperCase()}
                      </span>
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] text-text-muted mb-0.5">{soldByLabel}</p>
                    <a href={supplierStoreHref} className="block truncate text-sm font-semibold text-text hover:text-primary transition-colors">
                      {supplierDisplayName}
                    </a>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-text-muted">
                      {supplierProfile.badge_level && supplierProfile.badge_level !== "none" && (() => {
                        const badge = getPartnerBadgeStyle(supplierProfile.badge_level);
                        return (
                          <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-bold ${badge.toneClass}`}>
                            {badge.emoji} {badge.label}
                          </span>
                        );
                      })()}
                      {supplierProfile.is_verified && (
                        <span className="theme-chip-success inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-semibold">
                          <CheckCircle className="h-3 w-3" /> Verified
                        </span>
                      )}
                      {supplierProfile.avg_rating > 0 && (
                        <span className="theme-elevated inline-flex items-center gap-1 rounded-full border border-border/80 px-2 py-0.5">
                          <Star className="h-3 w-3 fill-warning text-warning" />
                          {supplierProfile.avg_rating.toFixed(1)}
                        </span>
                      )}
                      <span className="theme-elevated rounded-full border border-border/80 px-2 py-0.5">{supplierProfile.product_count} {productsLabel}</span>
                    </div>
                  </div>

                  <a
                    href={supplierStoreHref}
                    className="theme-btn-secondary shrink-0 rounded-xl border px-3 py-1.5 text-[11px] font-semibold text-text-muted"
                  >
                    {visitStoreLabel} {isRtl ? "←" : "→"}
                  </a>
                </div>

                {supplierStory && (
                  <p className="mt-4 text-sm leading-relaxed text-text-muted">{supplierStory}</p>
                )}

                <div className="mt-4 grid gap-2 text-xs text-text-muted sm:grid-cols-2">
                  {supplierLocation && (
                    <div className="theme-elevated inline-flex items-center gap-2 rounded-xl border border-border/80 px-3 py-2">
                      <MapPin className="h-3.5 w-3.5 text-primary" />
                      <span>{supplierLocation}</span>
                    </div>
                  )}
                  {supplierProfile.website && (
                    <a
                      href={supplierProfile.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="theme-elevated inline-flex items-center gap-2 rounded-xl border border-border/80 px-3 py-2 transition-colors hover:border-primary"
                    >
                      <Globe className="h-3.5 w-3.5 text-primary" />
                      <span className="truncate">{supplierProfile.website.replace(/^https?:\/\//, "")}</span>
                    </a>
                  )}
                  {supplierMemberYear && (
                    <div className="theme-elevated inline-flex items-center gap-2 rounded-xl border border-border/80 px-3 py-2">
                      <Calendar className="h-3.5 w-3.5 text-primary" />
                      <span>Member since {supplierMemberYear}</span>
                    </div>
                  )}
                  <div className="theme-elevated inline-flex items-center gap-2 rounded-xl border border-border/80 px-3 py-2">
                    <Shield className="h-3.5 w-3.5 text-primary" />
                    <span>{formatVerificationStatus(supplierProfile.verification_status)}</span>
                  </div>
                </div>

                {supplierCertifications.length > 0 && (
                  <div className="mt-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Supplier Certifications</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {supplierCertifications.slice(0, 3).map((cert, index) => (
                        <span key={`${cert.title}-${index}`} className="theme-elevated inline-flex items-center gap-1 rounded-full border border-border/80 px-2.5 py-1 text-[11px] text-text-muted">
                          <Award className="h-3 w-3 text-primary" />
                          {cert.title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {(supplierEmbeddedVideoUrl || supplierVideoUrl) && (
                  <div className="mt-4">
                    <a
                      href={supplierVideoUrl || supplierProfile.video_url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="theme-elevated inline-flex items-center gap-2 rounded-xl border border-border/80 px-3 py-2 text-xs font-semibold text-text-muted transition-colors hover:border-primary hover:text-primary"
                    >
                      <Play className="h-3.5 w-3.5" />
                      {supplierEmbeddedVideoUrl ? "Watch supplier video" : "Open supplier video"}
                    </a>
                  </div>
                )}

                {supplierSocialEntries.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {supplierSocialEntries.slice(0, 4).map(([platform, url]) => (
                      <a
                        key={platform}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="theme-elevated rounded-full border border-border/80 px-2.5 py-1 text-[11px] font-semibold capitalize text-text-muted transition-colors hover:border-primary hover:text-primary"
                      >
                        {platform}
                      </a>
                    ))}
                  </div>
                )}

                <div className="mt-4 flex flex-wrap gap-2">
                  <Link
                    href={`/chatbot?supplier=${supplierProfile.id}`}
                    className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold shadow-none"
                  >
                    <MessageSquare className="h-3.5 w-3.5" />
                    Chat with Supplier
                  </Link>
                  <a
                    href={supplierStoreHref}
                    className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-semibold text-text-muted"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    View Storefront
                  </a>
                </div>
                <p className="mt-2 text-[11px] text-text-faint">
                  Supplier chat is monitored for safety and keeps your personal contact details private.
                </p>
              </section>
            )}
          </motion.div>

          {/* You May Also Like — sticky desktop sidebar (right column, top row) */}
            <div className="hidden lg:flex flex-col gap-3 sticky top-6 self-start max-h-screen overflow-y-auto lg:col-start-3 lg:row-start-1 min-w-0">
            <Recommendations currentCategory={product.category} excludeIds={[product.id]} compact />
          </div>
           {/* Reviews — full-width row below the image/info/recommendations/description */}
           <div className="lg:col-start-1 lg:row-start-2 lg:col-span-3 border-t border-border pt-8 mt-2">
             {/* Reviews — two columns: Type your review | Public reviews */}
             <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
               {/* Left: Type your review */}
               <div className="p-5 rounded-2xl theme-elevated border">
                 <h3 className="text-sm font-bold text-text mb-4 flex items-center gap-2">
                   <Send className="theme-status-info h-4 w-4" />
                   {tr("writeReview")}
                 </h3>
                 {!isLoggedIn ? (
                   <p className="text-text-faint text-sm">
                     <button onClick={() => router.push("/login")} className="theme-link-brand">{tr("signIn")}</button>{" "}{tr("toLeaveReview")}
                   </p>
                 ) : (
                   <form onSubmit={submitReview} className="space-y-4">
                     <div>
                       <p className="mb-2 text-xs text-text-muted">{tr("rating")}</p>
                       <div className="flex gap-1">
                         {[1, 2, 3, 4, 5].map((star) => (
                           <button key={star} type="button" onMouseEnter={() => setHoverRating(star)} onMouseLeave={() => setHoverRating(0)} onClick={() => setReviewRating(star)}>
                             <Star className={`w-6 h-6 transition-colors ${star <= (hoverRating || reviewRating) ? "theme-status-warning fill-current" : "text-text-faint"}`} />
                           </button>
                         ))}
                       </div>
                     </div>
                     <div>
                       <label className="mb-1 block text-xs text-text-muted">{tr("reviewCommentLabel")}</label>
                       <textarea value={reviewComment} onChange={(e) => setReviewComment(e.target.value)} rows={3}
                         placeholder={tr("reviewPlaceholder")}
                         className="theme-input w-full resize-none rounded-xl border px-3 py-2 text-sm focus:border-primary focus:outline-none transition-colors" />
                       </div>
                       <button type="submit" disabled={reviewSubmitting}
                         className="theme-btn-primary flex items-center gap-2 px-5 py-2 text-sm font-bold disabled:opacity-50">
                         {reviewSubmitting ? <div className="btn-spinner" /> : <Send className="w-4 h-4" />}
                         {tr("submitReview")}
                       </button>
                     </form>
                   )}
                 </div>

               {/* Right: Public reviews */}
               <div>
                 <h3 className="text-sm font-bold text-text mb-4 flex items-center gap-2">
                   <MessageSquare className="theme-status-info h-4 w-4" />
                   {tr("reviews")} ({reviews.length})
                 </h3>

                 {/* Review summary */}
                 {reviews.length > 0 && (
                   <div className="flex items-center gap-6 p-4 rounded-2xl theme-elevated border mb-4">
                     <div className="text-center">
                       <p className="text-4xl font-bold text-text">{rating.toFixed(1)}</p>
                       <div className="flex items-center justify-center gap-0.5 mt-1">
                         {Array.from({ length: 5 }).map((_, i) => (
                           <Star key={i} className={`w-3.5 h-3.5 ${i < Math.round(rating) ? "theme-status-warning fill-current" : "text-text-faint"}`} />
                         ))}
                       </div>
                       <p className="text-[11px] text-text-faint mt-1">{reviews.length} {tr("reviews").toLowerCase()}</p>
                     </div>
                     <div className="flex-1 space-y-1">
                       {[5, 4, 3, 2, 1].map((star) => {
                         const count = reviews.filter((r) => Math.round(r.rating) === star).length;
                         const pct = reviews.length > 0 ? (count / reviews.length) * 100 : 0;
                         return (
                           <div key={star} className="flex items-center gap-2">
                             <span className="text-[10px] text-text-faint w-4">{star}</span>
                             <div className="flex-1 h-1.5 rounded-full bg-surface-3 overflow-hidden">
                               <div className="h-full rounded-full bg-warning transition-all" style={{ width: `${pct}%` }} />
                             </div>
                             <span className="text-[10px] text-text-faint w-5 text-right">{count}</span>
                           </div>
                         );
                       })}
                     </div>
                   </div>
                 )}

                 {/* Review list */}
                 {reviewsLoading ? (
                   <p className="text-text-faint text-sm">Loading reviews…</p>
                 ) : reviews.length === 0 ? (
                   <div className="text-center py-10 text-text-muted">
                     <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-40" />
                     <p className="text-sm">{tr("noReviewsYet")}</p>
                   </div>
                 ) : (
                   <div className="grid gap-4">
                     {reviews.map((r) => (
                       <div key={r.id} className="p-4 rounded-2xl theme-elevated border">
                         <div className="flex items-center justify-between mb-2">
                           <span className="text-xs font-semibold text-text">{r.username || `${customerLabel} #${r.user_id}`}</span>
                           <div className="flex items-center gap-1">
                             {Array.from({ length: 5 }).map((_, i) => (
                               <Star key={i} className={`w-3 h-3 ${i < Math.round(r.rating) ? "theme-status-warning fill-current" : "text-text-faint"}`} />
                             ))}
                             <span className="text-[11px] text-text-faint ml-1">{r.rating.toFixed(1)}</span>
                           </div>
                         </div>
                         {r.comment && <p className="text-sm text-text-muted leading-relaxed">{r.comment}</p>}
                         {r.is_verified_purchase && (
                           <span className="theme-chip-success mt-1 inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-bold">
                             <Check className="w-2.5 h-2.5" /> {tr("verifiedPurchase")}
                           </span>
                         )}
                         <p className="text-[11px] text-text-faint mt-2">{formatLocalizedDate(r.created_at, locale, { year: "numeric", month: "short", day: "numeric" })}</p>
                       </div>
                     ))}
                   </div>
                 )}
               </div>
             </div>
          </div>
        </div>
      </div>

      {product && (
        <div className="lg:hidden max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
          <Recommendations
            currentCategory={product.category}
            excludeIds={[product.id]}
          />
        </div>
      )}

      {product && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
          <RecentlyViewed excludeId={product.id} />
        </div>
      )}

    </main>
  );
}
