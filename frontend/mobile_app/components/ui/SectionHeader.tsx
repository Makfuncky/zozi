import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";

interface SectionHeaderProps {
  title: string;
  icon?: React.ComponentProps<typeof Ionicons>["name"];
  accent?: string;
  onSeeAll?: () => void;
  seeAllLabel?: string;
  testID?: string;
}

/**
 * Consistent, reusable section header used across home and tab screens.
 * Renders an optional tinted icon chip + bold display title + optional "See all" affordance.
 */
export function SectionHeader({
  title,
  icon,
  accent,
  onSeeAll,
  seeAllLabel = "See all",
  testID,
}: SectionHeaderProps) {
  const { theme } = useThemeStore();
  const accentColor = accent ?? theme.colors.brand;
  const styles = makeLocalStyles(theme);

  return (
    <View style={styles.header} testID={testID}>
      <View style={styles.left}>
        {icon ? (
          <View style={[styles.iconBg, { backgroundColor: accentColor + "18" }]}>
            <Ionicons name={icon} size={16} color={accentColor} />
          </View>
        ) : null}
        <Text style={[styles.title, { fontFamily: theme.fontFamily.heading }]}>{title}</Text>
      </View>
      {onSeeAll ? (
        <TouchableOpacity
          onPress={onSeeAll}
          activeOpacity={0.7}
          style={[styles.seeAll, { borderColor: theme.colors.border }]}
          accessibilityRole="button"
          accessibilityLabel={seeAllLabel}
        >
          <Text style={[styles.seeAllText, { color: theme.colors.brand }]}>{seeAllLabel}</Text>
          <Ionicons name="chevron-forward" size={12} color={theme.colors.brand} />
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

function makeLocalStyles(theme: AppTheme) {
  return StyleSheet.create({
    header: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      paddingHorizontal: 16,
      marginBottom: 12,
    },
    left: {
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
    },
    iconBg: {
      width: 28,
      height: 28,
      borderRadius: 8,
      alignItems: "center",
      justifyContent: "center",
    },
    title: {
      color: theme.colors.text,
      fontSize: 17,
      fontWeight: "800",
      letterSpacing: -0.3,
    },
    seeAll: {
      flexDirection: "row",
      alignItems: "center",
      gap: 2,
      paddingHorizontal: 10,
      paddingVertical: 5,
      borderRadius: 16,
      borderWidth: 1,
    },
    seeAllText: {
      fontSize: 12,
      fontWeight: "700",
    },
  });
}

export default SectionHeader;
