import React, { useCallback, useEffect, useRef, useState } from "react";
import { View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity, Linking, AppState } from "react-native";
import { setStringAsync } from "@/lib/clipboard";
import { AppTheme, makeStyles } from "@/theme";
import { useRouter } from "expo-router";
import { getPublicCoupons, type Coupon, apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useTranslateText, useTranslateTexts } from "@/lib/useTranslate";
import AppHeader from "@/components/ui/AppHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/LoadingSkeleton";
import { Product } from "@shared/types";
import { ProductCard } from "../components/ProductCard";
import { formatLocalizedDateTime, isRtlLocale } from "@shared/localization";

let LinearGradient: React.ComponentType<{
  colors: string[];
  start?: { x: number; y: number };
  end?: { x: number; y: number };
  style?: object;
  children?: React.ReactNode;
}> | null = null;
try { LinearGradient = require("expo-linear-gradient").LinearGradient; } catch { /* fallback to flat card */ }

interface FlashSale {
  id: number;
  title: string;
  discount_pct: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
}

interface PromotionalBanner {
  id: number | string;
  title: string;
  subtitle: string;
  badge_text?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  cta_url?: string | null;
  is_active?: boolean;
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    borderRadius: theme.radius.xl,
    borderWidth: 1.5,
    padding: theme.spacing.md,
    gap: 12,
  },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: theme.spacing.xs,
    borderRadius: 20,
  },
  badgeText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: theme.fontSize.sm,
  },
  codeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  meta: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.sm,
  },
  copyBtn: {
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: "center",
  },
  section: {
    gap: theme.spacing.md,
  },
  sectionTitle: {
    fontSize: theme.fontSize.sm,
    fontWeight: "800",
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  offerCard: {
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  offerMetaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: theme.spacing.sm,
  },
  offerPill: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
  },
  offerPillText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: theme.fontSize.xs,
  },
  ctaBtn: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: "center",
  },
  screenHeader: {
    margin: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  headerEyebrow: {
    fontSize: theme.fontSize.xs,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  headerTitle: {
    fontSize: theme.fontSize.xl,
    fontWeight: "800",
  },
  headerSummaryRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.sm,
  },
  summaryChip: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
    minWidth: 96,
  },
  summaryValue: {
    fontSize: theme.fontSize.md,
    fontWeight: "800",
  },
  summaryLabel: {
    fontSize: theme.fontSize.xs,
    marginTop: 2,
  },
  tabRail: {
    flexDirection: "row",
    marginHorizontal: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    borderRadius: 14,
    overflow: "hidden",
    borderWidth: 1,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 12,
    gap: 3,
  },
  tabCount: {
    fontSize: theme.fontSize.xs,
    opacity: 0.75,
  },
  codeBlock: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  hintText: {
    fontSize: theme.fontSize.xs,
    lineHeight: 16,
  },
  loadingContainer: {
    padding: theme.spacing.md,
    gap: theme.spacing.md,
  },
});

const SALE_GRADIENTS: [string, string][] = [
  ["#7c3aed", "#4f46e5"],
  ["#f43f5e", "#ec4899"],
  ["#f59e0b", "#f97316"],
  ["#10b981", "#14b8a6"],
];

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function getCountdown(endsAt: string | null, nowMs: number): string | null {
  if (!endsAt) return null;
  const diff = new Date(endsAt).getTime() - nowMs;
  if (diff <= 0) return null;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

function SaleCard({ sale, idx, nowMs, openLabel, durationLabel, onPress }: {
  sale: FlashSale;
  idx: number;
  nowMs: number;
  openLabel: string;
  durationLabel: string;
  onPress: () => void;
}) {
  const { theme } = useThemeStore();
  const locale = useLocaleStore((state) => state.locale);
  const styles = createStyles(theme);
  const isRtl = isRtlLocale(locale);
  const remaining = getCountdown(sale.ends_at, nowMs);

  const [start, end] = SALE_GRADIENTS[idx % SALE_GRADIENTS.length];
  const cardStyle = { borderRadius: theme.radius.xl, padding: theme.spacing.md, gap: theme.spacing.sm };
  const content = (
    <>
      {/* Header row */}
      <View style={[styles.offerMetaRow, { flexDirection: isRtl ? "row-reverse" : "row" }]}>
        <View style={[styles.offerPill, { backgroundColor: "rgba(255,255,255,0.25)" }]}>
          <Text style={styles.offerPillText}>{Math.round(sale.discount_pct)}% OFF</Text>
        </View>
        {remaining && (
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4, backgroundColor: "rgba(0,0,0,0.25)", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 }}>
            <Text style={{ color: "#fff", fontSize: theme.fontSize.xs, fontWeight: "800", fontVariant: ["tabular-nums"] }}>⏱ {remaining}</Text>
          </View>
        )}
      </View>
      {/* Title */}
      <Text style={{ color: "#fff", fontWeight: "800", fontSize: theme.fontSize.lg }}>{sale.title}</Text>
      {/* Duration label */}
      <Text style={{ color: "rgba(255,255,255,0.8)", fontSize: theme.fontSize.sm }}>
        {remaining ? `Ends in ${remaining}` : formatWindow(locale, "Starts", "Until", sale.starts_at, sale.ends_at) ?? durationLabel}
      </Text>
      {/* CTA */}
      <TouchableOpacity
        style={{ backgroundColor: "rgba(255,255,255,0.2)", borderRadius: 10, paddingVertical: 10, alignItems: "center", borderWidth: 1, borderColor: "rgba(255,255,255,0.35)" }}
        onPress={onPress}
        activeOpacity={0.8}
      >
        <Text style={{ color: "#fff", fontWeight: "800", fontSize: theme.fontSize.sm }}>{openLabel}</Text>
      </TouchableOpacity>
    </>
  );

  if (LinearGradient) {
    return (
      <LinearGradient colors={[start, end]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={cardStyle}>
        {content}
      </LinearGradient>
    );
  }
  return (
    <View style={[cardStyle, { backgroundColor: start }]}>{content}</View>
  );
}

function formatWindow(locale: string, startsLabel: string, untilLabel: string, startsAt?: string | null, endsAt?: string | null) {
  if (!startsAt && !endsAt) return null;
  const startLabel = startsAt ? formatLocalizedDateTime(startsAt, locale, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : null;
  const endLabel = endsAt ? formatLocalizedDateTime(endsAt, locale, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : null;
  if (startLabel && endLabel) return `${startLabel} → ${endLabel}`;
  return endLabel ? `${untilLabel} ${endLabel}` : startLabel ? `${startsLabel} ${startLabel}` : null;
}

function CouponCard({ item }: { item: Coupon }) {
  const { theme } = useThemeStore();
  const locale = useLocaleStore((state) => state.locale);
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const formatPrice = useCurrencyStore((state) => state.format);
  const [copied, setCopied] = useState(false);
  const [offLabel, copiedTitle, minOrderLabel, usesLeftLabel, expiredLabel, expiresLabel, tapToCopyLabel] = useTranslateTexts([
    "OFF",
    "Copied!",
    "Min. order",
    "uses left",
    "Expired",
    "Expires",
    "Tap to copy code",
  ]);

  const discountLabel =
    item.discount_type === "percentage"
      ? `${item.discount_value}% ${offLabel}`
      : `${formatPrice(item.discount_value)} ${offLabel}`;

  const expired = item.expires_at && new Date(item.expires_at) < new Date();
  const available = item.max_uses > 0 ? item.max_uses - item.current_uses : null;

  function handleCopy() {
    void setStringAsync(item.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.colors.surface1,
          borderColor: expired ? theme.colors.border : theme.colors.brand + "66",
          opacity: expired ? 0.65 : 1,
        },
      ]}
    >
      {/* Discount badge row */}
      <View style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
        <View style={[styles.badge, { backgroundColor: expired ? theme.colors.textMuted : theme.colors.brand }]}>
          <Text style={styles.badgeText}>{discountLabel}</Text>
        </View>
        {expired && (
          <View style={[styles.badge, { backgroundColor: theme.colors.danger }]}>
            <Text style={styles.badgeText}>{expiredLabel.toUpperCase()}</Text>
          </View>
        )}
      </View>

      {/* Code */}
      <TouchableOpacity onPress={handleCopy} style={styles.codeRow} disabled={!!expired} activeOpacity={0.85}>
        <View style={[styles.codeBlock, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
          <Text style={[s.text, { fontFamily: "monospace", fontSize: theme.fontSize.md, fontWeight: "700", letterSpacing: 2 }]}>
            {item.code}
          </Text>
          <Text style={[styles.hintText, { color: theme.colors.textMuted }]}>{tapToCopyLabel}</Text>
        </View>
        <Text style={{ fontSize: theme.fontSize.md }}>📋</Text>
      </TouchableOpacity>

      {/* Meta */}
      <View style={styles.meta}>
        {item.min_order_amount > 0 && (
          <Text style={s.textMuted}>
            {minOrderLabel}: {formatPrice(item.min_order_amount)}
          </Text>
        )}
        {available !== null && (
          <Text style={s.textMuted}>{available} {usesLeftLabel}</Text>
        )}
        {item.expires_at && (
          <Text style={[s.textMuted, expired && { color: theme.colors.danger }]}>
            {expired ? expiredLabel : `${expiresLabel} ${formatLocalizedDateTime(item.expires_at, locale, { year: "numeric", month: "short", day: "numeric" })}`}
          </Text>
        )}
      </View>

      {!expired && (
        <TouchableOpacity onPress={handleCopy} activeOpacity={0.8}>
          <View style={[styles.copyBtn, { backgroundColor: theme.colors.brand + "22", borderColor: theme.colors.brand }]}>
            <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
              {copied ? copiedTitle : tapToCopyLabel}
            </Text>
          </View>
        </TouchableOpacity>
      )}
    </View>
  );
}

export default function OffersScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [offersTitle, dealsTabLabel, couponsTabLabel, retryLabel, noOffersTitle, noOffersSubtitle, flashSalesLabel, promotionalOffersLabel, supplierDiscountsLabel, openFlashSaleLabel, openOfferLabel, durationAdminLabel, durationBannerLabel, durationSupplierLabel, noCouponsTitle, noCouponsSubtitle, startsLabel, untilLabel, errorDealsLabel, errorCouponsLabel] = useTranslateTexts([
    "Offers & Coupons",
    "Deals",
    "Coupons",
    "Retry",
    "No live offers right now",
    "Check back soon for flash sales, promotional campaigns, and supplier discounts.",
    "Flash Sales",
    "Promotional Offers",
    "Supplier Discounts",
    "Open Flash Sale",
    "Open Offer",
    "Duration managed by admin.",
    "Duration managed by admin banner campaign.",
    "Supplier-controlled duration is active while this offer runs.",
    "No coupons right now",
    "Check back soon for exclusive codes!",
    "Starts",
    "Until",
    "Error loading deals",
    "Error loading coupons",
  ]);
  const failedToLoadOffersLabel = useTranslateText("Failed to load offers");

  const [tab, setTab] = useState<'deals' | 'coupons'>('deals');
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [flashSales, setFlashSales] = useState<FlashSale[]>([]);
  const [promotions, setPromotions] = useState<PromotionalBanner[]>([]);
  const [supplierDeals, setSupplierDeals] = useState<Product[]>([]);
  const [nowMs, setNowMs] = useState<number>(() => Date.now());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (selectedTab: 'deals' | 'coupons', silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      if (selectedTab === 'coupons') {
        setCoupons(await getPublicCoupons());
      } else {
        const [salesData, bannerData, supplierData] = await Promise.all([
          apiFetch<FlashSale[] | { items?: FlashSale[] }>("/flash-sales", { skipAuth: true } as never),
          apiFetch<PromotionalBanner[] | { banners?: PromotionalBanner[] }>("/banners?type=promotional", { skipAuth: true } as never),
          apiFetch<Product[] | { items?: Product[] }>("/products?sort=discount&min_discount=5&limit=12", { skipAuth: true } as never),
        ]);

        const parsedBanners = Array.isArray(bannerData)
          ? bannerData
          : Array.isArray((bannerData as { banners?: PromotionalBanner[] })?.banners)
            ? (bannerData as { banners: PromotionalBanner[] }).banners
            : [];

        setFlashSales(normalizeCollectionResponse<FlashSale>(salesData).filter((sale) => sale.is_active));
        setPromotions(parsedBanners.filter((item) => item?.is_active !== false));
        setSupplierDeals(normalizeCollectionResponse<Product>(supplierData, ["products"]));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : failedToLoadOffersLabel);
    } finally {
      if (!silent) setLoading(false);
      setRefreshing(false);
    }
  }, [failedToLoadOffersLabel]);

  useEffect(() => { void load(tab); }, [tab, load]);

  useEffect(() => {
    if (tab !== "deals" || flashSales.length === 0) {
      return;
    }

    let appIsActive = AppState.currentState === "active";
    const tick = () => {
      if (!appIsActive) return;
      setNowMs(Date.now());
    };

    const subscription = AppState.addEventListener("change", (nextState) => {
      appIsActive = nextState === "active";
      if (appIsActive) {
        setNowMs(Date.now());
      }
    });

    tick();
    const timer = setInterval(tick, 1000);

    return () => {
      clearInterval(timer);
      subscription.remove();
    };
  }, [tab, flashSales.length]);

  const onTabChange = (newTab: 'deals' | 'coupons') => {
    setTab(newTab);
    setError(null);
    setRefreshing(false);
  };

  async function handleOpenCta(url?: string | null) {
    if (!url) {
      router.push("/products?deals=1" as never);
      return;
    }
    if (url.startsWith("http://") || url.startsWith("https://")) {
      await Linking.openURL(url);
      return;
    }
    router.push(url as never);
  }

  const hasDeals = flashSales.length > 0 || promotions.length > 0 || supplierDeals.length > 0;
  const dealsCount = flashSales.length + promotions.length + supplierDeals.length;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <AppHeader showSearch={false} />

      <View style={[s.section, { paddingTop: theme.spacing.md }]}>
        <Text style={[s.textMuted, { lineHeight: 20 }]}>Browse live deals, supplier discounts, and coupon codes from one place with clearer tab context and faster copy actions.</Text>
        <View style={[styles.headerSummaryRow, { marginTop: theme.spacing.md }]}>
          <View style={[styles.summaryChip, { backgroundColor: theme.colors.brand + "16", borderColor: theme.colors.brand + "33" }]}>
            <Text style={[styles.summaryValue, { color: theme.colors.text }]}>{dealsCount}</Text>
            <Text style={[styles.summaryLabel, { color: theme.colors.textMuted }]}>Live deals</Text>
          </View>
          <View style={[styles.summaryChip, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <Text style={[styles.summaryValue, { color: theme.colors.text }]}>{coupons.length}</Text>
            <Text style={[styles.summaryLabel, { color: theme.colors.textMuted }]}>Coupons</Text>
          </View>
        </View>
      </View>

      {/* Toggle Tabs */}
      <View style={[styles.tabRail, { flexDirection: isRtl ? 'row-reverse' : 'row', borderColor: theme.colors.border }]}>
        <TouchableOpacity
          style={[styles.tabBtn, { backgroundColor: tab === 'deals' ? theme.colors.brand : theme.colors.surface1 }]}
          onPress={() => onTabChange('deals')}
        >
          <Text style={{ color: tab === 'deals' ? '#fff' : theme.colors.text, textAlign: 'center', fontWeight: '700' }}>{dealsTabLabel}</Text>
          <Text style={[styles.tabCount, { color: tab === 'deals' ? '#fff' : theme.colors.textMuted, textAlign: 'center' }]}>{dealsCount} items</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabBtn, { backgroundColor: tab === 'coupons' ? theme.colors.brand : theme.colors.surface1 }]}
          onPress={() => onTabChange('coupons')}
        >
          <Text style={{ color: tab === 'coupons' ? '#fff' : theme.colors.text, textAlign: 'center', fontWeight: '700' }}>{couponsTabLabel}</Text>
          <Text style={[styles.tabCount, { color: tab === 'coupons' ? '#fff' : theme.colors.textMuted, textAlign: 'center' }]}>{coupons.length} codes</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          {[1, 2, 3].map((index) => (
            <Skeleton key={index} height={tab === 'deals' ? 176 : 148} style={{ borderRadius: theme.radius.xl }} />
          ))}
        </View>
      ) : error ? (
        <EmptyState
          title={tab === 'deals' ? errorDealsLabel : errorCouponsLabel}
          subtitle={error}
          action={{ label: retryLabel, onPress: () => { void load(tab); } }}
        />
      ) : tab === 'deals' ? (
        !hasDeals ? (
          <EmptyState
            title={noOffersTitle}
            subtitle={noOffersSubtitle}
            icon={<Text style={{ fontSize: theme.fontSize["3xl"] }}>🔥</Text>}
          />
        ) : (
          <FlatList
            data={[{ key: "offers" }]}
            keyExtractor={(item) => item.key}
            contentContainerStyle={{ padding: theme.spacing.md, gap: 14 }}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => { setRefreshing(true); void load(tab, true); }}
                colors={[theme.colors.brand]}
              />
            }
            renderItem={() => (
              <View style={styles.section}>
                {flashSales.length > 0 && (
                  <View style={styles.section}>
                    <Text style={[styles.sectionTitle, { color: theme.colors.textMuted, textAlign: isRtl ? "right" : "left" }]}>{flashSalesLabel}</Text>
                    {flashSales.map((sale, idx) => (
                      <SaleCard
                        key={sale.id}
                        sale={sale}
                        idx={idx}
                        nowMs={nowMs}
                        openLabel={openFlashSaleLabel}
                        durationLabel={durationAdminLabel}
                        onPress={() => router.push("/flash-sales" as never)}
                      />
                    ))}
                  </View>
                )}

                {promotions.length > 0 && (
                  <View style={styles.section}>
                    <Text style={[styles.sectionTitle, { color: theme.colors.textMuted, textAlign: isRtl ? "right" : "left" }]}>{promotionalOffersLabel}</Text>
                    {promotions.map((promotion) => (
                      <View
                        key={String(promotion.id)}
                        style={[
                          styles.offerCard,
                          { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
                        ]}
                      >
                        <View style={styles.offerMetaRow}>
                          <View style={[styles.offerPill, { backgroundColor: "#6d28d9" }]}>
                            <Text style={styles.offerPillText}>{promotion.badge_text ?? "Promotion"}</Text>
                          </View>
                        </View>
                        <Text style={[s.text, { fontWeight: "800", fontSize: theme.fontSize.lg }]}>{promotion.title}</Text>
                        <Text style={s.textMuted}>{promotion.subtitle}</Text>
                        <Text style={[s.textMuted, { textAlign: isRtl ? "right" : "left" }]}>{formatWindow(locale, startsLabel, untilLabel, promotion.starts_at, promotion.ends_at) ?? durationBannerLabel}</Text>
                        <TouchableOpacity
                          style={[styles.ctaBtn, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}
                          onPress={() => handleOpenCta(promotion.cta_url)}
                        >
                          <Text style={{ color: theme.colors.text, fontWeight: "800" }}>{openOfferLabel}</Text>
                        </TouchableOpacity>
                      </View>
                    ))}
                  </View>
                )}

                {supplierDeals.length > 0 && (
                  <View style={styles.section}>
                    <Text style={[styles.sectionTitle, { color: theme.colors.textMuted, textAlign: isRtl ? "right" : "left" }]}>{supplierDiscountsLabel}</Text>
                    {supplierDeals.map((item) => (
                      <View key={item.id} style={styles.section}>
                        <ProductCard product={item} />
                        <Text style={[s.textMuted, { paddingHorizontal: theme.spacing.xs, textAlign: isRtl ? "right" : "left" }]}> 
                          {formatWindow(locale, startsLabel, untilLabel, item.offer_starts_at ?? item.discount_starts_at, item.offer_ends_at ?? item.discount_ends_at) ?? durationSupplierLabel}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            )}
          />
        )
      ) : (
        coupons.length === 0 ? (
          <EmptyState
            title={noCouponsTitle}
            subtitle={noCouponsSubtitle}
            icon={<Text style={{ fontSize: theme.fontSize["3xl"] }}>🏷️</Text>}
          />
        ) : (
          <FlatList
            data={coupons}
            keyExtractor={(item) => String(item.id)}
            contentContainerStyle={{ padding: theme.spacing.md, gap: 14 }}
            showsVerticalScrollIndicator={false}
            initialNumToRender={6}
            maxToRenderPerBatch={8}
            windowSize={7}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => { setRefreshing(true); void load(tab, true); }}
                colors={[theme.colors.brand]}
              />
            }
            renderItem={({ item }) => <CouponCard item={item} />}
          />
        )
      )}
    </View>
  );
}
