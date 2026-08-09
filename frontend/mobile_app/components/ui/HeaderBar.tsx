import React from "react";
import { View, TouchableOpacity, Text, StyleSheet, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { useRouter } from "expo-router";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  /* fallback to solid brand */
}

interface HeaderBarProps {
  /** label for the left slider button (accessibility) */
  leftLabel?: string;
  /** label for the right slider button (accessibility) */
  rightLabel?: string;
  onLeftPress?: () => void;
  onRightPress?: () => void;
  /** when true, render the logo as plain text (no navigation) */
  logoOnly?: boolean;
}

/**
 * Branded ZOZI header bar — mobile mirror of the HTML sample.
 * Diagonal lime gradient (#6ae022 → #45b31a), a decorative frosted gloss
 * orb in the top-right, a green glow shadow, a slider menu button on each
 * side, and the ZOZI wordmark centered. The lime region is intentionally
 * tall so it flows down behind the web_app Search+Filter bar and overlaps
 * the top half of the banner below (sample's .banner { margin:-72px }).
 * The search itself lives in ProductSearchFilterBar, not here.
 */
function HeaderBar({
  leftLabel = "Open menu",
  rightLabel = "Account",
  onLeftPress,
  onRightPress,
  logoOnly = false,
}: HeaderBarProps) {
  const { theme } = useThemeStore();
  const router = useRouter();

  const handleLeft = () => {
    if (onLeftPress) onLeftPress();
  };
  const handleRight = () => {
    if (onRightPress) onRightPress();
  };

  const iconColor = theme.colors.onBrand;
  const btnBg = "rgba(255,255,255,0.20)";

  const logo = (
    <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8 }}>
      <View
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          backgroundColor: btnBg,
          borderWidth: 1,
          borderColor: "rgba(255,255,255,0.45)",
          alignItems: "center",
          justifyContent: "center",
          ...Platform.select({
            web: { backdropFilter: "blur(10px)" },
            default: { shadowColor: "#000", shadowOpacity: 0.18, shadowRadius: 6, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
          }),
        }}
      >
        <Ionicons name="leaf" size={18} color={iconColor} />
      </View>
      <Text
        style={{
          color: iconColor,
          fontWeight: "800",
          fontSize: 24,
          letterSpacing: -0.5,
          textShadowColor: "rgba(0,0,0,0.1)",
          textShadowOffset: { width: 0, height: 2 },
          textShadowRadius: 4,
        }}
      >
        ZOZI
      </Text>
    </View>
  );

  const sideBtn = (icon: any, onPress: () => void, label: string, align: "left" | "right") => (
    <TouchableOpacity
      onPress={onPress}
      accessibilityLabel={label}
      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      style={[
        styles.sliderBtn,
        {
          backgroundColor: btnBg,
          borderWidth: 1,
          borderColor: "rgba(255,255,255,0.45)",
          transform: align === "left" ? [{ rotate: "180deg" }] : [],
        },
      ]}
    >
      <Ionicons name={icon} size={20} color={iconColor} />
    </TouchableOpacity>
  );

  const inner = (
    <View style={styles.bar}>
      {logoOnly ? (
        <View style={styles.sideSpacer} />
      ) : (
        sideBtn("menu-outline", handleLeft, leftLabel, "left")
      )}

      <View style={styles.logoWrap}>{logo}</View>

      {logoOnly ? (
        <View style={styles.sideSpacer} />
      ) : (
        sideBtn("person-circle-outline", handleRight, rightLabel, "right")
      )}
    </View>
  );

  const gradientProps = {
    colors: theme.gradients.header as [string, string, string],
    start: { x: 0, y: 0 },
    end: { x: 1, y: 1 },
    style: styles.gradient,
  };

  if (LinearGradient) {
    return (
      <LinearGradient {...gradientProps}>
        <View style={styles.orb} pointerEvents="none" />
        {inner}
      </LinearGradient>
    );
  }

  return (
    <View style={[styles.gradient, { backgroundColor: theme.colors.brand }]}>
      <View style={styles.orb} pointerEvents="none" />
      {inner}
    </View>
  );
}

const styles = StyleSheet.create({
  gradient: {
    width: "100%",
    paddingTop: 8,
    // Tall lime region so the web_app Search+Filter bar sits inside the head section.
    paddingBottom: 100,
    overflow: "hidden",
    ...Platform.select({
      web: {
        backdropFilter: "blur(14px) saturate(150%)",
        boxShadow: "0 8px 24px rgba(106,224,34,0.40)",
      },
      default: {
        shadowColor: "#6ae022",
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.4,
        shadowRadius: 24,
        elevation: 10,
      },
    }),
  },
  // Decorative frosted orb (mirrors the sample's ::before circle)
  orb: {
    position: "absolute",
    top: -60,
    right: -40,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: "rgba(255,255,255,0.10)",
  },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 18,
    paddingVertical: 14,
  },
  logoWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  sideSpacer: {
    width: 36,
    height: 36,
  },
  sliderBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    ...Platform.select({
      web: { backdropFilter: "blur(10px)", boxShadow: "0 2px 8px rgba(0,0,0,0.12)" },
      default: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.18,
        shadowRadius: 6,
        elevation: 4,
      },
    }),
  },
});

export default React.memo(HeaderBar);
export { HeaderBar };
