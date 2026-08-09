import React, { useState, useEffect } from "react";
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Switch, ActivityIndicator } from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { getNotificationPreferences, updateNotificationPreferences, NotificationPreferences } from "@/lib/api";
import ScreenHeader from "@/components/ui/ScreenHeader";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surface0,
  },
  scroll: {
    flex: 1,
    padding: theme.spacing.lg,
  },
  section: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.md,
  },
  sectionTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: "700",
    marginBottom: theme.spacing.md,
    color: theme.colors.text,
  },
  settingRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 1,
  },
  settingRowLast: {
    borderBottomWidth: 0,
  },
  settingLabel: {
    flex: 1,
    marginRight: theme.spacing.md,
  },
  settingTitle: {
    fontSize: theme.fontSize.base,
    fontWeight: "600",
    color: theme.colors.text,
  },
  settingDescription: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textMuted,
    marginTop: 2,
  },
  footer: {
    padding: theme.spacing.lg,
    paddingTop: 0,
  },
  saveBtn: {
    backgroundColor: theme.colors.brand,
    borderRadius: theme.radius.xl,
    paddingVertical: theme.spacing.md,
    alignItems: "center",
  },
  saveBtnText: {
    color: theme.colors.onBrand,
    fontSize: theme.fontSize.base,
    fontWeight: "700",
  },
});

const SETTING_CONFIGS = [
  {
    key: "order_status" as const,
    title: "Order Status Updates",
    description: "Receive notifications about your order progress, shipping, and delivery.",
  },
  {
    key: "promotions" as const,
    title: "Promotions & Deals",
    description: "Be the first to know about sales, discounts, and special offers.",
  },
  {
    key: "newsletter" as const,
    title: "Newsletter",
    description: "Weekly updates, new products, and exclusive offers.",
  },
  {
    key: "ai_assistant" as const,
    title: "AI Assistant",
    description: "Get helpful suggestions and answers from our shopping assistant.",
  },
];

export default function NotificationPreferencesScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    order_status: true,
    promotions: true,
    newsletter: false,
    ai_assistant: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const data = await getNotificationPreferences();
        setPreferences(data);
      } catch (err) {
        console.warn("Failed to load preferences", err);
      } finally {
        setLoading(false);
      }
    };
    loadPreferences();
  }, []);

  const handleToggle = (key: keyof NotificationPreferences) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!hasChanges) return;
    setSaving(true);
    try {
      await updateNotificationPreferences(preferences);
      setHasChanges(false);
    } catch (err) {
      console.warn("Failed to save preferences", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: "center", alignItems: "center" }]}>
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScreenHeader title="Notification Preferences" rightIcon="checkmark" onRightPress={handleSave} />

      <ScrollView style={styles.scroll}>
        <Text style={[s.textMuted, { marginBottom: theme.spacing.lg }]}>
          Choose which notifications you'd like to receive. You can change these at any time.
        </Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notification Types</Text>
          {SETTING_CONFIGS.map((config, index) => (
            <View
              key={config.key}
              style={[
                styles.settingRow,
                index === SETTING_CONFIGS.length - 1 && styles.settingRowLast,
                { borderBottomColor: theme.colors.border },
              ]}
            >
              <View style={styles.settingLabel}>
                <Text style={styles.settingTitle}>{config.title}</Text>
                <Text style={styles.settingDescription}>{config.description}</Text>
              </View>
              <Switch
                value={preferences[config.key]}
                onValueChange={() => handleToggle(config.key)}
                trackColor={{ false: theme.colors.surface2, true: theme.colors.brand + "80" }}
                thumbColor={preferences[config.key] ? theme.colors.brand : theme.colors.textMuted}
              />
            </View>
          ))}
        </View>

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.saveBtn, { opacity: hasChanges || saving ? 1 : 0.6 }]}
            onPress={handleSave}
            disabled={!hasChanges || saving}
          >
            <Text style={styles.saveBtnText}>Save Preferences</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}