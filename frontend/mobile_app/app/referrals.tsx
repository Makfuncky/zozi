import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Share,
} from "react-native";
import { setStringAsync } from "@/lib/clipboard";
import { useRouter } from "expo-router";
import AppHeader from "@/components/ui/AppHeader";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "../lib/themeStore";
import { useAuthStore } from "../lib/authStore";
import {
  buildAppReferralLink,
  claimReferralShareBonus,
  getReferralDashboard,
  getReferralHistory,
  type ReferralActivityItem,
  type ReferralDashboard,
} from "../lib/api";
import { makeStyles, AppTheme } from "../theme";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: {
      padding: theme.spacing.md,
      gap: theme.spacing.md,
      paddingBottom: 48,
    },
    card: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      padding: theme.spacing.md,
      gap: theme.spacing.sm,
    },
    statsRow: {
      flexDirection: "row",
      gap: 8,
    },
    stat: {
      flex: 1,
      minWidth: 72,
      borderRadius: 12,
      borderWidth: 1,
      paddingVertical: 10,
      alignItems: "center",
    },
    infoBox: {
      borderRadius: 12,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    codeChip: {
      borderRadius: 10,
      borderWidth: 1,
      paddingVertical: 6,
      paddingHorizontal: 10,
      alignSelf: "flex-start",
    },
    linkBox: {
      borderRadius: 12,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
      gap: 4,
    },
    actionRow: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
      marginTop: 4,
    },
    primaryBtn: {
      flex: 1,
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
      borderRadius: 12,
      paddingVertical: 10,
      paddingHorizontal: 12,
    },
    secondaryBtn: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 6,
      borderRadius: 12,
      borderWidth: 1,
      paddingVertical: 10,
      paddingHorizontal: 12,
    },
    activityItem: {
      borderRadius: 10,
      borderWidth: 1,
      paddingVertical: 10,
      paddingHorizontal: 12,
      gap: 4,
    },
    footerRow: {
      marginTop: 8,
      alignItems: "center",
    },
  });

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString();
}

function eventLabel(event: ReferralActivityItem): string {
  if (event.description && event.description.trim()) return event.description;
  return event.event_type.replace(/_/g, " ");
}

export default function ReferralHistoryScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { isLoggedIn } = useAuthStore();

  const [dashboard, setDashboard] = useState<ReferralDashboard | null>(null);
  const [items, setItems] = useState<ReferralActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [copying, setCopying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const pageSize = 20;
  const hasMore = items.length < total;

  const hydrate = useCallback(async (reset: boolean) => {
    if (reset) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    const offset = reset ? 0 : items.length;

    if (reset) {
      setError(null);
    }

    try {
      const [dash, history] = await Promise.all([
        getReferralDashboard(),
        getReferralHistory(pageSize, offset),
      ]);

      setDashboard(dash);
      setTotal(history.total || 0);
      setItems((prev) => (reset ? history.items : [...prev, ...history.items]));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to load referral activity right now.");
      if (reset) {
        setDashboard(null);
        setItems([]);
        setTotal(0);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [items.length]);

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace("/(auth)/login");
      return;
    }
    void hydrate(true);
  }, [hydrate, isLoggedIn, router]);

  async function onRefresh() {
    setRefreshing(true);
    setMessage(null);
    await hydrate(true);
  }

  async function onShareInvite() {
    if (!dashboard) return;
    setClaiming(true);
    setError(null);
    setMessage(null);
    try {
      const appLink = buildAppReferralLink(dashboard.referral_code);
      const shareResult = await Share.share({
        message: `Join me on ZOZI and use my invite code ${dashboard.referral_code}.\nApp: ${appLink}\nWeb: ${dashboard.referral_link}`,
      });

      if (shareResult.action !== Share.dismissedAction) {
        const claim = await claimReferralShareBonus("mobile_referral_history");
        setMessage(claim.message);
        await hydrate(true);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to share right now.");
    } finally {
      setClaiming(false);
    }
  }

  async function onCopyLink() {
    if (!dashboard?.referral_link) return;
    setCopying(true);
    setError(null);
    setMessage(null);
    try {
      await setStringAsync(dashboard.referral_link);
      setMessage("Referral link copied.");
    } catch {
      setError("Could not copy referral link.");
    } finally {
      setCopying(false);
    }
  }

  async function onClaimDailyBonus() {
    setClaiming(true);
    setError(null);
    setMessage(null);
    try {
      const claim = await claimReferralShareBonus("mobile_referral_bonus");
      setMessage(claim.message);
      await hydrate(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to claim the daily bonus right now.");
    } finally {
      setClaiming(false);
    }
  }

  return (
    <View style={[s.container, { flex: 1 }]}>
      <AppHeader showSearch={false} />

      {loading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color={theme.colors.brand} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
        >
          {error ? (
              <View style={[styles.infoBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}> 
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm }}>{error}</Text>
            </View>
          ) : null}

          {message ? (
              <View style={[styles.infoBox, { backgroundColor: theme.colors.successBg, borderColor: theme.colors.success }]}> 
              <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm }}>{message}</Text>
            </View>
          ) : null}

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <View>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", letterSpacing: 0.7 }]}>Referral Ledger</Text>
                <Text style={[s.text, { fontWeight: "700", marginTop: 2 }]}>Track invites and share rewards</Text>
              </View>
              <Ionicons name="gift-outline" size={22} color={theme.colors.brand} />
            </View>

            {dashboard ? (
              <>
                <View style={styles.statsRow}>
                  <View style={[styles.stat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Total</Text>
                    <Text style={[s.text, { fontWeight: "800", color: theme.colors.brand }]}>{dashboard.total_points}</Text>
                  </View>
                  <View style={[styles.stat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Referral</Text>
                    <Text style={[s.text, { fontWeight: "700" }]}>{dashboard.referral_points}</Text>
                  </View>
                  <View style={[styles.stat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Sharing</Text>
                    <Text style={[s.text, { fontWeight: "700" }]}>{dashboard.sharing_points}</Text>
                  </View>
                  <View style={[styles.stat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Friends</Text>
                    <Text style={[s.text, { fontWeight: "700" }]}>{dashboard.referred_count}</Text>
                  </View>
                </View>

                <View style={[styles.codeChip, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Code</Text>
                  <Text style={[s.text, { fontWeight: "800", letterSpacing: 1.2 }]}>{dashboard.referral_code}</Text>
                </View>

                <View style={[styles.linkBox, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Invite link</Text>
                  <Text style={[s.text, { fontSize: theme.fontSize.sm }]} numberOfLines={2}>{dashboard.referral_link}</Text>
                </View>

                <View style={styles.actionRow}>
                  <TouchableOpacity
                    onPress={onShareInvite}
                    disabled={claiming}
                    style={[styles.primaryBtn, { backgroundColor: theme.colors.brand, opacity: claiming ? 0.75 : 1 }]}
                  >
                    <Ionicons name="share-social-outline" size={18} color={theme.colors.onBrand} />
                    <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>{claiming ? "Sharing..." : "Share invite"}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={onCopyLink}
                    disabled={copying}
                    style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
                  >
                    <Ionicons name="copy-outline" size={16} color={theme.colors.textMuted} />
                    <Text style={{ color: theme.colors.textMuted, fontWeight: "600" }}>{copying ? "Copying..." : "Copy link"}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={onClaimDailyBonus}
                    disabled={claiming}
                    style={[styles.secondaryBtn, { borderColor: theme.colors.brand, backgroundColor: theme.colors.pillActiveBg }]}
                  >
                    <Ionicons name="flash-outline" size={16} color={theme.colors.brand} />
                    <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{claiming ? "Claiming..." : "Claim daily +5"}</Text>
                  </TouchableOpacity>
                </View>
              </>
            ) : (
              <Text style={s.textMuted}>Referral information is unavailable right now.</Text>
            )}
          </View>

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>Activity</Text>
            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{items.length} of {total} entries loaded</Text>

            <View style={{ gap: 8, marginTop: 4 }}>
              {items.length === 0 ? (
                <Text style={s.textMuted}>No referral events yet. Share your invite to start earning points.</Text>
              ) : (
                items.map((item) => (
                  <View key={item.id} style={[styles.activityItem, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                    <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                      <Text style={[s.text, { flex: 1, fontWeight: "600" }]} numberOfLines={1}>{eventLabel(item)}</Text>
                      <Text style={{ color: theme.colors.success, fontWeight: "800" }}>+{item.points}</Text>
                    </View>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{formatDate(item.created_at)}{item.referred_username ? ` • ${item.referred_username}` : ""}</Text>
                  </View>
                ))
              )}
            </View>

            {hasMore && (
              <View style={styles.footerRow}>
                <TouchableOpacity
                  onPress={() => void hydrate(false)}
                  disabled={loadingMore}
                  style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2, opacity: loadingMore ? 0.7 : 1 }]}
                >
                  <Ionicons name="refresh-outline" size={16} color={theme.colors.textMuted} />
                  <Text style={{ color: theme.colors.textMuted, fontWeight: "600" }}>{loadingMore ? "Loading..." : "Load more"}</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </ScrollView>
      )}
    </View>
  );
}
