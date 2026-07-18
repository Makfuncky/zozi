/**
 * Admin Users Management — React Native
 * View, search, and manage all users (activate/deactivate, view role).
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  StyleSheet,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { normalizeAdminUsers, type AdminUserRecord } from "@/lib/adminManagementUtils";
import { useAuthStore } from "@/lib/authStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    pill: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 20,
    },
    card: {
      flexDirection: "row",
      alignItems: "center",
      padding: 14,
      borderRadius: 14,
      borderWidth: 1,
      marginBottom: 10,
      gap: 10,
    },
    roleBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 6,
      borderWidth: 1,
    },
  });

const ROLE_COLOR: Record<string, string> = {
  admin: "#ef4444",
  sub_admin: "#f97316",
  moderator: "#8b5cf6",
  support: "#14b8a6",
  supplier: "#f59e0b",
  customer: "#3b82f6",
};

export default function AdminUsersScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [usersTitle, cancelLabel, errorLabel, failedToUpdateUserStatusLabel, adminAccessRequiredLabel, searchNameOrEmailLabel, userCountLabel, noUsersFoundLabel, joinedLabel, ordersLabel, activeLabel, inactiveLabel, activateLabel, deactivateLabel, activateUserPromptLabel, deactivateUserPromptLabel, allLabel] = useTranslateTexts([
    "Users",
    "Cancel",
    "Error",
    "Failed to update user status",
    "Admin access required",
    "Search name or email…",
    "users",
    "No users found",
    "Joined",
    "orders",
    "Active",
    "Inactive",
    "Activate",
    "Deactivate",
    "This will activate",
    "This will deactivate",
    "All",
  ]);
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [filterRole, setFilterRole] = useState<string>("all");
  const hasAccess = ["admin", "sub_admin"].includes(user?.role ?? "");
  const styles = createStyles(theme);
  const translatedRoles = useTranslateTexts(["All", ...Array.from(new Set(users.map((u) => u.role))).map((role) => role.replace(/_/g, " "))]);

  const load = useCallback(async () => {
    if (!hasAccess) {
      setUsers([]);
      setLoading(false);
      return;
    }
    try {
      const data = await apiFetch<AdminUserRecord[] | { items?: AdminUserRecord[] }>("/admin/users");
      setUsers(normalizeAdminUsers(normalizeCollectionResponse<AdminUserRecord>(data, ["users"])));
    } catch {
      setUsers([]);
    }
    setLoading(false);
  }, [hasAccess]);

  useEffect(() => { load(); }, [load]);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const filtered = users.filter((u) => {
    const lowered = query.toLowerCase();
    const matchQ = !query
      || u.display_name.toLowerCase().includes(lowered)
      || u.username.toLowerCase().includes(lowered)
      || u.email.toLowerCase().includes(lowered);
    const matchR = filterRole === "all" || u.role === filterRole;
    return matchQ && matchR;
  });

  const roles = ["all", ...Array.from(new Set(users.map((u) => u.role)))];

  const toggleActive = (u: AdminUserRecord) => {
    Alert.alert(`${u.is_active ? deactivateLabel : activateLabel} user?`, `${u.is_active ? deactivateUserPromptLabel : activateUserPromptLabel} ${u.display_name}.`, [
      { text: cancelLabel, style: "cancel" },
      {
        text: u.is_active ? deactivateLabel : activateLabel,
        style: u.is_active ? "destructive" : "default",
        onPress: async () => {
          try {
            await apiFetch(`/admin/users/${u.id}/toggle-active`, {
              method: "POST",
            });
            setUsers((prev) => prev.map((x) => x.id === u.id ? { ...x, is_active: !x.is_active } : x));
          } catch {
            Alert.alert(errorLabel, failedToUpdateUserStatusLabel);
          }
        },
      },
    ]);
  };

  if (!hasAccess) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#ef4444" }}>{adminAccessRequiredLabel}</Text>
      </View>
    );
  }

  return (
    <View style={[{ flex: 1, backgroundColor: theme.colors.surface0 }, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen options={{ title: usersTitle, headerStyle: { backgroundColor: theme.colors.surface0 }, headerTitleStyle: { color: theme.colors.text, fontWeight: "700" } }} />

      {/* Search */}
      <View style={{ padding: theme.spacing.md, gap: 10 }}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder={searchNameOrEmailLabel}
          placeholderTextColor={theme.colors.textMuted}
          style={[s.input, { backgroundColor: theme.colors.surface1, color: theme.colors.text, paddingHorizontal: 14, height: 44, borderRadius: 12 }]}
        />
        {/* Role filter */}
        <View style={{ flexDirection: "row", gap: 8 }}>
          {roles.map((r) => (
            <TouchableOpacity
              key={r}
              onPress={() => setFilterRole(r)}
              style={[styles.pill, { backgroundColor: filterRole === r ? theme.colors.brand : theme.colors.surface2 }]}
            >
              <Text style={{ color: filterRole === r ? "#000" : theme.colors.textMuted, fontSize: theme.fontSize.xs, fontWeight: "600", textTransform: "capitalize" }}>{translatedRoles[roles.indexOf(r)] || (r === "all" ? allLabel : r.replace(/_/g, " "))}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{filtered.length} {userCountLabel}</Text>
      </View>

      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => String(item.id)}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ paddingHorizontal: theme.spacing.md, paddingBottom: 40 }}
          ListEmptyComponent={<Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 40 }}>{noUsersFoundLabel}</Text>}
          renderItem={({ item }) => (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                  <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.sm }} numberOfLines={1}>{item.display_name}</Text>
                  <View style={[styles.roleBadge, { backgroundColor: ROLE_COLOR[item.role] + "22", borderColor: ROLE_COLOR[item.role] }]}>
                    <Text style={{ color: ROLE_COLOR[item.role], fontSize: 10, fontWeight: "700", textTransform: "uppercase" }}>{item.role}</Text>
                  </View>
                </View>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 2 }}>{item.email}</Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: 10, marginTop: 4 }}>
                  {joinedLabel} {formatLocalizedDate(item.created_at, locale, { month: "short", day: "numeric", year: "numeric" })}
                  {item.total_orders !== undefined ? ` · ${item.total_orders} ${ordersLabel}` : ""}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => toggleActive(item)}
                style={[styles.pill, { backgroundColor: item.is_active ? "#22c55e22" : "#ef444422", borderColor: item.is_active ? "#22c55e" : "#ef4444", borderWidth: 1 }]}
              >
                <Text style={{ color: item.is_active ? "#22c55e" : "#ef4444", fontSize: theme.fontSize.xs, fontWeight: "700" }}>
                  {item.is_active ? activeLabel : inactiveLabel}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        />
      )}
    </View>
  );
}
