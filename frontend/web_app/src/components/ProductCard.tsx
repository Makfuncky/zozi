"use client";

import { useState, memo } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Star, Tag, Maximize2, ShoppingCart, Check, Zap, Clock } from "@/lib/icons";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useCartStore } from "@/lib/cartStore";
import { useToastStore } from "@/lib/toastStore";
import { useRequireAuthAction } from "@/lib/useRequireAuthAction";
import { Product } from "@/lib/types";
import { CARD_BRANDS, resolveImage, fmtSold, productUrl, productUrlFrom } from "@/lib/utils";
import { useLocaleStore } from "@/lib/localeStore";
import { t as translateStatic } from "@/lib/i18n";
import { useTranslateText } from "@/lib/useTranslate";
import TranslatedText from "@/components/TranslatedText";
import QuickViewModal from "@/components/QuickViewModal";
import { useCurrencyStore } from "@/lib/currencyStore";
import { mapProductToCardModel } from "@shared/productCardModel";
import { getProductBadges } from "@shared/productHelpers";
import { formatLocalizedDateTime, isRtlLocale } from "@shared/localization";

const MotionImage = motion.create(Image);

interface ProductCardProps {
  product: Product;
  variant?: "default" | "featured";
  translatedName?: string;
}

function ProductCard({ product, variant = "default", translatedName }: ProductCardProps) {
  const [hovered, setHovered] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [quickViewOpen, setQuickViewOpen] = useState(false);
  const router = useRouter();
  const locale = useLocaleStore((s) => s.locale);
  const formatPrice = useCurrencyStore((s) => s.format);

  const ids = useWishlistStore((s) => s.ids);
  const addWl = useWishlistStore((s) => s.add);
  const removeWl = useWishlistStore((s) => s.remove);
  const inWishlist = ids.includes(product.id);
  const addToCart = useCartStore((s) => s.addItem);
  const addToast = useToastStore((s) => s.addToast);
  const requireAuthAction = useRequireAuthAction();
  const [cartAdded, setCartAdded] = useState(false);
  const isRtl = isRtlLocale(locale);
  const addToCartLabel = useTranslateText(translateStatic("en", "addToCart"));
  const outOfStockLabel = useTranslateText(translateStatic("en", "outOfStock"));
  const quickViewLabel = useTranslateText(translateStatic("en", "quickView"));
  const wishlistLabel = useTranslateText(
    inWishlist
      ? translateStatic("en", "removeFromWishlist")
      : translateStatic("en", "addToWishlist")
  );
  const addedToCartToast = useTranslateText("Added to cart");
  const offerEndsLabel = useTranslateText(
    product.offer_type === "flash_sale" ? "Sale ends" : "Offer until"
  );
  const aiBadgeLabel = useTranslateText("AI");

  const imageUrl = resolveImage(product.image_url);
  const isFeatured = variant === "featured";

  const toggleWl = (e: React.MouseEvent) => { 
    e.preventDefault(); 
    e.stopPropagation(); 
    if (inWishlist) {
      removeWl(product.id);
    } else {
      addWl(product.id);
    }
  };

  const model = mapProductToCardModel(
    product,
    formatPrice,
    (p) => p.supplier || CARD_BRANDS[(p.category || "general").toLowerCase()] || "ZOZI CURATED",
    product.rating,
    product.sales_count
  );

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!model.inStock) return;
    requireAuthAction(() => {
      addToCart(product);
      addToast(addedToCartToast, "success");
      setCartAdded(true);
      setTimeout(() => setCartAdded(false), 2000);
    });
  };

  const outOfStock = !model.inStock;
  const productTags = model.tags;

  const badges = getProductBadges(product, variant);
  const displayName = translatedName || product.name;

  return (
    <>
      <motion.div
        dir={isRtl ? "rtl" : "ltr"}
        className={`group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border glass-product-card shadow-card transition-all duration-300 ${
          isFeatured ? "h-full" : ""
        }`}
        onHoverStart={() => setHovered(true)}
        onHoverEnd={() => setHovered(false)}
        onClick={() => router.push(productUrlFrom(product))}
        whileHover={{ y: -4 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      >
        <div
          className={`relative overflow-hidden bg-surface-1 ${
            isFeatured ? "flex-1 min-h-40 sm:min-h-48" : "aspect-square"
          }`}
        >
          {!imgLoaded && !imgError && (
            <div className="absolute inset-0 animate-shimmer theme-bg-shimmer bg-size-[200%_100%]" />
          )}
          {imgError && (
            <div className="absolute inset-0 product-image-placeholder flex items-center justify-center">
              <svg className="w-10 h-10 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          )}
          <Link href={productUrlFrom(product)} className="relative block w-full h-full" aria-label={`View product: ${displayName}`}>
            {!imgError && (
              <MotionImage
                src={imageUrl}
                alt={displayName}
                fill
                sizes="(max-width: 640px) 50vw, (max-width: 1024px) 25vw, (max-width: 1280px) 20vw, (max-width: 1536px) 16vw, 12vw"
                className="object-cover"
                animate={{ scale: hovered ? 1.05 : 1 }}
                transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
                onLoad={() => setImgLoaded(true)}
                onError={() => setImgError(true)}
              />
            )}
          </Link>

          {badges.length > 0 && (
            <div className={`absolute top-2 flex flex-col gap-1 ${isRtl ? "right-0 items-end" : "left-0 items-start"}`}>
              {badges.slice(0, 2).map((b) =>
                b.shape === "pill" ? (
                  <span
                    key={b.label}
                    className={`text-[7px] sm:text-[8px] font-extrabold px-1 sm:px-1.5 py-0.5 rounded-full uppercase tracking-wider leading-none shadow-md ${isRtl ? "mr-1" : "ml-1"} ${b.cls}`}
                  >
                    <TranslatedText text={b.label} />
                  </span>
                ) : (
                  <span
                    key={b.label}
                    className={`text-[7px] sm:text-[8px] font-extrabold px-1 sm:px-1.5 py-0.5 uppercase tracking-wider leading-none shadow-md ${isRtl ? "pl-2 sm:pl-2.5 rounded-l-full" : "pr-2 sm:pr-2.5 rounded-r-full"} ${b.cls}`}
                    style={{ clipPath: isRtl ? "polygon(12% 0, 100% 0, 100% 100%, 0 100%)" : "polygon(0 0, 100% 0, 88% 100%, 0 100%)" }}
                  >
                    <TranslatedText text={b.label} />
                  </span>
                )
              )}
            </div>
          )}

          {/* Wishlist */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={toggleWl}
            className={`absolute top-1 ${isRtl ? "left-1" : "right-1"} flex h-6 w-6 items-center justify-center rounded-full border transition-all shadow-md ${
              inWishlist
                ? "theme-chip-danger shadow-danger/20"
                : "theme-elevated border-border text-text-faint backdrop-blur-sm hover:border-accent hover:text-accent"
            }`}
            aria-label={wishlistLabel}
          >
            <Heart className="w-2.5 h-2.5" fill={inWishlist ? "currentColor" : "none"} />
          </motion.button>

          {/* AI description badge */}
          {product.ai_description && (
            <div className={`theme-chip-brand absolute top-1 ${isRtl ? "left-8" : "right-8"} flex items-center gap-0.5 rounded-md border px-1.5 py-0.5 shadow-lg shadow-primary/15`}>
              <span className="text-[8px] font-bold leading-none">{aiBadgeLabel}</span>
            </div>
          )}

          <AnimatePresence>
            {hovered && (
              <>
                {productTags.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 6 }}
                    className={`absolute bottom-1 flex items-center gap-1 flex-wrap ${isRtl ? "right-1 justify-end" : "left-1"}`}
                  >
                    <Tag className="w-2.5 h-2.5 text-primary-light shrink-0" />
                    {productTags.map((tag) => (
                      <span key={tag} className="rounded-full border border-primary/20 bg-glass-base px-1.5 py-0.5 text-[8px] font-medium leading-none text-primary-light backdrop-blur-sm">
                        <TranslatedText text={tag} />
                      </span>
                    ))}
                  </motion.div>
                )}
              </>
            )}
          </AnimatePresence>
        </div>

        <div className="flex flex-col gap-0.5 p-2 sm:p-1.5">
          <span className="text-[9px] sm:text-[10px] font-extrabold uppercase tracking-[0.1em] text-primary truncate">{model.brand}</span>

          <Link href={productUrlFrom(product)}>
            <h3 className={`line-clamp-2 font-bold text-text leading-snug transition-colors group-hover:text-primary ${isFeatured ? "text-sm sm:text-base" : "text-[11px] sm:text-[13px]"} ${isRtl ? "text-right" : "text-left"}`}>
              {translatedName ? translatedName : <TranslatedText text={product.name} />}
            </h3>
          </Link>

          <div className="flex items-baseline gap-1.5 flex-wrap mt-0.5">
            <span className={`font-black text-text tracking-tight ${isFeatured ? "text-sm sm:text-base" : "text-xs sm:text-sm"}`}>
              {formatPrice(Number(product.price))}
            </span>
            {product.compare_price && Number(product.compare_price) > Number(product.price) && (
              <span className="text-[8px] sm:text-[9px] line-through text-text-faint">{formatPrice(Number(product.compare_price))}</span>
            )}
            {product.offer_discount_pct && Number(product.offer_discount_pct) > 0 && (
              <span className="text-[7px] sm:text-[8px] font-bold text-accent">
                -{Math.round(Number(product.offer_discount_pct))}%
              </span>
            )}
          </div>

          {/* Flash sale / supplier discount end-time strip */}
          {product.offer_ends_at && (
            <div className={`flex items-center gap-1 text-[7px] sm:text-[8px] font-semibold mt-0.5 ${
              product.offer_type === "flash_sale" ? "text-accent" : "text-text-muted"
            }`}>
              <span>{product.offer_type === "flash_sale" ? <Zap className="w-2.5 h-2.5" /> : <Clock className="w-2.5 h-2.5" />}</span>
              <span>{offerEndsLabel}</span>
              <span className="truncate">
                {formatLocalizedDateTime(product.offer_ends_at, locale, {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-1 pt-1 mt-auto">
            <div className="flex items-center gap-0.5 min-w-0 flex-1">
              <Star className="w-2.5 h-2.5 text-accent fill-current shrink-0" />
              <span className="text-[10px] sm:text-[11px] font-bold text-text truncate">{model.rating.toFixed(1)}</span>
              <span className="text-[8px] sm:text-[9px] text-text-muted truncate">({fmtSold(model.sold)})</span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={(e: React.MouseEvent<HTMLButtonElement>) => { e.preventDefault(); e.stopPropagation(); setQuickViewOpen(true); }}
                className="theme-btn-accent h-7! w-7! sm:h-6! sm:w-6! rounded-lg! p-0! flex shrink-0 items-center justify-center shadow-none"
                aria-label={quickViewLabel}
              >
                <Maximize2 className="w-3 h-3 sm:w-2.5 sm:h-2.5" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.92 }}
                onClick={handleAddToCart}
                disabled={outOfStock}
                aria-label={addToCartLabel}
                className={`min-w-0 rounded-lg! px-2! sm:px-1.5! py-1.5! sm:py-1! flex items-center gap-1 text-[10px] sm:text-[9px] font-bold shrink-0 transition-all ${
                  outOfStock
                    ? "bg-surface-2 text-text-faint cursor-not-allowed"
                    : cartAdded
                    ? "theme-chip-success shadow-success/20"
                    : "theme-btn-primary shadow-none"
                }`}
              >
                <ShoppingCart className="w-3 h-3 sm:w-2.5 sm:h-2.5 shrink-0" />
                <span className="truncate">{cartAdded ? <Check className="w-3 h-3" /> : outOfStock ? outOfStockLabel : addToCartLabel}</span>
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>

      {quickViewOpen && (
        <QuickViewModal product={product} onClose={() => setQuickViewOpen(false)} />
      )}
    </>
  );
}

export default memo(ProductCard);


