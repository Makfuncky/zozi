/**
 * /r/[code] — Referral deep-link landing page.
 *
 * On web this would be a server-rendered redirect page. On mobile,
 * Expo Router handles the route and we auto-navigate to registration
 * with the referral code pre-filled.
 *
 * If the user is already logged in, we navigate to the referrals screen directly.
 */
import React, { useEffect } from "react";
import { View, Text, ActivityIndicator, StyleSheet, TouchableOpacity } from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { useAuthStore } from "@/lib/authStore";

export default function ReferralLandingScreen(): React.ReactElement {
  const { code } = useLocalSearchParams<{ code: string }>();
  const router = useRouter();
  const theme = useThemeStore((s) => s.theme);
  const isLoggedIn = useAuthStore((s) => Boolean(s.user));
  const authLoading = useAuthStore((s) => s.isLoading);

  useEffect(() => {
    if (!code || authLoading) return;

    const timer = setTimeout(() => {
      if (isLoggedIn) {
        // Already authenticated — bring them to the referrals page
        router.replace("/referrals" as never);
      } else {
        // Navigate to register with code pre-filled
        router.replace({ pathname: "/(auth)/register", params: { ref: code } } as never);
      }
    }, 1800);

    return () => clearTimeout(timer);
  }, [code, isLoggedIn, authLoading, router]);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surface0 }]}>
      <Stack.Screen options={{ headerShown: false }} />

      {/* Brand card */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        <Text style={[styles.emoji]}>🎁</Text>
        <Text style={[styles.headline, { color: theme.colors.text }]}>You're Invited!</Text>
        <Text style={[styles.sub, { color: theme.colors.textMuted }]}>
          Your friend shared a referral code:
        </Text>
        <View style={[styles.codeBox, { backgroundColor: theme.colors.brand + "18", borderColor: theme.colors.brand }]}>
          <Text style={[styles.code, { color: theme.colors.brand }]}>{code ?? "—"}</Text>
        </View>
        <Text style={[styles.sub, { color: theme.colors.textMuted }]}>
          Sign up to claim your reward and start shopping!
        </Text>
      </View>

      <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
        <ActivityIndicator color={theme.colors.brand} />
        <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>
          {isLoggedIn ? "Redirecting to referrals…" : "Taking you to sign up…"}
        </Text>
      </View>

      <TouchableOpacity
        onPress={() => {
          if (isLoggedIn) {
            router.replace("/referrals" as never);
          } else {
            router.replace({ pathname: "/(auth)/register", params: { ref: code } } as never);
          }
        }}
        style={[styles.btn, { backgroundColor: theme.colors.brand }]}
      >
        <Text style={{ color: theme.colors.onBrand, fontWeight: "800", fontSize: 15 }}>
          {isLoggedIn ? "Go to Referrals" : "Sign Up & Claim Reward"}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 28,
    gap: 24,
  },
  card: {
    width: "100%",
    borderRadius: 22,
    borderWidth: 1,
    padding: 28,
    alignItems: "center",
    gap: 14,
  },
  emoji: { fontSize: 56, lineHeight: 64 },
  headline: { fontSize: 26, fontWeight: "900", textAlign: "center" },
  sub: { fontSize: 14, textAlign: "center", lineHeight: 20 },
  codeBox: {
    borderRadius: 14,
    borderWidth: 1.5,
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  code: { fontSize: 22, fontWeight: "900", letterSpacing: 3 },
  btn: {
    width: "100%",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
  },
});
