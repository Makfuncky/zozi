import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, Switch, StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from "react-native";

import { useRouter } from "expo-router";
import AppHeader from "@/components/ui/AppHeader";
import { getNewsletterPreferences, subscribeNewsletter, unsubscribeNewsletter } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    padding: 20,
    gap: 20,
    paddingBottom: 40,
  },
  header: {
    gap: 10,
    paddingVertical: theme.spacing.md,
    alignItems: "center",
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    padding: theme.spacing.md,
    borderRadius: 14,
    borderWidth: 1,
    gap: 12,
  },
  infoBox: {
    padding: 14,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
  },
});
// Button not used in this screen

export default function NewsletterScreen() {
  const router = useRouter();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user } = useAuthStore();

  const [subscribed, setSubscribed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingPreference, setLoadingPreference] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingPreference(true);
    getNewsletterPreferences(user?.email)
      .then((data) => {
        if (!cancelled) setSubscribed(Boolean(data?.is_active));
      })
      .catch(() => {
        if (!cancelled) setSubscribed(false);
      })
      .finally(() => {
        if (!cancelled) setLoadingPreference(false);
      });

    return () => {
      cancelled = true;
    };
  }, [user?.email]);

  async function handleToggle(value: boolean) {
    setSaving(true);
    try {
      if (value) {
        await subscribeNewsletter(user?.email ?? "");
        setSubscribed(true);
        Alert.alert("Subscribed!", "You'll receive our latest offers and updates.");
      } else {
        await unsubscribeNewsletter(user?.email ?? "");
        setSubscribed(false);
        Alert.alert("Unsubscribed", "You've been removed from our newsletter list.");
      }
    } catch (err: unknown) {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Could not update preference"
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <AppHeader showSearch={false} />
      <ScrollView
        contentContainerStyle={[styles.scroll, { backgroundColor: theme.colors.surface0 }]}
      >
        {/* Header illustration */}
        <View style={styles.header}>
          <Text style={{ fontSize: theme.fontSize["3xl"], textAlign: "center" }}>📧</Text>
          <Text style={[s.title, { textAlign: "center" }]}>Newsletter</Text>
          <Text style={[s.textMuted, { textAlign: "center" }]}>
            Stay up to date with ZOZI offers, new products, and exclusive deals.
          </Text>
        </View>

        {/* Toggle card */}
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={{ flex: 1, gap: theme.spacing.xs }}>
            <Text style={[s.text, { fontWeight: "600" }]}>Marketing emails</Text>
            <Text style={s.textMuted}>
              Receive promotions, deals, and product highlights
            </Text>
          </View>
          {saving || loadingPreference ? (
            <ActivityIndicator color={theme.colors.brand} />
          ) : (
            <Switch
              value={subscribed}
              onValueChange={handleToggle}
              trackColor={{ false: theme.colors.border, true: theme.colors.brand }}
              thumbColor={theme.colors.onBrand}
            />
          )}
        </View>

        {/* Info */}
        <View style={[styles.infoBox, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={{ flexDirection: "row", gap: 6, alignItems: "flex-start" }}>
            <Ionicons name="lock-closed" size={14} color={theme.colors.textMuted} style={{ marginTop: 3 }} />
            <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, lineHeight: 20, flex: 1 }]}>
              We respect your privacy. You can unsubscribe at any time. We will never share your email with third parties.
            </Text>
          </View>
        </View>

        {/* Email display */}
        {user?.email && (
          <Text style={[s.textMuted, { textAlign: "center", fontSize: theme.fontSize.sm }]}>
            Preferences for {user.email}
          </Text>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
