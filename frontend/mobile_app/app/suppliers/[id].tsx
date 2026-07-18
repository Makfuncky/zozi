/**
 * Customer-facing public supplier profile screen.
 * Route: /suppliers/[id]  (public — no auth required)
 *
 * Displays: banner, logo, about us, stats, products, certifications,
 * social links, video, and chat CTA.
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  ScrollView,
  Image,
  FlatList,
  Linking,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { apiFetch, resolveApiAssetUrl } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles, AppTheme } from "@/theme";
import { SupplierPublicProfile, SupplierCertification, Product } from "@shared/types";
import ScreenHeader from "@/components/ui/ScreenHeader";

// ─── helpers ────────────────────────────────────────────────────────────────

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function badgeColor(level: string, theme: AppTheme): string {
  switch ((level || "").toLowerCase()) {
    case "gold":     return "#F59E0B";
    case "silver":   return "#9CA3AF";
    case "bronze":   return "#92400E";
    case "verified": return theme.colors.brand;
    default:         return theme.colors.textMuted;
  }
}

function Stars({ rating, reviews, theme }: { rating: number; reviews: number; theme: AppTheme }) {
  const stars = [];
  const full = Math.floor(rating);
  for (let i = 0; i < 5; i++) {
    stars.push(
      <Text key={i} style={{ color: i < full ? "#F59E0B" : theme.colors.border, fontSize: theme.fontSize.sm }}>
        ★
      </Text>
    );
  }
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 2 }}>
      {stars}
      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginLeft: 4 }}>
        ({reviews})
      </Text>
    </View>
  );
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
    .map((value) => value.trim())
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

  const [intro, ...rest] = paragraphs;
  return {
    intro: intro ?? null,
    paragraphs: rest,
    bulletPoints,
  };
}

// ─── styles ─────────────────────────────────────────────────────────────────

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    centered: { flex: 1, alignItems: "center", justifyContent: "center" },
    banner: { width: "100%", height: 160, backgroundColor: theme.colors.surface2 },
    avatarWrap: {
      position: "absolute",
      bottom: -36,
      left: theme.spacing.lg,
      width: 72,
      height: 72,
      borderRadius: 36,
      borderWidth: 3,
      borderColor: theme.colors.surface0,
      backgroundColor: theme.colors.surface1,
      overflow: "hidden",
    },
    avatarText: {
      color: theme.colors.brand,
      fontWeight: theme.fontWeight.bold,
      fontSize: theme.fontSize["2xl"],
    },
    badgePill: {
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: 2,
      borderRadius: theme.radius.full,
      alignSelf: "flex-start",
      marginTop: theme.spacing.xs,
    },
    section: {
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.lg,
    },
    sectionTitle: {
      color: theme.colors.text,
      fontWeight: theme.fontWeight.semibold,
      fontSize: theme.fontSize.base,
      marginBottom: theme.spacing.sm,
    },
    card: {
      backgroundColor: theme.colors.surface1,
      borderRadius: theme.radius.lg,
      padding: theme.spacing.md,
    },
    statsRow: {
      flexDirection: "row",
      justifyContent: "space-around",
      backgroundColor: theme.colors.surface1,
      borderRadius: theme.radius.lg,
      padding: theme.spacing.md,
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.sm,
    },
    statLabel: {
      color: theme.colors.textMuted,
      fontSize: theme.fontSize.xs,
      marginTop: 2,
    },
    statValue: {
      color: theme.colors.text,
      fontWeight: theme.fontWeight.bold,
      fontSize: theme.fontSize.base,
    },
    productItem: {
      flex: 1,
      margin: theme.spacing.xs,
      backgroundColor: theme.colors.surface1,
      borderRadius: theme.radius.md,
      overflow: "hidden",
    },
    productImage: { width: "100%", height: 110, backgroundColor: theme.colors.surface2 },
    productName: {
      color: theme.colors.text,
      fontSize: theme.fontSize.xs,
      fontWeight: theme.fontWeight.semibold,
      padding: theme.spacing.xs,
    },
    productPrice: {
      color: theme.colors.brand,
      fontSize: theme.fontSize.sm,
      fontWeight: theme.fontWeight.bold,
      paddingHorizontal: theme.spacing.xs,
      paddingBottom: theme.spacing.xs,
    },
    certRow: {
      flexDirection: "row",
      gap: theme.spacing.sm,
      flexWrap: "wrap",
    },
    certCard: {
      backgroundColor: theme.colors.surface2,
      borderRadius: theme.radius.md,
      padding: theme.spacing.sm,
      minWidth: 120,
      flex: 1,
    },
    reviewCard: {
      backgroundColor: theme.colors.surface1,
      borderRadius: theme.radius.lg,
      padding: theme.spacing.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
      marginBottom: theme.spacing.sm,
    },
    socialRow: {
      flexDirection: "row",
      gap: theme.spacing.md,
      flexWrap: "wrap",
    },
    socialBtn: {
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.md,
      borderRadius: theme.radius.full,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    chatBtn: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: theme.spacing.sm,
      backgroundColor: theme.colors.brand,
      borderRadius: theme.radius.xl,
      paddingVertical: theme.spacing.md,
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.lg,
      marginBottom: theme.spacing.xl,
    },
    paginationRow: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginTop: theme.spacing.md,
    },
    pageBtn: {
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.lg,
      borderRadius: theme.radius.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
  });

// ─── main screen ─────────────────────────────────────────────────────────────

const PAGE_SIZE = 8;

export default function SupplierPublicScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const routeParam = Array.isArray(id) ? id[0] : id;
  const router = useRouter();
  const { theme } = useThemeStore();
  const formatPrice = useCurrencyStore((state) => state.format);
  const s = makeStyles(theme);
  const styles = createStyles(theme);

  const [resolvedSupplierId, setResolvedSupplierId] = useState<string | null>(null);
  const [resolvingSupplierId, setResolvingSupplierId] = useState(true);
  const [profile, setProfile] = useState<SupplierPublicProfile | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [page, setPage] = useState(0);
  const [totalProducts, setTotalProducts] = useState(0);

  useEffect(() => {
    let mounted = true;

    if (!routeParam) {
      setResolvedSupplierId(null);
      setResolvingSupplierId(false);
      return () => { mounted = false; };
    }

    if (/^\d+$/.test(routeParam)) {
      setResolvedSupplierId(routeParam);
      setResolvingSupplierId(false);
      return () => { mounted = false; };
    }

    setResolvingSupplierId(true);
    apiFetch<{ id?: number }>(`/suppliers/resolve/${encodeURIComponent(routeParam)}`, { skipAuth: true })
      .then((data) => {
        if (mounted) setResolvedSupplierId(data?.id ? String(data.id) : null);
      })
      .catch(() => {
        if (mounted) setResolvedSupplierId(null);
      })
      .finally(() => {
        if (mounted) setResolvingSupplierId(false);
      });

    return () => { mounted = false; };
  }, [routeParam]);

  // ── load profile ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!resolvedSupplierId) {
      setProfile(null);
      if (!resolvingSupplierId) setLoadingProfile(false);
      return;
    }

    let mounted = true;
    (async () => {
      try {
        const res = await apiFetch<SupplierPublicProfile>(`/suppliers/${resolvedSupplierId}`, { skipAuth: true });
        if (mounted) setProfile(res);
      } catch {
        // leave null; UI shows not-found
      } finally {
        if (mounted) setLoadingProfile(false);
      }
    })();
    return () => { mounted = false; };
  }, [resolvedSupplierId, resolvingSupplierId]);

  useEffect(() => {
    if (!profile?.slug || !routeParam) return;
    if (routeParam === profile.slug) return;
    router.replace(`/suppliers/${profile.slug}` as never);
  }, [profile, routeParam, router]);

  // ── load products ───────────────────────────────────────────────────────
  const loadProducts = useCallback(async (pageIndex: number) => {
    if (!resolvedSupplierId) return;
    setLoadingProducts(true);
    try {
      const res = await apiFetch<{ total: number; items: Product[] }>(
        `/suppliers/${resolvedSupplierId}/products?limit=${PAGE_SIZE}&offset=${pageIndex * PAGE_SIZE}`,
        { skipAuth: true }
      );
      setProducts(res.items ?? []);
      setTotalProducts(res.total ?? 0);
    } catch {
      setProducts([]);
    } finally {
      setLoadingProducts(false);
    }
  }, [resolvedSupplierId]);

  useEffect(() => {
    if (!resolvedSupplierId) {
      setProducts([]);
      setTotalProducts(0);
      setLoadingProducts(false);
      return;
    }
    loadProducts(page);
  }, [resolvedSupplierId, page, loadProducts]);

  // ── derived ─────────────────────────────────────────────────────────────
  const totalPages = Math.ceil(totalProducts / PAGE_SIZE);
  const displayName = profile?.business_name || profile?.username || "Supplier";
  const initials = displayName.slice(0, 2).toUpperCase();
  const location = [profile?.city, profile?.region, profile?.country].filter(Boolean).join(", ");
  const memberYear = profile?.member_since ? new Date(profile.member_since).getFullYear() : "—";
  const bColor = profile ? badgeColor(profile.badge_level, theme) : theme.colors.brand;
  const narrative = formatSupplierNarrative(profile?.about_us || profile?.bio);

  // ── loading state ────────────────────────────────────────────────────────
  if (loadingProfile || resolvingSupplierId) {
    return (
      <View style={[s.container, styles.centered]}>
        <ScreenHeader title="Supplier" />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={[s.container, styles.centered]}>
        <ScreenHeader title="Not Found" />
        <Text style={s.text}>Supplier not found.</Text>
        <TouchableOpacity style={[s.btnSecondary, { marginTop: theme.spacing.md }]} onPress={() => router.back()}>
          <Text style={s.btnSecondaryText}>Go back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ── social links helper ──────────────────────────────────────────────────
  const socialEntries = Object.entries(profile.social_links || {}).filter(([, v]) => Boolean(v)) as [string, string][];

  // ── certifications ───────────────────────────────────────────────────────
  const certs: SupplierCertification[] = Array.isArray(profile.certifications)
    ? profile.certifications
    : [];
  const recentReviews = Array.isArray(profile.recent_reviews) ? profile.recent_reviews : [];

  return (
    <View style={s.container}>
      <ScreenHeader title={displayName} />

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* ── Hero Banner ── */}
        <View style={{ position: "relative" }}>
          {resolveApiAssetUrl(profile.banner_url) ? (
            <Image source={{ uri: resolveApiAssetUrl(profile.banner_url)! }} style={styles.banner} resizeMode="cover" />
          ) : (
            <View style={[styles.banner, { backgroundColor: bColor + "33" }]} />
          )}

          {/* Logo */}
          <View style={styles.avatarWrap}>
            {resolveApiAssetUrl(profile.logo_url) ? (
              <Image source={{ uri: resolveApiAssetUrl(profile.logo_url)! }} style={{ width: "100%", height: "100%" }} resizeMode="cover" />
            ) : (
              <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
                <Text style={styles.avatarText}>{initials}</Text>
              </View>
            )}
          </View>
        </View>

        {/* ── Header info ── */}
        <View style={{ marginTop: 44, marginHorizontal: theme.spacing.md }}>
          <Text style={[s.title, { fontSize: theme.fontSize.xl }]}>{displayName}</Text>

          {/* Badge */}
          {profile.badge_level && profile.badge_level !== "none" && (
            <View style={[styles.badgePill, { backgroundColor: bColor + "22" }]}>
              <Text style={{ color: bColor, fontWeight: theme.fontWeight.semibold, fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                {profile.badge_level} {profile.is_verified ? "✓" : ""}
              </Text>
            </View>
          )}

          {location ? (
            <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginTop: theme.spacing.xs }}>
              <Ionicons name="location-outline" size={14} color={theme.colors.textMuted} />
              <Text style={[s.textMuted]}>{location}</Text>
            </View>
          ) : null}

          {profile.website ? (
            <TouchableOpacity onPress={() => Linking.openURL(profile.website!)} style={{ flexDirection: "row", alignItems: "center", gap: 4, marginTop: theme.spacing.xs }}>
              <Ionicons name="globe-outline" size={14} color={theme.colors.brand} />
              <Text style={[s.textBrand]}>{profile.website}</Text>
            </TouchableOpacity>
          ) : null}

          <Stars rating={profile.avg_rating} reviews={profile.total_reviews} theme={theme} />
        </View>

        {/* ── Stats row ── */}
        <View style={[styles.statsRow, { marginTop: theme.spacing.lg }]}>
          <View style={{ alignItems: "center" }}>
            <Text style={styles.statValue}>{profile.product_count}</Text>
            <Text style={styles.statLabel}>Products</Text>
          </View>
          <View style={{ alignItems: "center" }}>
            <Text style={styles.statValue}>{formatNumber(profile.total_sales)}</Text>
            <Text style={styles.statLabel}>Sales</Text>
          </View>
          <View style={{ alignItems: "center" }}>
            <Text style={styles.statValue}>{profile.avg_rating.toFixed(1)}</Text>
            <Text style={styles.statLabel}>Rating</Text>
          </View>
          <View style={{ alignItems: "center" }}>
            <Text style={styles.statValue}>{memberYear}</Text>
            <Text style={styles.statLabel}>Since</Text>
          </View>
        </View>

        {/* ── About Us ── */}
        {(profile.about_us || profile.bio) ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About Us</Text>
            <View style={styles.card}>
              {narrative.intro ? (
                <Text style={{ color: theme.colors.text, lineHeight: 22, fontWeight: theme.fontWeight.semibold }}>
                  {narrative.intro}
                </Text>
              ) : null}

              {narrative.paragraphs.length > 0 ? (
                <View style={{ marginTop: theme.spacing.sm, gap: theme.spacing.sm }}>
                  {narrative.paragraphs.map((paragraph, index) => (
                    <Text key={`${index}-${paragraph.slice(0, 24)}`} style={{ color: theme.colors.textMuted, lineHeight: 21 }}>
                      {paragraph}
                    </Text>
                  ))}
                </View>
              ) : null}

              {narrative.bulletPoints.length > 0 ? (
                <View style={{ marginTop: theme.spacing.md, gap: theme.spacing.xs }}>
                  {narrative.bulletPoints.map((point, index) => (
                    <View
                      key={`${index}-${point.slice(0, 24)}`}
                      style={{
                        borderRadius: theme.radius.md,
                        borderWidth: 1,
                        borderColor: theme.colors.border,
                        backgroundColor: theme.colors.surface2,
                        paddingHorizontal: theme.spacing.sm,
                        paddingVertical: theme.spacing.xs,
                      }}
                    >
                      <Text style={{ color: theme.colors.textMuted, lineHeight: 20 }}>• {point}</Text>
                    </View>
                  ))}
                </View>
              ) : null}
            </View>
          </View>
        ) : null}

        {/* ── Business info ── */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Business Info</Text>
          <View style={styles.card}>
            {profile.business_type ? (
              <Text style={s.textMuted}>Type: {profile.business_type}</Text>
            ) : null}
            {profile.established_year ? (
              <Text style={[s.textMuted, { marginTop: 4 }]}>Est. {profile.established_year}</Text>
            ) : null}
            {profile.credibility_score > 0 ? (
              <Text style={[s.textMuted, { marginTop: 4 }]}>Credibility: {profile.credibility_score}/100</Text>
            ) : null}
            <Text style={[s.textMuted, { marginTop: 4 }]}>Verification: {profile.is_verified ? "Verified" : profile.verification_status.replace(/_/g, " ")}</Text>
          </View>
        </View>

        {/* ── Products ── */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Products ({totalProducts})</Text>

          {loadingProducts ? (
            <ActivityIndicator color={theme.colors.brand} style={{ marginVertical: theme.spacing.md }} />
          ) : products.length === 0 ? (
            <Text style={s.textMuted}>No products available.</Text>
          ) : (
            <FlatList
              data={products}
              keyExtractor={(item) => String(item.id)}
              numColumns={2}
              scrollEnabled={false}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.productItem}
                  onPress={() => router.push(`/(tabs)/products/${item.id}` as never)}
                >
                  {resolveApiAssetUrl(item.image_url) ? (
                    <Image source={{ uri: resolveApiAssetUrl(item.image_url)! }} style={styles.productImage} resizeMode="cover" />
                  ) : (
                    <View style={[styles.productImage, { alignItems: "center", justifyContent: "center" }]}>
                      <Ionicons name="cube-outline" size={32} color={theme.colors.textMuted} />
                    </View>
                  )}
                  <Text style={styles.productName} numberOfLines={2}>{item.name}</Text>
                  {(item.ai_description || item.description) ? (
                    <Text
                      style={{
                        color: theme.colors.textMuted,
                        fontSize: theme.fontSize.xs,
                        lineHeight: 18,
                        paddingHorizontal: theme.spacing.xs,
                        paddingBottom: 2,
                      }}
                      numberOfLines={2}
                    >
                      {item.ai_description || item.description}
                    </Text>
                  ) : null}
                  <Text style={styles.productPrice}>
                    {formatPrice(Number(item.price ?? 0))}
                  </Text>
                  {typeof item.rating === "number" && item.rating > 0 ? (
                    <Text style={{ color: theme.colors.textFaint, fontSize: theme.fontSize.xs, paddingHorizontal: theme.spacing.xs, paddingBottom: theme.spacing.xs }}>
                      ★ {item.rating.toFixed(1)}
                    </Text>
                  ) : null}
                </TouchableOpacity>
              )}
            />
          )}

          {/* Pagination */}
          {totalPages > 1 ? (
            <View style={styles.paginationRow}>
              <TouchableOpacity
                style={[styles.pageBtn, { opacity: page === 0 ? 0.4 : 1 }]}
                onPress={() => page > 0 && setPage(page - 1)}
                disabled={page === 0}
              >
                <Text style={{ color: theme.colors.text }}>← Prev</Text>
              </TouchableOpacity>
              <Text style={s.textMuted}>Page {page + 1} / {totalPages}</Text>
              <TouchableOpacity
                style={[styles.pageBtn, { opacity: page >= totalPages - 1 ? 0.4 : 1 }]}
                onPress={() => page < totalPages - 1 && setPage(page + 1)}
                disabled={page >= totalPages - 1}
              >
                <Text style={{ color: theme.colors.text }}>Next →</Text>
              </TouchableOpacity>
            </View>
          ) : null}
        </View>

        {/* ── Video ── */}
        {profile.video_url ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Brand Video</Text>
            <TouchableOpacity
              style={[styles.card, { flexDirection: "row", alignItems: "center", gap: theme.spacing.md }]}
              onPress={() => Linking.openURL(resolveApiAssetUrl(profile.video_url) || profile.video_url!)}
            >
              <Text style={{ fontSize: 32 }}>▶️</Text>
              <Text style={{ color: theme.colors.brand, fontWeight: theme.fontWeight.semibold }}>
                Watch our brand video
              </Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {/* ── Certifications ── */}
        {certs.length > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Certifications</Text>
            <View style={styles.certRow}>
              {certs.map((cert, idx) => (
                <View key={idx} style={styles.certCard}>
                  {resolveApiAssetUrl(cert.image_url) ? (
                    <Image source={{ uri: resolveApiAssetUrl(cert.image_url)! }} style={{ width: 42, height: 42, borderRadius: 10 }} resizeMode="cover" />
                  ) : (
                    <Text style={{ fontSize: 20 }}>🏅</Text>
                  )}
                  <Text style={{ color: theme.colors.text, fontWeight: theme.fontWeight.semibold, marginTop: 4 }}>
                    {cert.title}
                  </Text>
                  {cert.issuer ? (
                    <Text style={s.textMuted}>{cert.issuer}</Text>
                  ) : null}
                  {cert.year ? (
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{cert.year}</Text>
                  ) : null}
                </View>
              ))}
            </View>
          </View>
        ) : null}

        {recentReviews.length > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recent Reviews</Text>
            {recentReviews.map((review) => (
              <View key={review.id} style={styles.reviewCard}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: theme.spacing.sm }}>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: theme.colors.text, fontWeight: theme.fontWeight.semibold }}>
                      {review.customer_name || review.username || "Verified customer"}
                    </Text>
                    {review.product_name ? (
                      <Text style={[s.textMuted, { marginTop: 2, fontSize: theme.fontSize.xs }]}>
                        on {review.product_name}
                      </Text>
                    ) : null}
                  </View>
                  <Text style={{ color: theme.colors.brand, fontWeight: theme.fontWeight.bold }}>
                    {review.rating.toFixed(1)} ★
                  </Text>
                </View>
                {review.comment ? (
                  <Text style={[s.text, { marginTop: theme.spacing.sm, lineHeight: 20 }]}>{review.comment}</Text>
                ) : null}
                <Text style={[s.textMuted, { marginTop: theme.spacing.xs, fontSize: theme.fontSize.xs }]}>
                  {new Date(review.created_at).toLocaleDateString()}
                </Text>
              </View>
            ))}
          </View>
        ) : null}

        {/* ── Social Links ── */}
        {socialEntries.length > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Find Us On</Text>
            <View style={styles.socialRow}>
              {socialEntries.map(([platform, url]) => (
                <TouchableOpacity
                  key={platform}
                  style={styles.socialBtn}
                  onPress={() => Linking.openURL(url)}
                >
                  <Text style={{ color: theme.colors.text, textTransform: "capitalize" }}>{platform}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ) : null}

        {/* ── Chat CTA ── */}
        <TouchableOpacity
          style={styles.chatBtn}
          onPress={() => router.push(`/chatbot?supplier=${profile.id}` as never)}
        >
          <Ionicons name="chatbubble-outline" size={20} color="#fff" />
          <Text style={{ color: "#fff", fontWeight: theme.fontWeight.bold, fontSize: theme.fontSize.base }}>
            Chat with this Supplier
          </Text>
        </TouchableOpacity>
        <Text style={[s.textMuted, { marginHorizontal: theme.spacing.md, marginTop: -theme.spacing.lg, marginBottom: theme.spacing.xl, fontSize: theme.fontSize.xs }]}>
          Chat is privacy-safe and does not share your personal contact information.
        </Text>
      </ScrollView>
    </View>
  );
}
