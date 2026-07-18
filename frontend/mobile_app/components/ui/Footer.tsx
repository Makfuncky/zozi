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

interface FooterLink {
  key: string;
  label: string;
  icon: React.ComponentProps<typeof Ionicons>["name"];
  route: string;
  /** primary variant = white pill with lime text (mirrors .footer-btn.primary) */
  primary?: boolean;
}

const FOOTER_LINKS: FooterLink[] = [
  { key: "shop", label: "Shop", icon: "grid-outline", route: "/(tabs)/products", primary: true },
  { key: "orders", label: "Orders", icon: "receipt-outline", route: "/(tabs)/orders" },
  { key: "wishlist", label: "Wishlist", icon: "heart-outline", route: "/wishlist" },
  { key: "cart", label: "Cart", icon: "bag-outline", route: "/(tabs)/cart" },
  { key: "chat", label: "AI Chat", icon: "chatbubble-ellipses-outline", route: "/chatbot" },
];

interface FooterProps {
  /** extra links appended after the defaults (e.g. account/profile) */
  extraLinks?: FooterLink[];
  onNavigate?: (route: string) => void;
}

/**
 * Branded ZOZI footer — mobile mirror of the HTML sample.
 * Diagonal lime gradient with a decorative frosted orb in the bottom-left,
 * glass pill buttons (rgba(255,255,255,0.20)) plus a primary white variant.
 * Deliberately excludes the Search and Home buttons (Home no longer exists;
 * Search lives in the header bar).
 */
export default function Footer({ extraLinks = [], onNavigate }: FooterProps) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const links = [...FOOTER_LINKS, ...extraLinks];

  const press = (route: string) => {
    if (onNavigate) onNavigate(route);
    else router.push(route as never);
  };

  const inner = (
    <View style={styles.inner}>
      <View style={styles.row}>
        {links.map((l) => {
          const isPrimary = !!l.primary;
          const btn = (
            <View style={styles.btnWrap}>
              <View
                style={[
                  styles.btnGlass,
                  isPrimary
                    ? { backgroundColor: "#ffffff" }
                    : { backgroundColor: "rgba(255,255,255,0.20)", borderColor: "rgba(255,255,255,0.45)" },
                ]}
              >
                <Ionicons name={l.icon} size={18} color={isPrimary ? theme.colors.brand : "#ffffff"} />
                <Text style={[styles.btnText, { color: isPrimary ? theme.colors.brand : "#ffffff" }]}>{l.label}</Text>
              </View>
              {/* glossy top sheen */}
              <View
                style={[
                  styles.gloss,
                  { backgroundColor: isPrimary ? "rgba(0,0,0,0.04)" : "rgba(255,255,255,0.22)" },
                ]}
                pointerEvents="none"
              />
            </View>
          );
          return (
            <TouchableOpacity
              key={l.key}
              onPress={() => press(l.route)}
              accessibilityLabel={l.label}
              activeOpacity={0.82}
              style={styles.touch}
            >
              {btn}
            </TouchableOpacity>
          );
        })}
      </View>
      <Text style={[styles.copy, { color: "#1A5204" }]}>© ZOZI — Shop smart, live fresh.</Text>
    </View>
  );

  const gradientProps = {
    colors: theme.gradients.footer as [string, string, string],
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
    marginTop: 16,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    overflow: "hidden",
    ...Platform.select({
      web: {
        backdropFilter: "blur(14px) saturate(150%)",
        boxShadow: "0 -4px 20px rgba(106,224,34,0.30)",
      },
      default: {
        shadowColor: "#6ae022",
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.3,
        shadowRadius: 20,
        elevation: 10,
      },
    }),
  },
  // Decorative frosted orb (mirrors the sample's ::before circle)
  orb: {
    position: "absolute",
    bottom: -60,
    left: -40,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: "rgba(255,255,255,0.10)",
  },
  inner: {
    paddingVertical: 20,
    paddingHorizontal: 16,
    gap: 16,
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 8,
  },
  touch: {
    borderRadius: 14,
  },
  btnWrap: {
    borderRadius: 14,
    overflow: "hidden",
  },
  btnGlass: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    height: 48,
    paddingHorizontal: 16,
    borderRadius: 14,
    borderWidth: 1,
    ...Platform.select({
      web: { backdropFilter: "blur(10px)", boxShadow: "0 2px 8px rgba(0,0,0,0.10)" },
      default: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
        elevation: 3,
      },
    }),
  },
  gloss: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: "44%",
    borderTopLeftRadius: 14,
    borderTopRightRadius: 14,
  },
  btnText: {
    fontWeight: "600",
    fontSize: 13,
  },
  copy: {
    textAlign: "center",
    fontSize: 11,
    fontWeight: "600",
  },
});

export { Footer };
