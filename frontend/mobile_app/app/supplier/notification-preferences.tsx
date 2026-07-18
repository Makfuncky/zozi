import React, { useCallback, useEffect, useMemo, useState } from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, RefreshControl } from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { toast } from "@/lib/toastStore";

type PreferenceField =
  | "notify_new_order"
  | "notify_low_stock"
  | "notify_payout_processed"
  | "notify_doc_expiry"
  | "notify_return_updates"
  | "notify_dispute_updates"
  | "in_app_enabled"
  | "email_enabled"
  | "push_enabled";

interface SupplierNotificationPreferences {
  supplier_id: number;
  notify_new_order: boolean;
  notify_low_stock: boolean;
  notify_payout_processed: boolean;
  notify_doc_expiry: boolean;
  notify_return_updates: boolean;
  notify_dispute_updates: boolean;
  in_app_enabled: boolean;
  email_enabled: boolean;
  push_enabled: boolean;
  updated_at?: string | null;
}

const DEFAULT_PREFERENCES: SupplierNotificationPreferences = {
  supplier_id: 0,
  notify_new_order: true,
  notify_low_stock: true,
  notify_payout_processed: true,
  notify_doc_expiry: true,
  notify_return_updates: true,
  notify_dispute_updates: true,
  in_app_enabled: true,
  email_enabled: true,
  push_enabled: false,
};

const EVENT_TOGGLES: Array<{ key: PreferenceField; label: string; description: string }> = [
  { key: "notify_new_order", label: "New orders", description: "Alert me when a new order is assigned to my storefront." },
  { key: "notify_low_stock", label: "Low stock", description: "Alert me when inventory drops below low-stock threshold." },
  { key: "notify_payout_processed", label: "Payout processed", description: "Alert me when payout requests move to processing or completion." },
  { key: "notify_doc_expiry", label: "Document expiry", description: "Alert me before KYC and compliance documents expire." },
  { key: "notify_return_updates", label: "Return updates", description: "Alert me about return request status updates." },
  { key: "notify_dispute_updates", label: "Dispute updates", description: "Alert me when disputes are reviewed or resolved by admins." },
];

const CHANNEL_TOGGLES: Array<{ key: PreferenceField; label: string; description: string }> = [
  { key: "in_app_enabled", label: "In-app notifications", description: "Show alerts inside supplier mobile screens." },
  { key: "email_enabled", label: "Email notifications", description: "Send alerts to your account email." },
  { key: "push_enabled", label: "Push notifications", description: "Send device push notifications when supported." },
];

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 12, paddingBottom: 40 },
    hero: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    statsRow: { flexDirection: "row", gap: 10, flexWrap: "wrap" },
    statCard: { flexGrow: 1, minWidth: 100, borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
    statValue: { fontSize: theme.fontSize.lg, fontWeight: "800" },
    section: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 10 },
    toggleRow: { borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 8 },
    toggleHeader: { flexDirection: "row", justifyContent: "space-between", gap: 10, alignItems: "center" },
    togglePill: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6 },
    helperRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    helperChip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 10, paddingVertical: 6 },
  });

function formatUpdatedAt(value?: string | null) {
  if (!value) return "Not updated yet";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "Not updated yet" : parsed.toLocaleString();
}

export default function SupplierNotificationPreferencesScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const [prefs, setPrefs] = useState<SupplierNotificationPreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [savingKey, setSavingKey] = useState<PreferenceField | null>(null);

  const loadPreferences = useCallback(async (silent = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const payload = await apiFetch<Partial<SupplierNotificationPreferences>>("/supplier/notification-preferences");
      setPrefs({ ...DEFAULT_PREFERENCES, ...payload });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to load notification preferences");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  const savePreference = useCallback(async (field: PreferenceField) => {
    const nextState = { ...prefs, [field]: !prefs[field] };
    setPrefs(nextState);
    setSavingKey(field);
    try {
      const updated = await apiFetch<Partial<SupplierNotificationPreferences>>("/supplier/notification-preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nextState),
      });
      setPrefs({ ...DEFAULT_PREFERENCES, ...nextState, ...updated });
      toast.success("Notification preferences saved");
    } catch (error) {
      setPrefs(prefs);
      toast.error(error instanceof Error ? error.message : "Failed to save notification preferences");
    } finally {
      setSavingKey(null);
    }
  }, [prefs]);

  const enabledEventCount = useMemo(() => EVENT_TOGGLES.reduce((count, row) => count + (prefs[row.key] ? 1 : 0), 0), [prefs]);
  const enabledChannelCount = useMemo(() => CHANNEL_TOGGLES.reduce((count, row) => count + (prefs[row.key] ? 1 : 0), 0), [prefs]);
  const criticalAlertsEnabled = prefs.notify_doc_expiry && prefs.notify_dispute_updates && prefs.email_enabled;

  return (
    <ScrollView
      testID="supplier-notification-preferences-screen"
      style={s.container}
      contentContainerStyle={styles.scroll}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void loadPreferences(true)} tintColor={theme.colors.brand} />}
    >
      <Stack.Screen options={{ title: "Notification Preferences" }} />

      <View style={[styles.hero, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
        <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>Supplier Notification Preferences</Text>
        <Text style={s.textMuted}>Control which supplier events trigger alerts and which channels deliver them.</Text>
        <View style={styles.helperRow}>
          <View style={[styles.helperChip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{criticalAlertsEnabled ? "Critical alerts protected" : "Critical alerts need attention"}</Text>
          </View>
          <View style={[styles.helperChip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{enabledChannelCount} active delivery channels</Text>
          </View>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.statValue, { color: theme.colors.brand }]}>{enabledEventCount}</Text>
          <Text style={s.textMuted}>Enabled event alerts</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.statValue, { color: theme.colors.info }]}>{enabledChannelCount}</Text>
          <Text style={s.textMuted}>Enabled channels</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.statValue, { color: theme.colors.success, fontSize: theme.fontSize.md }]}>{formatUpdatedAt(prefs.updated_at)}</Text>
          <Text style={s.textMuted}>Last updated</Text>
        </View>
      </View>

      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" />
      ) : (
        <>
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Event Preferences</Text>
            <Text style={s.textMuted}>Keep document expiry and dispute updates enabled so supplier operations do not miss launch-blocking escalations.</Text>
            {EVENT_TOGGLES.map((row) => (
              <TouchableOpacity
                key={row.key}
                testID={`supplier-pref-${row.key}`}
                style={[styles.toggleRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}
                onPress={() => void savePreference(row.key)}
                disabled={savingKey !== null}
              >
                <View style={styles.toggleHeader}>
                  <Text style={[s.text, { flex: 1, fontWeight: "700" }]}>{row.label}</Text>
                  <View style={[styles.togglePill, { backgroundColor: prefs[row.key] ? theme.colors.brand : theme.colors.surface2 }]}> 
                    <Text style={{ color: prefs[row.key] ? theme.colors.onBrand : theme.colors.textMuted, fontWeight: "700" }}>
                      {savingKey === row.key ? "Saving..." : prefs[row.key] ? "On" : "Off"}
                    </Text>
                  </View>
                </View>
                <Text style={s.textMuted}>{row.description}</Text>
                {row.key === "notify_doc_expiry" || row.key === "notify_dispute_updates" ? (
                  <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>Recommended for launch readiness</Text>
                ) : null}
              </TouchableOpacity>
            ))}
          </View>

          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Delivery Channels</Text>
            <Text style={s.textMuted}>In-app plus email is the safest launch combination if push permissions are not enabled on every device yet.</Text>
            {CHANNEL_TOGGLES.map((row) => (
              <TouchableOpacity
                key={row.key}
                testID={`supplier-pref-${row.key}`}
                style={[styles.toggleRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}
                onPress={() => void savePreference(row.key)}
                disabled={savingKey !== null}
              >
                <View style={styles.toggleHeader}>
                  <Text style={[s.text, { flex: 1, fontWeight: "700" }]}>{row.label}</Text>
                  <View style={[styles.togglePill, { backgroundColor: prefs[row.key] ? theme.colors.brand : theme.colors.surface2 }]}> 
                    <Text style={{ color: prefs[row.key] ? theme.colors.onBrand : theme.colors.textMuted, fontWeight: "700" }}>
                      {savingKey === row.key ? "Saving..." : prefs[row.key] ? "On" : "Off"}
                    </Text>
                  </View>
                </View>
                <Text style={s.textMuted}>{row.description}</Text>
                {row.key === "in_app_enabled" || row.key === "email_enabled" ? (
                  <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>Recommended baseline channel</Text>
                ) : null}
              </TouchableOpacity>
            ))}
          </View>
        </>
      )}
    </ScrollView>
  );
}