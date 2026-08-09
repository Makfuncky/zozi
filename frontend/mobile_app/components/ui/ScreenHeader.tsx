import React from "react";
import { View, TouchableOpacity, Text, StyleSheet, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter, useNavigation } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  /* fallback to solid brand */
}

interface ScreenHeaderProps {
  title: string;
  /** Show a back button (uses router.back). Defaults to true. */
  showBack?: boolean;
  /** Optional right-side icon button. */
  rightIcon?: React.ComponentProps<typeof Ionicons>["name"];
  onRightPress?: () => void;
  /** Accessibility label for the right button. */
  rightLabel?: string;
  subtitle?: string;
}

/**
 * Branded lime-gradient screen header used by standalone (Stack) screens so every
 * screen in the app shares the same ZOZI header as the tab bar. Renders a back
 * chevron, a centered wordmark-style title, and an optional right action.
 */
function ScreenHeader({
  title,
  showBack = true,
  rightIcon,
  onRightPress,
  rightLabel,
  subtitle,
}: ScreenHeaderProps) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const navigation = useNavigation();

  const iconColor = theme.colors.onBrand;
  const btnBg = "rgba(255,255,255,0.20)";

  const inner = (
    <View style={styles.bar}>
      <View style={styles.side}>
        {showBack ? (
          <TouchableOpacity
            onPress={() => {
              try {
                if (navigation.canGoBack()) router.back();
                else router.replace("/(tabs)/products" as never);
              } catch {
                router.replace("/(tabs)/products" as never);
              }
            }}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            style={[styles.sliderBtn, { backgroundColor: btnBg, borderColor: "rgba(255,255,255,0.45)" }]}
            accessibilityLabel="Go back"
          >
            <Ionicons name="chevron-back" size={22} color={iconColor} />
          </TouchableOpacity>
        ) : null}
      </View>

      <View style={styles.titleWrap}>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        {subtitle ? <Text style={styles.subtitle} numberOfLines={1}>{subtitle}</Text> : null}
      </View>

      <View style={styles.side}>
        {rightIcon ? (
          <TouchableOpacity
            onPress={onRightPress}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            style={[styles.sliderBtn, { backgroundColor: btnBg, borderColor: "rgba(255,255,255,0.45)" }]}
            accessibilityLabel={rightLabel ?? "Action"}
          >
            <Ionicons name={rightIcon} size={20} color={iconColor} />
          </TouchableOpacity>
        ) : null}
      </View>
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
    paddingBottom: 14,
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
    paddingHorizontal: 14,
    paddingTop: 6,
  },
  side: {
    width: 44,
    alignItems: "flex-start",
  },
  titleWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 20,
    letterSpacing: -0.3,
    textShadowColor: "rgba(0,0,0,0.10)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  subtitle: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 11,
    fontWeight: "600",
    marginTop: 1,
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

export default React.memo(ScreenHeader);
export { ScreenHeader };
