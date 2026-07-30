"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShoppingBag,
  Heart,
  User,
  Menu,
  X,
  LogOut,
  Package,
  ClipboardList,
  Settings,
  Store,
  LayoutDashboard,
  Bell,
  ChevronDown,
  Search
} from "@/lib/icons";
import HeaderSearchBar from "./HeaderSearchBar";
import MobileSearchOverlay from "./MobileSearchOverlay";
import { useAuth } from "@/lib/useAuth";
import { useCartStore } from "@/lib/cartStore";
import { useWishlistStore } from "@/lib/wishlistStore";
import ThemeToggle from "./ThemeToggle";
import Logo from "./Logo";
import { useNotificationStore } from "@/lib/notificationStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { apiFetch } from "@/lib/api";
import type { TranslationKey } from "@/lib/i18n";
import { useAuthModalStore } from "@/lib/authModalStore";
import { LANGUAGE_OPTIONS, type Locale } from "@shared/localization";
import type { SupplierPublicSummary } from "@/lib/types";

type PublicCountryOption = {
  code: string;
  name: string;
  currency?: string;
  is_active: boolean;
};

const MAIN_NAV: { href: string; labelKey: TranslationKey }[] = [
  { href: "/products", labelKey: "shop" },
  { href: "/suppliers", labelKey: "suppliers" },
  { href: "/offers", labelKey: "offers" },
  { href: "/help", labelKey: "help" },
];

const GUEST_NAV: { href: string; labelKey: TranslationKey }[] = MAIN_NAV;

const CUSTOMER_NAV: { href: string; labelKey: TranslationKey }[] = [
  ...MAIN_NAV,
  { href: "/orders", labelKey: "myOrders" },
  { href: "/wishlist", labelKey: "wishlist" },
  { href: "/profile", labelKey: "profile" },
];

// Returns true for routes that should NOT render the global storefront header.
// Login/minimal pages and the full panel areas (admin / supplier / logistics)
// render their own chrome via PanelShell, so the marketing header is hidden
// there to avoid a stacked, overlapping header that blocks the sidebar.
function isMinimalHeaderRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return [
    "/login",
    "/admin/login",
    "/supplier/login",
    "/supplier/register",
    "/logistics-partner/login",
    "/logistics-partner/register",
    "/auth",
  ].some((prefix) => pathname.startsWith(prefix));
}

// Routes owned by a panel shell — the global header must be fully suppressed
// so the panel's own topbar/sidebar is not overlapped (which blocks the
// collapse control and shifts layout).
function isPanelRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return ["/admin", "/supplier", "/logistics-partner"].some((prefix) =>
    pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
}

// ── Language Toggle ───────────────────────────────────────────────────────

const LocaleToggle = React.memo(function LocaleToggle() {
  const { locale, setLocale, syncLocaleToServer } = useLocaleStore();
  const { isLoggedIn } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const activeLanguage = LANGUAGE_OPTIONS.find((language: any) => language.code === locale) ?? LANGUAGE_OPTIONS[0];

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const handleSelect = (nextLocale: Locale) => {
    setLocale(nextLocale);
    setOpen(false);
    if (isLoggedIn) void syncLocaleToServer();
  };

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] text-text-muted transition-colors hover:border-border-light hover:bg-surface-1/70 hover:text-text"
        aria-label="Choose language"
        title={activeLanguage.nativeName}
      >
        <span>{activeLanguage.code.toUpperCase()}</span>
        <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="glass-dropdown absolute right-0 z-[999] mt-2 min-w-44 rounded-2xl p-1"
          >
            {LANGUAGE_OPTIONS.map((language: any) => {
              const selected = language.code === locale;
              return (
                <button
                  key={language.code}
                  type="button"
                  onClick={() => handleSelect(language.code)}
                  className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs transition-colors ${
                    selected
                      ? "bg-surface-1 text-text"
                      : "text-text-muted hover:bg-surface-1/80 hover:text-text"
                  }`}
                >
                  <span>{language.name}</span>
                  <span className="text-[11px] text-text-faint">{language.nativeName}</span>
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

const CountryToggle = React.memo(function CountryToggle() {
  const { isLoggedIn } = useAuth();
  const selectedCountry = useCurrencyStore((s) => s.selectedCountry);
  const currentCurrency = useCurrencyStore((s) => s.currency.code);
  const setCountry = useCurrencyStore((s) => s.setCountry);
  const detectFromIP = useCurrencyStore((s) => s.detectFromIP);

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [countries, setCountries] = useState<PublicCountryOption[]>([]);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  useEffect(() => {
    let active = true;

    const loadCountries = async () => {
      setLoading(true);
      try {
        const response = await apiFetch("/countries", { disableCache: true });
        const payload = await response.json().catch(() => null);
        if (!response.ok || !Array.isArray(payload)) {
          if (active) setCountries([]);
          return;
        }
        if (!active) return;
        setCountries(
          payload
            .filter((entry: any) => entry && typeof entry.code === "string" && typeof entry.name === "string")
            .map((entry: any) => ({
              code: String(entry.code).toUpperCase(),
              name: String(entry.name),
              currency: typeof entry.currency === "string" ? entry.currency : undefined,
              is_active: Boolean(entry.is_active),
            }))
        );
      } catch {
        if (active) setCountries([]);
      } finally {
        if (active) setLoading(false);
      }
    };

    void loadCountries();
    return () => {
      active = false;
    };
  }, []);

  const syncCountryPreference = async (countryCode: string, currencyCode: string) => {
    if (!isLoggedIn || !countryCode) return;
    try {
      await apiFetch("/auth/me/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preferred_country: countryCode,
          preferred_currency: currencyCode,
        }),
      });
    } catch {
      // Keep selector responsive even if preference sync fails.
    }
  };

  const handleAutoDetect = async () => {
    await detectFromIP();
    const state = useCurrencyStore.getState();
    await syncCountryPreference(state.selectedCountry, state.currency.code);
    setOpen(false);
  };

  const handleSelectCountry = async (countryCode: string) => {
    await setCountry(countryCode, { lock: true });
    const state = useCurrencyStore.getState();
    await syncCountryPreference(state.selectedCountry || countryCode, state.currency.code || currentCurrency);
    setOpen(false);
  };

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold tracking-[0.18em] text-text-muted transition-colors hover:border-border-light hover:bg-surface-1/70 hover:text-text"
        aria-label="Choose country"
      >
        <span>{selectedCountry || "AUTO"}</span>
        <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="glass-dropdown absolute right-0 z-[999] mt-2 min-w-52 rounded-2xl p-1"
          >
            <button
              type="button"
              onClick={() => void handleAutoDetect()}
              className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs text-text-muted transition-colors hover:bg-surface-1/80 hover:text-text"
            >
              <span>Auto detect</span>
              <span className="text-[11px] text-text-faint">IP + browser hints</span>
            </button>

            <div className="my-1 h-px bg-border/70" />

            {loading ? (
              <p className="px-3 py-2 text-xs text-text-faint">Loading countries...</p>
            ) : countries.length === 0 ? (
              <p className="px-3 py-2 text-xs text-text-faint">No active countries available.</p>
            ) : (
              countries.map((country) => {
                const selected = country.code === selectedCountry;
                return (
                  <button
                    key={country.code}
                    type="button"
                    onClick={() => void handleSelectCountry(country.code)}
                    className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs transition-colors ${
                      selected
                        ? "bg-surface-1 text-text"
                        : "text-text-muted hover:bg-surface-1/80 hover:text-text"
                    }`}
                  >
                    <span>{country.name}</span>
                    <span className="text-[11px] text-text-faint">{country.code}</span>
                  </button>
                );
              })
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

const surfacePanelClass =
  "rounded-[22px] glass-dropdown shadow-card-xl";
const interactiveMutedClass =
  "text-text-muted hover:bg-surface-1/90 hover:text-text";
const menuItemClass =
  "text-text-muted hover:bg-surface-1/90 hover:text-text";

export default function Header() {
  const { user, isLoggedIn, logout } = useAuth();
  const router = useRouter();
  const searchParams = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
  const cartCount = useCartStore((s) => s.getItemCount());
  const wishlistCount = useWishlistStore((s) => s.ids.length);
  const pathname = usePathname();
  const tr = useLocaleStore((s) => s.t);
  const openAuthModal = useAuthModalStore((s) => s.open);

  const [menuOpen, setMenuOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const mobileImageInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    apiFetch("/search/visual", {
      method: "POST",
      body: formData,
    })
      .then((r) => r.ok ? r.json() : Promise.reject())
      .then((data) => {
        sessionStorage.setItem("zozi_visual_search", JSON.stringify({
          products: data.similarProducts || [],
          timestamp: Date.now(),
        }));
        router.push("/products?visualSearch=1");
      })
      .catch(() => {
        // Fallback: just navigate to products page
        router.push("/products");
      })
      .finally(() => {
        // Reset the input so the same file can be selected again
        e.target.value = "";
      });
  }, [router]);

  // Mobile image search handler (uses the same upload logic)
  const handleMobileImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    apiFetch("/search/visual", {
      method: "POST",
      body: formData,
    })
      .then((r) => r.ok ? r.json() : Promise.reject())
      .then((data) => {
        sessionStorage.setItem("zozi_visual_search", JSON.stringify({
          products: data.similarProducts || [],
          timestamp: Date.now(),
        }));
        setMobileSearchOpen(false);
        router.push("/products?visualSearch=1");
      })
      .catch(() => {
        setMobileSearchOpen(false);
        router.push("/products");
      })
      .finally(() => {
        e.target.value = "";
      });
  }, [router]);
  
  // ── Header search state (URL-driven for persistence) ──────────────────
  const [headerSearch, setHeaderSearch] = useState(searchParams?.get("q") || searchParams?.get("search") || "");
  const [headerCategory, setHeaderCategory] = useState(searchParams?.get("category") || "all");
  const [headerMinPrice, setHeaderMinPrice] = useState(searchParams?.get("minPrice") || "");
  const [headerMaxPrice, setHeaderMaxPrice] = useState(searchParams?.get("maxPrice") || "");
  const [headerMinRating, setHeaderMinRating] = useState(searchParams?.get("minRating") || "");
  const [headerSort, setHeaderSort] = useState(searchParams?.get("sort") || "default");
  const [headerSupplier, setHeaderSupplier] = useState(searchParams?.get("supplier") || "");
  const [supplierSuggestions, setSupplierSuggestions] = useState<SupplierPublicSummary[]>([]);
  const headerImageInputRef = useRef<HTMLInputElement>(null);
  
  // ──
  const unreadNotifs = useNotificationStore((state) => state.unreadCount);
  const currency = useCurrencyStore((s) => s.currency);
  const selectedCountry = useCurrencyStore((s) => s.selectedCountry);
  const countryLocked = useCurrencyStore((s) => s.countryLocked);

  const userRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    useCartStore.getState().initialize();
    useWishlistStore.getState().initialize();
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userRef.current && !userRef.current.contains(e.target as Node))
        setUserOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Fetch supplier suggestions for the header search bar
  useEffect(() => {
    let cancelled = false;
    apiFetch("/products/suppliers")
      .then((r) => (r.ok ? r.json() : []))
      .then((names: string[]) => {
        if (cancelled) return;
        // Convert supplier names to SupplierPublicSummary-like objects for the dropdown
        const suggestions: SupplierPublicSummary[] = names.map((name, i) => ({
          id: i + 1,
          username: name.toLowerCase().replace(/\s+/g, "_"),
          slug: name.toLowerCase().replace(/\s+/g, "-"),
          business_name: name,
          logo_url: null,
          bio: null,
          city: null,
          country: null,
          badge_level: "none",
          is_verified: false,
          verification_status: "pending",
          product_count: 0,
          total_reviews: 0,
          avg_rating: 0,
          credibility_score: 0,
          total_sales: 0,
          member_since: new Date().toISOString(),
        }));
        setSupplierSuggestions(suggestions);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  // ── Auto-navigate on filter change (debounced) ─────────────────────
  const navTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isOnProductsPage = useMemo(() => pathname === "/products", [pathname]);

  useEffect(() => {
    // Don't auto-navigate if already on the products page — it syncs its own URL params
    if (isOnProductsPage) return;
    // Don't navigate if nothing is set (still in default state)
    const hasAnyFilter = headerSearch.trim() ||
      (headerCategory && headerCategory !== "all") ||
      headerMinPrice || headerMaxPrice || headerMinRating ||
      (headerSort && headerSort !== "default") || headerSupplier;
    if (!hasAnyFilter) return;

    if (navTimerRef.current) clearTimeout(navTimerRef.current);
    navTimerRef.current = setTimeout(() => {
      const params = new URLSearchParams();
      if (headerSearch.trim()) params.set("q", headerSearch.trim());
      if (headerCategory && headerCategory !== "all") params.set("category", headerCategory);
      if (headerMinPrice) params.set("minPrice", headerMinPrice);
      if (headerMaxPrice) params.set("maxPrice", headerMaxPrice);
      if (headerMinRating) params.set("minRating", headerMinRating);
      if (headerSort && headerSort !== "default") params.set("sort", headerSort);
      if (headerSupplier) params.set("supplier", headerSupplier);
      const qs = params.toString();
      router.push(`/products${qs ? `?${qs}` : ""}`);
    }, 400);

    return () => {
      if (navTimerRef.current) clearTimeout(navTimerRef.current);
    };
  }, [
    headerSearch, headerCategory, headerMinPrice, headerMaxPrice,
    headerMinRating, headerSort, headerSupplier, isOnProductsPage, router,
  ]);

  // Hide the main nav menu on auth/login pages (sign-in, admin login, callback, etc.)
  const hideNav = isMinimalHeaderRoute(pathname);
  const currencySourceLabel = countryLocked && selectedCountry
    ? `Country ${selectedCountry}`
    : selectedCountry
    ? `Detected ${selectedCountry}`
    : "Auto detected";
  const nav: { href: string; labelKey: TranslationKey }[] = [];

  // Panel routes render their own chrome (PanelShell); suppress the global
  // storefront header so it doesn't stack over and block the sidebar.
  if (isPanelRoute(pathname)) return null;

  return (
    <>
      <header
        className={`sticky top-0 z-100 transition-all duration-300 border-b border-glass-border backdrop-blur-xl ${
          scrolled
            ? "bg-glass-hi shadow-lg shadow-black/10"
            : "bg-glass-panel shadow-sm shadow-black/5"
        }`}
        style={{ backgroundColor: "var(--color-glass-panel)", backdropFilter: "blur(14px) saturate(130%)" }}
      >
        <div className="max-w-11xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between gap-3 h-14">
            {/* Logo */}
            <Link href="/" className="flex items-center shrink-0" aria-label="Go to home">
              <Logo size="sm" />
            </Link>

            {/* Global search bar (desktop) - Enhanced with all filters */}
            {!hideNav && !isPanelRoute(pathname) && (
              <div className="hidden md:flex flex-1 max-w-5xl mx-auto">
                <HeaderSearchBar
                  search={headerSearch}
                  onSetSearch={setHeaderSearch}
                  category={headerCategory}
                  onSetCategory={setHeaderCategory}
                  minPrice={headerMinPrice}
                  maxPrice={headerMaxPrice}
                  onSetMinPrice={setHeaderMinPrice}
                  onSetMaxPrice={setHeaderMaxPrice}
                  minRating={headerMinRating}
                  onSetMinRating={setHeaderMinRating}
                  sort={headerSort}
                  onSetSort={setHeaderSort}
                  supplier={headerSupplier}
                  onSetSupplier={setHeaderSupplier}
                  onImageSearch={() => headerImageInputRef.current?.click()}
                  supplierSuggestions={supplierSuggestions}
                />
                <input
                  ref={headerImageInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleImageUpload}
                />
              </div>
            )}

            {/* Hidden file input for mobile image search */}
            <input
              ref={mobileImageInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleMobileImageUpload}
            />

            {/* Right actions */}
            <div className="flex items-center gap-1 sm:gap-2">
              {/* Theme Toggle */}
              <ThemeToggle />

              <div className="hidden md:inline-flex md:items-center md:gap-1 md:sm:gap-2">
                <div className="inline-flex flex-col items-start rounded-full border border-primary/20 bg-white/64 px-2.5 py-1 text-primary shadow-card-sm backdrop-blur-md dark:border-white/12 dark:bg-slate-950/30 dark:text-white">
                  <span className="text-[10px] font-semibold tracking-[0.18em]">{currency.code}</span>
                  <span className="text-[8px] font-medium tracking-[0.08em] text-text-faint dark:text-white/70">{currencySourceLabel}</span>
                </div>

                <CountryToggle />

                {/* Language Toggle */}
                <LocaleToggle />
              </div>

              {/* Notifications (logged-in users) */}
              {isLoggedIn && (
                <Link
                  href="/notifications"
                  prefetch={false}
                  className={`relative rounded-xl p-2 transition-colors ${interactiveMutedClass}`}
                  aria-label={unreadNotifs > 0 ? `Notifications (${unreadNotifs} unread)` : "Notifications"}
                >
                  <Bell className="w-5 h-5 text-accent" />
                  {unreadNotifs > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-accent text-[10px] font-bold text-white flex items-center justify-center">
                      {unreadNotifs > 9 ? "9+" : unreadNotifs}
                    </span>
                  )}
                </Link>
              )}

              {/* Wishlist */}
              <Link
                href="/wishlist"
                className={`relative rounded-xl p-2 transition-colors ${interactiveMutedClass}`}
                aria-label={wishlistCount > 0 ? `Wishlist (${wishlistCount} items)` : "Wishlist"}
              >
                <Heart className="w-5 h-5 text-accent" />
                {wishlistCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-accent text-[10px] font-bold text-white flex items-center justify-center">
                    {wishlistCount > 9 ? "9+" : wishlistCount}
                  </span>
                )}
              </Link>

              {/* Cart */}
              <Link
                href="/cart"
                className={`relative rounded-xl p-2 transition-colors ${interactiveMutedClass}`}
                aria-label={cartCount > 0 ? `Cart (${cartCount} items)` : "Cart"}
              >
                <ShoppingBag className="w-5 h-5 text-primary" />
                {cartCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-primary text-[10px] font-bold text-on-brand flex items-center justify-center">
                    {cartCount > 9 ? "9+" : cartCount}
                  </span>
                )}
              </Link>

              {/* User dropdown (desktop) */}
              <div className="relative hidden sm:block" ref={userRef}>
                <button
                  onClick={() => setUserOpen(!userOpen)}
                  className={`flex items-center gap-2 rounded-xl p-2 transition-colors ${interactiveMutedClass}`}
                  aria-label={isLoggedIn ? "Open account menu" : "Open sign in menu"}
                >
                  <User className="w-5 h-5 text-primary opacity-70" />
                  {user && (
                    <span className="max-w-20 truncate text-xs font-medium text-text-muted">
                      {user.username}
                    </span>
                  )}
                </button>
                <AnimatePresence>
                  {userOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      className={`absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden p-2.5 ${surfacePanelClass}`}
                    >
                      <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-white/8 via-transparent to-black/8 rounded-[22px]" />
                      <div className="relative">
                      {isLoggedIn ? (
                        <>
                          <div className="mb-1 rounded-2xl border border-border/40 bg-surface-2/60 px-3 py-2">
                            <p className="truncate text-sm font-semibold text-text">
                              {user?.username}
                            </p>
                            <p className="text-xs text-text-muted">
                              {user?.email}
                            </p>
                            <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-primary/15 text-primary">
                              {user?.role}
                            </span>
                          </div>
                          <div className="theme-divider my-1 h-px" />
                          <Link
                            href="/profile"
                            onClick={() => setUserOpen(false)}
                            className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm ${menuItemClass}`}
                          >
                            <Settings className="w-4 h-4 text-primary opacity-70" />
                            {tr("profile")}
                          </Link>
                          <Link
                            href="/orders"
                            onClick={() => setUserOpen(false)}
                            className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm ${menuItemClass}`}
                          >
                            <ClipboardList className="w-4 h-4 text-primary opacity-70" />
                            {tr("myOrders")}
                          </Link>
                          <Link
                            href="/wishlist"
                            onClick={() => setUserOpen(false)}
                            className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm ${menuItemClass}`}
                          >
                            <Heart className="w-4 h-4 text-accent" />
                            {tr("wishlist")}
                          </Link>
                          <Link
                            href="/help"
                            onClick={() => setUserOpen(false)}
                            className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm ${menuItemClass}`}
                          >
                            <ClipboardList className="w-4 h-4 text-primary opacity-70" />
                            {tr("help")}
                          </Link>
                          {user?.role === "supplier" && (
                            <Link
                              href="/supplier/dashboard"
                              onClick={() => setUserOpen(false)}
                              className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm ${menuItemClass}`}
                            >
                              <LayoutDashboard className="w-4 h-4 text-primary opacity-70" />
                            {tr("supplierDashboard")}
                            </Link>
                          )}
                          {user?.role === "admin" && (
                            <Link
                              href="/admin/dashboard"
                              onClick={() => setUserOpen(false)}
                              className={`flex items-center gap-3 rounded-xl px-2 py-1.5 text-sm ${menuItemClass}`}
                            >
                              <LayoutDashboard className="w-4 h-4 text-primary opacity-70" />
                              Admin Dashboard
                            </Link>
                          )}
                          <div className="theme-divider my-1 h-px" />
                          <Button variant="danger" className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-danger" onClick={() => {
                              setUserOpen(false);
                              logout();
                            }}
                          >
                            <LogOut className="w-4 h-4" />
                            {tr("signOut")}
                          </Button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => {
                              setUserOpen(false);
                              openAuthModal("login");
                            }}
                            className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-text hover:bg-surface-1"
                          >
                            <User className="w-4 h-4 text-primary opacity-60" />
                            {tr("signIn")}
                          </button>
                          <button
                            onClick={() => {
                              setUserOpen(false);
                              openAuthModal("register");
                            }}
                            className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium ${menuItemClass}`}
                          >
                            <Package className="w-4 h-4 text-primary opacity-60" />
                            {tr("register")}
                          </button>
                          <Link
                            href="/help"
                            onClick={() => setUserOpen(false)}
                            className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium ${menuItemClass}`}
                          >
                            <ClipboardList className="w-4 h-4 text-primary opacity-70" />
                            {tr("help")}
                          </Link>
                          <div className="theme-divider my-1 h-px" />
                          <Link
                            href="/supplier/login"
                            onClick={() => setUserOpen(false)}
                            className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-primary hover:bg-primary/10"
                          >
                            <Store className="w-4 h-4" />
                            Sell on ZOZI
                          </Link>
                        </>
                      )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Mobile search trigger — visible on small screens only */}
              {!hideNav && (
                <button
                  onClick={() => setMobileSearchOpen(true)}
                  className={`rounded-xl p-2 transition-colors md:hidden ${interactiveMutedClass}`}
                  aria-label="Open mobile search"
                >
                  <Search className="w-5 h-5" />
                </button>
              )}

              {/* Mobile menu toggle */}
              {!hideNav && (
                <button
                  onClick={() => setMenuOpen(!menuOpen)}
                  className={`rounded-xl p-2 transition-colors md:hidden ${interactiveMutedClass}`}
                  aria-label={menuOpen ? "Close menu" : "Open menu"}
                >
                  {menuOpen ? (
                    <X className="w-5 h-5" />
                  ) : (
                    <Menu className="w-5 h-5" />
                  )}
                </button>
              )}
            </div>
          </div>

          {!hideNav && nav.length > 0 && (
            <nav className="hidden sm:flex items-center -mb-px pb-2 overflow-x-auto scrollbar-none">
              <div className="flex items-center gap-1 rounded-full border border-border bg-surface-1/70 px-2 py-1 backdrop-blur">
                {nav.map((item) => {
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`relative px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.2em] rounded-full transition-all whitespace-nowrap ${
                        active
                          ? "bg-primary text-on-brand shadow-sm shadow-black/20"
                          : "text-text-faint hover:text-text"
                      }`}
                    >
                      {tr(item.labelKey)}
                    </Link>
                  );
                })}
              </div>
            </nav>
          )}
        </div>
      </header>

      <AnimatePresence>
        {menuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMenuOpen(false)}
              className="fixed inset-0 theme-overlay z-[150]"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed bottom-0 right-0 top-0 z-[151] flex w-72 max-w-[85vw] flex-col border-l border-border bg-surface-base"
            >
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <span className="text-base font-bold text-text">Menu</span>
                <button
                  onClick={() => setMenuOpen(false)}
                  className={`rounded-xl p-2 ${interactiveMutedClass}`}
                  aria-label="Close menu"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>


              {user && (
                <div className="theme-panel mx-4 mb-2 rounded-xl border p-2">
                  <p className="truncate text-sm font-semibold text-text">
                    {user.username}
                  </p>
                  <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-primary/15 text-primary">
                    {user.role}
                  </span>
                </div>
              )}

              <nav className="flex-1 overflow-y-auto px-4 py-1.5 space-y-1">
                {nav.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMenuOpen(false)}
                    className={`block px-2 py-2 rounded-xl text-sm font-medium transition-colors ${
                      pathname === item.href
                        ? "bg-primary/10 text-primary"
                        : menuItemClass
                    }`}
                  >
                    {tr(item.labelKey)}
                  </Link>
                ))}

              </nav>

              <div className="space-y-2 border-t border-border px-5 py-4">
                {isLoggedIn ? (
                  <Button variant="danger" className="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-danger" onClick={() => {
                      setMenuOpen(false);
                      logout();
                    }}
                  >
                    <LogOut className="w-4 h-4" />
                    {tr("signOut")}
                  </Button>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        openAuthModal("login");
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-text hover:bg-surface-1"
                    >
                      <User className="w-4 h-4 text-primary opacity-60" />
                      {tr("signIn")}
                    </button>
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        openAuthModal("register");
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-text hover:bg-surface-1"
                    >
                      <Package className="w-4 h-4 text-primary opacity-60" />
                      {tr("register")}
                    </button>
                    <Link
                      href="/help"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-text hover:bg-surface-1"
                    >
                      <ClipboardList className="w-4 h-4 text-primary opacity-70" />
                      {tr("help")}
                    </Link>
                    <Link
                      href="/supplier/login"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-primary hover:bg-primary/10"
                    >
                      <Store className="w-4 h-4" />
                      Become a Supplier
                    </Link>
                  </>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Mobile Search Overlay */}
      <MobileSearchOverlay
        open={mobileSearchOpen}
        onClose={() => setMobileSearchOpen(false)}
        search={headerSearch}
        onSetSearch={setHeaderSearch}
        category={headerCategory}
        onSetCategory={setHeaderCategory}
        minPrice={headerMinPrice}
        maxPrice={headerMaxPrice}
        onSetMinPrice={setHeaderMinPrice}
        onSetMaxPrice={setHeaderMaxPrice}
        minRating={headerMinRating}
        onSetMinRating={setHeaderMinRating}
        sort={headerSort}
        onSetSort={setHeaderSort}
        supplier={headerSupplier}
        onSetSupplier={setHeaderSupplier}
        onImageSearch={() => mobileImageInputRef.current?.click()}
      />
    </>
  );
}
