import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { setStringAsync } from "@/lib/clipboard";
import { getPublicCoupons, type Coupon } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import AppHeader from "@/components/ui/AppHeader";

function formatDiscount(c: Coupon) {
  if (c.discount_type === "percentage") return `${c.discount_value}% OFF`;
  return `$${Number(c.discount_value).toFixed(2)} OFF`;
}

function isExpired(expires_at: string | null) {
  if (!expires_at) return false;
  return new Date(expires_at) < new Date();
}

function daysLeft(expires_at: string | null) {
  if (!expires_at) return null;
  const diff = Math.ceil((new Date(expires_at).getTime() - Date.now()) / 86_400_000);
  return diff;
}

export default function CouponsScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);

  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await getPublicCoupons();
      setCoupons(data.filter((coupon) => coupon.is_active && !isExpired(coupon.expires_at)));
    } catch { /* ignore */ }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const copy = (code: string) => {
    void setStringAsync(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2500);
  };

  const renderItem = ({ item }: { item: Coupon }) => {
    const expired = isExpired(item.expires_at);
    const days = daysLeft(item.expires_at);
    const isCopied = copiedCode === item.code;
    const exhausted = item.max_uses > 0 && item.current_uses >= item.max_uses;

    return (
      <View style={[localStyles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        {/* Dashed left band */}
        <View style={[localStyles.band, { backgroundColor: theme.colors.brand }]}>
          <Text style={localStyles.bandText}>{formatDiscount(item)}</Text>
        </View>

        <View style={{ flex: 1, padding: 14, gap: 6 }}>
          {/* Code row */}
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <Text style={[s.text, { fontFamily: "monospace", fontSize: theme.fontSize.md, fontWeight: "800", letterSpacing: 2 }]}>
              {item.code}
            </Text>
            <TouchableOpacity
              style={[localStyles.copyBtn, { backgroundColor: isCopied ? theme.colors.success : theme.colors.brand }]}
              onPress={() => copy(item.code)}
              disabled={expired || exhausted}
            >
              <Text style={{ color: "#fff", fontSize: theme.fontSize.sm, fontWeight: "700" }}>
                {isCopied ? "Copied!" : "Copy"}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Min order */}
          {item.min_order_amount > 0 && (
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
              Min. order: ${Number(item.min_order_amount).toFixed(2)}
            </Text>
          )}

          {/* Use count */}
          {item.max_uses > 0 && (
            <Text style={{ color: exhausted ? theme.colors.danger : theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
              {exhausted
                ? "All uses claimed"
                : `${item.max_uses - item.current_uses} of ${item.max_uses} uses remaining`}
            </Text>
          )}

          {/* Expiry */}
          {item.expires_at && (
            <Text style={{ color: days != null && days <= 3 ? theme.colors.warning : theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
              {days != null && days > 0
                ? `⏰ Expires in ${days} day${days === 1 ? "" : "s"}`
                : "Expires today"}
            </Text>
          )}
        </View>
      </View>
    );
  };

  return (
    <>
      <AppHeader showSearch={false} />
      <View style={[s.container, { flex: 1 }]}>
        {loading ? (
          <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
            <ActivityIndicator color={theme.colors.brand} size="large" />
          </View>
        ) : (
          <FlatList
            data={coupons}
            keyExtractor={(c) => String(c.id)}
            renderItem={renderItem}
            contentContainerStyle={{ padding: theme.spacing.md, gap: 12, paddingBottom: 40 }}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => { setRefreshing(true); load(true); }}
                tintColor={theme.colors.brand}
              />
            }
            ListHeaderComponent={
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginBottom: theme.spacing.xs }}>
                {coupons.length === 0 ? "" : `${coupons.length} coupon${coupons.length === 1 ? "" : "s"} available`}
              </Text>
            }
            ListEmptyComponent={
              <View style={{ flex: 1, alignItems: "center", paddingTop: 80, gap: 12 }}>
                <Text style={{ fontSize: theme.fontSize["2xl"] }}>🏷️</Text>
                <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>No coupons right now</Text>
                <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>
                  Check back later for promotions and discount codes.
                </Text>
              </View>
            }
          />
        )}
      </View>
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  card: {
    flexDirection: "row",
    borderWidth: 1,
    borderRadius: 14,
    overflow: "hidden",
  },
  band: {
    width: 66,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: theme.spacing.md,
  },
  bandText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: theme.fontSize.sm,
    textAlign: "center",
    transform: [{ rotate: "-90deg" }],
    width: 90,
  },
  copyBtn: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: theme.radius.md,
  },
});
