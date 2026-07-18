import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  Switch,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from "react-native";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";
import { unregisterPushToken } from "@/lib/api";
import ScreenHeader from "@/components/ui/ScreenHeader";

// ── Storage helpers ────────────────────────────────────────────────────────────

const PREFS_KEY = "zozi_push_prefs";
const TOKEN_KEY = "zozi_push_token";

async function loadFromStore(key: string): Promise<string | null> {
  if (Platform.OS === "web") return localStorage.getItem(key);
  try {
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
}

async function saveToStore(key: string, value: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.setItem(key, value);
    return;
  }
  try {
    await SecureStore.setItemAsync(key, value);
  } catch {
    // ignore
  }
}

async function deleteFromStore(key: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.removeItem(key);
    return;
  }
  try {
    await SecureStore.deleteItemAsync(key);
  } catch {
    // ignore
  }
}

// ── Types ──────────────────────────────────────────────────────────────────────

interface PushPreferences {
  enabled: boolean;
  order_updates: boolean;
  promotions: boolean;
  flash_sales: boolean;
  new_arrivals: boolean;
  returns_refunds: boolean;
  chat_messages: boolean;
}

const DEFAULT_PREFS: PushPreferences = {
  enabled: true,
  order_updates: true,
  promotions: true,
  flash_sales: true,
  new_arrivals: false,
  returns_refunds: true,
  chat_messages: true,
};

const CATEGORIES: { key: keyof Omit<PushPreferences, "enabled">; label: string; description: string }[] = [
  { key: "order_updates", label: "Order Updates", description: "Shipping, delivery, and order status changes" },
  { key: "promotions", label: "Promotions & Deals", description: "Exclusive discounts and special offers" },
  { key: "flash_sales", label: "Flash Sales", description: "Limited-time flash sale alerts" },
  { key: "new_arrivals", label: "New Arrivals", description: "New products from brands you follow" },
  { key: "returns_refunds", label: "Returns & Refunds", description: "Status updates on your returns and refunds" },
  { key: "chat_messages", label: "Chat Messages", description: "Messages from support and sellers" },
];

// ── Styles ─────────────────────────────────────────────────────────────────────

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: {
      flex: 1,
    },
    section: {
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.md,
      borderRadius: theme.radius.lg,
      overflow: "hidden",
    },
    sectionHeader: {
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
    },
    sectionTitle: {
      fontSize: 12,
      fontWeight: "600",
      letterSpacing: 0.5,
      textTransform: "uppercase",
    },
    row: {
      flexDirection: "row",
      alignItems: "center",
      paddingHorizontal: theme.spacing.md,
      paddingVertical: 14,
      borderBottomWidth: StyleSheet.hairlineWidth,
    },
    rowLast: {
      borderBottomWidth: 0,
    },
    rowContent: {
      flex: 1,
      marginRight: theme.spacing.sm,
    },
    rowLabel: {
      fontSize: 15,
      fontWeight: "500",
    },
    rowDesc: {
      fontSize: 12,
      marginTop: 2,
    },
    masterRow: {
      flexDirection: "row",
      alignItems: "center",
      paddingHorizontal: theme.spacing.md,
      paddingVertical: 16,
    },
    masterContent: {
      flex: 1,
    },
    masterLabel: {
      fontSize: 16,
      fontWeight: "600",
    },
    masterDesc: {
      fontSize: 13,
      marginTop: 3,
    },
    divider: {
      height: StyleSheet.hairlineWidth,
      marginHorizontal: theme.spacing.md,
    },
    infoBox: {
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.md,
      padding: theme.spacing.md,
      borderRadius: theme.radius.lg,
      borderWidth: 1,
    },
    infoText: {
      fontSize: 13,
      lineHeight: 20,
    },
    deviceSection: {
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.md,
      borderRadius: theme.radius.lg,
      overflow: "hidden",
    },
    deviceRow: {
      flexDirection: "row",
      alignItems: "center",
      paddingHorizontal: theme.spacing.md,
      paddingVertical: 14,
    },
    deviceLabel: {
      flex: 1,
      fontSize: 14,
    },
    removeBtn: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: theme.radius.md,
      borderWidth: 1,
    },
    removeBtnText: {
      fontSize: 13,
      fontWeight: "500",
    },
    bottomPad: {
      height: 32,
    },
  });

// ── Screen ─────────────────────────────────────────────────────────────────────

export default function PushNotificationsScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);

  const [prefs, setPrefs] = useState<PushPreferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [registeredToken, setRegisteredToken] = useState<string | null>(null);
  const [removingDevice, setRemovingDevice] = useState(false);

  useEffect(() => {
    (async () => {
      const raw = await loadFromStore(PREFS_KEY);
      if (raw) {
        try {
          setPrefs({ ...DEFAULT_PREFS, ...JSON.parse(raw) });
        } catch {
          // use defaults
        }
      }
      const token = await loadFromStore(TOKEN_KEY);
      setRegisteredToken(token);
      setLoading(false);
    })();
  }, []);

  const persistPrefs = useCallback(
    async (updated: PushPreferences) => {
      setSaving(true);
      await saveToStore(PREFS_KEY, JSON.stringify(updated));
      setSaving(false);
    },
    []
  );

  const setEnabled = useCallback(
    (val: boolean) => {
      const updated = { ...prefs, enabled: val };
      setPrefs(updated);
      persistPrefs(updated);
    },
    [prefs, persistPrefs]
  );

  const setCategory = useCallback(
    (key: keyof Omit<PushPreferences, "enabled">, val: boolean) => {
      const updated = { ...prefs, [key]: val };
      setPrefs(updated);
      persistPrefs(updated);
    },
    [prefs, persistPrefs]
  );

  const handleRemoveDevice = useCallback(async () => {
    if (!registeredToken) return;
    Alert.alert(
      "Remove This Device",
      "You will no longer receive push notifications on this device.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Remove",
          style: "destructive",
          onPress: async () => {
            setRemovingDevice(true);
            try {
              await unregisterPushToken(registeredToken);
              await deleteFromStore(TOKEN_KEY);
              setRegisteredToken(null);
            } catch {
              Alert.alert("Error", "Could not remove this device. Please try again.");
            } finally {
              setRemovingDevice(false);
            }
          },
        },
      ]
    );
  }, [registeredToken]);

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: theme.colors.surface0 }}>
        <ScreenHeader title="Push Notifications" />
        <ActivityIndicator color={theme.colors.brand} />
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.scroll, { backgroundColor: theme.colors.surface0 }]}
      contentContainerStyle={{ paddingBottom: 24 }}
    >
      <ScreenHeader title="Push Notifications" />

      {/* Master toggle */}
      <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
        <View style={styles.masterRow}>
          <View style={styles.masterContent}>
            <Text style={[styles.masterLabel, { color: theme.colors.text }]}>
              Allow Push Notifications
            </Text>
            <Text style={[styles.masterDesc, { color: theme.colors.textMuted }]}>
              Receive alerts about orders, deals, and more
            </Text>
          </View>
          <Switch
            value={prefs.enabled}
            onValueChange={setEnabled}
            trackColor={{ false: theme.colors.border, true: theme.colors.brand }}
            thumbColor={theme.colors.surface1}
          />
        </View>
      </View>

      {/* Info box shown when notifications disabled */}
      {!prefs.enabled && (
        <View
          style={[
            styles.infoBox,
            { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
          ]}
        >
          <Text style={[styles.infoText, { color: theme.colors.textMuted }]}>
            Push notifications are disabled. Enable them above to stay informed about
            your orders, flash sales, and more.
            {"\n\n"}
            You may also need to allow notifications in your device settings for ZOZI.
          </Text>
        </View>
      )}

      {/* Category toggles (only when enabled) */}
      {prefs.enabled && (
        <>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>
              Notification Categories
            </Text>
          </View>

          <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
            {CATEGORIES.map((cat, idx) => (
              <View
                key={cat.key}
                style={[
                  styles.row,
                  { borderBottomColor: theme.colors.border },
                  idx === CATEGORIES.length - 1 && styles.rowLast,
                ]}
              >
                <View style={styles.rowContent}>
                  <Text style={[styles.rowLabel, { color: theme.colors.text }]}>
                    {cat.label}
                  </Text>
                  <Text style={[styles.rowDesc, { color: theme.colors.textMuted }]}>
                    {cat.description}
                  </Text>
                </View>
                <Switch
                  value={prefs[cat.key]}
                  onValueChange={(val) => setCategory(cat.key, val)}
                  trackColor={{ false: theme.colors.border, true: theme.colors.brand }}
                  thumbColor={theme.colors.surface1}
                />
              </View>
            ))}
          </View>
        </>
      )}

      {/* Registered device */}
      {registeredToken && (
        <>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>
              This Device
            </Text>
          </View>
          <View style={[styles.deviceSection, { backgroundColor: theme.colors.surface1 }]}>
            <View style={styles.deviceRow}>
              <Text style={[styles.deviceLabel, { color: theme.colors.text }]}>
                Registered for push notifications
              </Text>
              <TouchableOpacity
                style={[styles.removeBtn, { borderColor: theme.colors.danger }]}
                onPress={handleRemoveDevice}
                disabled={removingDevice}
              >
                {removingDevice ? (
                  <ActivityIndicator size="small" color={theme.colors.danger} />
                ) : (
                  <Text style={[styles.removeBtnText, { color: theme.colors.danger }]}>
                    Remove
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </>
      )}

      {/* Saving indicator */}
      {saving && (
        <View style={{ alignItems: "center", paddingTop: 8 }}>
          <ActivityIndicator size="small" color={theme.colors.textMuted} />
        </View>
      )}

      <View style={styles.bottomPad} />
    </ScrollView>
  );
}
