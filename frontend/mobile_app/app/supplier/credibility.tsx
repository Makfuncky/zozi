/**
 * Supplier Credibility — React Native
 * Mirrors frontend/web_app/src/app/supplier/credibility/page.tsx
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

// ── Data ──────────────────────────────────────────────────────────────────────

interface BadgeData {
  credibility_score: number;
  badge_level: "none" | "bronze" | "silver" | "gold";
}

const BADGE_CONFIG = {
  none:   { label: "No Badge",         emoji: "—",  color: "#999" },
  bronze: { label: "Bronze Supplier",  emoji: "🥉", color: "#ea580c" },
  silver: { label: "Silver Supplier",  emoji: "🥈", color: "#6b7280" },
  gold:   { label: "Gold Supplier",    emoji: "🥇", color: "#d97706" },
} as const;

const CRITERIA = [
  { label: "Order Fulfilment Rate",   max: 35, tip: "Complete orders on time (shipped / delivered / completed)." },
  { label: "Average Product Rating",  max: 25, tip: "Higher customer ratings (1–5 ★) push this up." },
  { label: "Document Verification",   max: 20, tip: "Upload and have your KYC documents approved by admin." },
  { label: "Account Age",             max: 10, tip: "Each month on the platform earns 1 point (up to 10)." },
  { label: "Approved Products",       max: 10, tip: "1 point per product approved by admin (up to 10)." },
];

const THRESHOLDS = [
  { badge: "bronze", min: 40, max: 64, emoji: "🥉", color: "#ea580c" },
  { badge: "silver", min: 65, max: 84, emoji: "🥈", color: "#6b7280" },
  { badge: "gold",   min: 85, max: 100, emoji: "🥇", color: "#d97706" },
] as const;

// ── Styles ────────────────────────────────────────────────────────────────────

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 16, paddingBottom: 50 },
    card: {
      borderRadius: theme.radius.xl, borderWidth: 1,
      padding: theme.spacing.md,
    },
    scoreCard: {
      borderRadius: theme.radius.xl, borderWidth: 2,
      padding: theme.spacing.md, gap: 10,
    },
    scoreNumber: { fontSize: 48, fontWeight: "900", lineHeight: 52 },
    scoreMax: { fontSize: 18, fontWeight: "400" },
    barBg: { height: 12, borderRadius: 6, overflow: "hidden", marginTop: 8 },
    barFill: { height: "100%", borderRadius: 6 },
    markerRow: {
      flexDirection: "row", justifyContent: "space-between",
      marginTop: 4,
    },
    nextBadgeBox: {
      borderRadius: theme.radius.md, padding: theme.spacing.sm,
      marginTop: 8,
    },
    badgeLevelItem: {
      borderRadius: theme.radius.lg, borderWidth: 1,
      padding: theme.spacing.sm, alignItems: "center", gap: 4,
      flex: 1,
    },
    criterionRow: { gap: 4, marginBottom: 12 },
    criterionBar: { height: 4, borderRadius: 2, overflow: "hidden", marginTop: 4 },
    actionCard: {
      flexDirection: "row", alignItems: "center", gap: 10,
      padding: theme.spacing.sm, borderRadius: theme.radius.md,
      borderWidth: 1,
    },
    refreshBtn: {
      flexDirection: "row", alignItems: "center", gap: 6,
      paddingHorizontal: 14, paddingVertical: 8,
      borderRadius: theme.radius.md, borderWidth: 1,
    },
  });

// ── Score bar with threshold markers ─────────────────────────────────────────

function ScoreBar({ score, theme }: { score: number; theme: any }) {
  const styles = createStyles(theme);
  const barColor =
    score >= 85 ? "#d97706"
    : score >= 65 ? "#6b7280"
    : score >= 40 ? "#ea580c"
    : theme.colors.picking;

  return (
    <View>
      <View style={[styles.barBg, { backgroundColor: theme.colors.surface2 }]}>
        <View style={[styles.barFill, { width: `${score}%` as any, backgroundColor: barColor }]} />
      </View>
      <View style={styles.markerRow}>
        <Text style={{ fontSize: 9, color: theme.colors.textFaint }}>0</Text>
        <Text style={{ fontSize: 9, color: "#ea580c" }}>Bronze 40</Text>
        <Text style={{ fontSize: 9, color: "#6b7280" }}>Silver 65</Text>
        <Text style={{ fontSize: 9, color: "#d97706" }}>Gold 85</Text>
        <Text style={{ fontSize: 9, color: theme.colors.textFaint }}>100</Text>
      </View>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────

export default function SupplierCredibilityScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [badge, setBadge] = useState<BadgeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await apiFetch<BadgeData>("/supplier/badge");
      setBadge(res);
    } catch {}
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  const cfg = BADGE_CONFIG[(badge?.badge_level ?? "none") as keyof typeof BADGE_CONFIG];
  const score = badge?.credibility_score ?? 0;
  const nextThreshold = THRESHOLDS.find((t) => score < t.min);
  const pointsToNext = nextThreshold ? nextThreshold.min - score : 0;
  const currentLevel = badge?.badge_level ?? "none";

  return (
    <>
      <Stack.Screen options={{ title: "Credibility & Trust Score" }} />
      <ScrollView
        style={s.container}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.brand} style={{ marginTop: 40 }} />
        ) : (
          <>
            {/* Score Card */}
            <View style={[styles.scoreCard, { backgroundColor: theme.colors.surface1, borderColor: cfg.color + "88" }]}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 16 }}>
                <Text style={{ fontSize: 52 }}>{cfg.emoji}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: theme.fontSize.xs, fontWeight: "700", color: cfg.color, letterSpacing: 1 }}>
                    {cfg.label.toUpperCase()}
                  </Text>
                  <Text style={[styles.scoreNumber, { color: theme.colors.text }]}>
                    {score}
                    <Text style={[styles.scoreMax, { color: theme.colors.textMuted }]}> / 100</Text>
                  </Text>
                </View>
              </View>
              <ScoreBar score={score} theme={theme} />

              {nextThreshold && (
                <View style={[styles.nextBadgeBox, { backgroundColor: theme.colors.surface2 }]}>
                  <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
                    › You need{" "}
                    <Text style={{ fontWeight: "700", color: theme.colors.text }}>{pointsToNext} more pt{pointsToNext !== 1 ? "s" : ""}</Text>
                    {" "}to reach{" "}
                    <Text style={{ fontWeight: "700", color: nextThreshold.color }}>
                      {nextThreshold.emoji} {nextThreshold.badge.charAt(0).toUpperCase() + nextThreshold.badge.slice(1)}
                    </Text>
                  </Text>
                </View>
              )}

              {score >= 85 && (
                <View style={[styles.nextBadgeBox, { backgroundColor: "#d97706" + "22" }]}>
                  <Text style={{ color: "#d97706", fontWeight: "700", fontSize: theme.fontSize.sm }}>
                    🎉 You have the highest badge! Keep it up.
                  </Text>
                </View>
              )}
            </View>

            {/* Badge Levels */}
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "700", marginBottom: 10 }]}>Badge Levels</Text>
              <View style={{ flexDirection: "row", gap: 8 }}>
                {(["none", "bronze", "silver", "gold"] as const).map((level) => {
                  const c = BADGE_CONFIG[level];
                  const t = THRESHOLDS.find((th) => th.badge === level);
                  const isCurrent = currentLevel === level;
                  return (
                    <View
                      key={level}
                      style={[
                        styles.badgeLevelItem,
                        {
                          borderColor: isCurrent ? c.color : theme.colors.border,
                          backgroundColor: isCurrent ? c.color + "18" : theme.colors.surface2,
                        },
                      ]}
                    >
                      <Text style={{ fontSize: 22 }}>{c.emoji}</Text>
                      <Text style={{ fontSize: theme.fontSize.xs, fontWeight: "700", color: c.color, textAlign: "center" }}>
                        {level === "none" ? "None" : level.charAt(0).toUpperCase() + level.slice(1)}
                      </Text>
                      <Text style={{ fontSize: 9, color: theme.colors.textFaint, textAlign: "center" }}>
                        {t ? `${t.min}–${t.max} pts` : "0–39 pts"}
                      </Text>
                      {isCurrent && (
                        <Text style={{
                          fontSize: 9, fontWeight: "700", color: c.color,
                          backgroundColor: c.color + "22",
                          paddingHorizontal: 6, paddingVertical: 2, borderRadius: 8,
                        }}>
                          CURRENT
                        </Text>
                      )}
                    </View>
                  );
                })}
              </View>
            </View>

            {/* Score Breakdown */}
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "700", marginBottom: 6 }]}>How Your Score is Calculated</Text>
              {CRITERIA.map(({ label, max, tip }) => (
                <View key={label} style={styles.criterionRow}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <View style={{ flex: 1, marginRight: 8 }}>
                      <Text style={[s.text, { fontWeight: "600", fontSize: theme.fontSize.sm }]}>{label}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginTop: 2 }]}>{tip}</Text>
                    </View>
                    <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.xs }}>
                      Max {max} pts
                    </Text>
                  </View>
                  <View style={[styles.criterionBar, { backgroundColor: theme.colors.surface2 }]}>
                    <View style={{ width: "100%", height: "100%", backgroundColor: theme.colors.brand + "44" }} />
                  </View>
                </View>
              ))}
            </View>

            {/* Improve Score — quick actions */}
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "700", marginBottom: 10 }]}>Improve Your Score</Text>
              {[
                { icon: "document-text-outline", label: "Upload KYC Documents", desc: "Earn up to 20 pts", route: "/supplier/documents" },
                { icon: "cube-outline", label: "Add More Products",    desc: "Earn up to 10 pts", route: "/supplier/products/" },
                { icon: "star", label: "Boost Product Ratings", desc: "Earn up to 25 pts", route: "/supplier/products/" },
              ].map(({ icon, label, desc, route }) => (
                <TouchableOpacity
                  key={label}
                  style={[styles.actionCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
                  onPress={() => router.push(route as never)}
                  activeOpacity={0.7}
                >
                   <Ionicons name={icon as any} size={24} color={theme.colors.brand} />
                  <View style={{ flex: 1 }}>
                    <Text style={[s.text, { fontWeight: "600", fontSize: theme.fontSize.sm }]}>{label}</Text>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{desc}</Text>
                  </View>
                  <Text style={{ color: theme.colors.textFaint }}>›</Text>
                </TouchableOpacity>
              ))}
            </View>
          </>
        )}
      </ScrollView>
    </>
  );
}
