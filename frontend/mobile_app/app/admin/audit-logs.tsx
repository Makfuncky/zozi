/**
 * Admin Audit Logs — React Native
 * Browse activity audit trail with filtering by action type and user.
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { buildAdminAuditLogsQuery, normalizeAdminAuditLogPage } from "@/lib/adminManagementUtils";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    card: {
      padding: 12,
      borderRadius: 12,
      borderWidth: 1,
      marginBottom: 8,
    },
    actionBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 6,
      borderWidth: 1,
    },
  });

interface AuditLog {
  id: number;
  user_id: number | null;
  username?: string;
  user_role?: string;
  action: string;
  resource_type?: string;
  resource_id?: number | string;
  details?: Record<string, any> | string | null;
  ip_address?: string;
  status: string;
  created_at: string;
}

const ACTION_COLOR: Record<string, string> = {
  create: "#22c55e",
  update: "#3b82f6",
  delete: "#ef4444",
  login: "#a855f7",
  logout: "#6b7280",
  export: "#f59e0b",
};

function getActionColor(action: string): string {
  const lower = action.toLowerCase();
  for (const [key, color] of Object.entries(ACTION_COLOR)) {
    if (lower.includes(key)) return color;
  }
  return "#9ca3af";
}

export default function AdminAuditLogsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const styles = createStyles(theme);
  const LIMIT = 30;

  const load = useCallback(async (p = 1, reset = false) => {
    try {
      const payload = normalizeAdminAuditLogPage(await apiFetch(buildAdminAuditLogsQuery(p, LIMIT)));
      const data = payload.items;
      if (reset) {
        setLogs(data);
      } else {
        setLogs((prev) => [...prev, ...data]);
      }
      setHasMore(p < payload.total_pages);
    } catch {
      if (reset) setLogs([]);
    }
    setLoading(false);
    setLoadingMore(false);
  }, []);

  useEffect(() => { load(1, true); }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    setPage(1);
    await load(1, true);
    setRefreshing(false);
  };

  const loadMore = () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const next = page + 1;
    setPage(next);
    load(next, false);
  };

  const filtered = logs.filter((l) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      l.action?.toLowerCase().includes(q) ||
      l.username?.toLowerCase().includes(q) ||
      l.resource_type?.toLowerCase().includes(q)
    );
  });

  if (!user || !["admin", "sub_admin", "moderator", "support"].includes(user.role ?? "")) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#ef4444" }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Audit Logs", headerStyle: { backgroundColor: theme.colors.surface0 }, headerTitleStyle: { color: theme.colors.text, fontWeight: "700" } }} />

      <View style={{ padding: theme.spacing.md }}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Filter by action, user, or resource…"
          placeholderTextColor={theme.colors.textMuted}
          style={[s.input, { backgroundColor: theme.colors.surface1, color: theme.colors.text, paddingHorizontal: 14, height: 44, borderRadius: 12 }]}
        />
        {!loading && (
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 8 }}>
            {filtered.length} log{filtered.length !== 1 ? "s" : ""}{query ? " matched" : " loaded"}
          </Text>
        )}
      </View>

      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => String(item.id)}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ paddingHorizontal: theme.spacing.md, paddingBottom: 40 }}
          onEndReached={!query ? loadMore : undefined}
          onEndReachedThreshold={0.3}
          ListEmptyComponent={<Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 40 }}>No audit logs found</Text>}
          ListFooterComponent={loadingMore ? <ActivityIndicator color={theme.colors.brand} style={{ marginVertical: 16 }} /> : null}
          renderItem={({ item }) => {
            const color = getActionColor(item.action);
            return (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderLeftColor: color, borderLeftWidth: 3 }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 2 }}>
                  <View style={[styles.actionBadge, { backgroundColor: color + "22", borderColor: color }]}>
                    <Text style={{ color, fontSize: 10, fontWeight: "800", textTransform: "uppercase" }}>{item.action}</Text>
                  </View>
                  {item.resource_type && (
                    <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>{item.resource_type}{item.resource_id ? ` #${item.resource_id}` : ""}</Text>
                  )}
                </View>
                {item.username && (
                  <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.xs, marginBottom: 2 }}>
                    👤 {item.username}{item.user_role ? ` · ${item.user_role}` : ""}
                  </Text>
                )}
                {item.ip_address && (
                  <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>IP: {item.ip_address}</Text>
                )}
                <Text style={{ color: theme.colors.textMuted, fontSize: 10, marginTop: 4 }}>{new Date(item.created_at).toLocaleString()}</Text>
              </View>
            );
          }}
        />
      )}
    </View>
  );
}
