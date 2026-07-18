import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useRouter } from "expo-router";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { listReturns, ReturnRequest } from "@/lib/api";
import { useTranslateTexts } from "@/lib/useTranslate";
import AppHeader from "@/components/ui/AppHeader";

// Status colors derived from theme tokens
function getStatusColors(theme: AppTheme) {
  return {
    pending: theme.colors.warning,
    approved: theme.colors.info,
    rejected: theme.colors.danger,
    completed: theme.colors.success,
    refunded: theme.colors.pillActive,
  };
}

function StatusBadge({ status, theme }: { status: string; theme: AppTheme }) {
  const colors = getStatusColors(theme);
  const color = colors[status as keyof typeof colors] ?? theme.colors.textMuted;
  return (
    <View style={[styles.badge, { backgroundColor: color + "22", borderColor: color }]}>
      <Text style={[styles.badgeText, { color }]}>{status.toUpperCase()}</Text>
    </View>
  );
}

function ReturnsScreen() {
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuthStore();
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const colors = getStatusColors(theme);
  const [
    myReturnsLabel,
    noReturnsYetLabel,
    failedToLoadReturnsLabel,
    backLabel,
  ] = useTranslateTexts([
    "My Returns",
    "No return requests yet.",
    "Failed to load returns.",
    "Back",
  ]);

  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadReturns = useCallback(async () => {
    if (!isLoggedIn) return;
    try {
      const data = await listReturns();
      setReturns(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setError(failedToLoadReturnsLabel);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isLoggedIn, failedToLoadReturnsLabel]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/(auth)/login");
      return;
    }
    loadReturns();
  }, [isLoggedIn, authLoading, router, loadReturns]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadReturns();
  }, [loadReturns]);

  if (loading || authLoading) {
    return (
      <View style={[s.container, styles.centered]}>
        <ActivityIndicator color={theme.colors.brand} size="large" />
      </View>
    );
  }

  return (
    <View style={s.container}>
      <AppHeader showSearch={false} />
      {error && (
        <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
          <Text style={{ color: theme.colors.danger, fontSize: 13 }}>{error}</Text>
        </View>
      )}
      <FlatList
        data={returns}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 32, gap: 12 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />
        }
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={{ color: theme.colors.textMuted, fontSize: 15, textAlign: "center", marginTop: 60 }}>
              {noReturnsYetLabel}
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => router.push(`/returns/${item.id}` as any)}
            style={[
              styles.card,
              {
                backgroundColor: theme.colors.surface1,
                borderColor: theme.colors.border,
              },
            ]}
            activeOpacity={0.7}
          >
            <View style={styles.cardHeader}>
              <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 14 }}>
                Return #{item.id}
              </Text>
              <StatusBadge status={item.status} theme={theme} />
            </View>
            <Text style={{ color: theme.colors.textMuted, fontSize: 13, marginTop: 4 }}>
              Order #{item.order_id}
            </Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: 13, marginTop: 2 }} numberOfLines={2}>
              {item.reason}
            </Text>
            {item.refund_amount != null && (
              <Text style={{ color: theme.colors.success, fontSize: 13, fontWeight: "600", marginTop: 4 }}>
                Refund: ${item.refund_amount.toFixed(2)}
              </Text>
            )}
            <Text style={{ color: theme.colors.textFaint, fontSize: 11, marginTop: 6 }}>
              {new Date(item.created_at).toLocaleDateString()}
            </Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  badge: {
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  errorBox: {
    margin: 16,
    marginBottom: 0,
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
  },
});

export default ReturnsScreen;
