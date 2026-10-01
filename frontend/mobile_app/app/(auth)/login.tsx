import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  TouchableOpacity,
} from "react-native";
import { useRouter, Stack } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { socialSignIn, SocialSignInError, type SocialProvider } from "@/lib/socialAuth";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme, glassWebFilter } from "@/theme";
import { Input } from "@/components/ui/Input";
import { GradientButton } from "@/components/ui/GradientButton";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    flexGrow: 1,
    justifyContent: "center",
  },
  wrap: {
    width: "100%",
    maxWidth: 440,
    alignSelf: "center",
    paddingVertical: theme.spacing.xl,
    paddingHorizontal: theme.spacing.lg,
    gap: theme.spacing.lg,
  },
  header: {
    alignItems: "center",
    gap: 6,
  },
  brandLockup: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  brandBadge: {
    width: 40,
    height: 40,
    borderRadius: 11,
    backgroundColor: theme.colors.brand + "22",
    borderWidth: 1,
    borderColor: theme.colors.brand + "55",
    alignItems: "center",
    justifyContent: "center",
  },
  brandWordmark: {
    color: theme.colors.text,
    fontWeight: "800",
    fontSize: 30,
    letterSpacing: -0.5,
  },
  tagline: {
    color: theme.colors.textMuted,
    fontSize: theme.fontSize.sm,
    textAlign: "center",
  },
  welcome: {
    fontSize: theme.fontSize.xl,
    fontWeight: "800",
    textAlign: "center",
  },
  sub: {
    color: theme.colors.textMuted,
    fontSize: theme.fontSize.sm,
    textAlign: "center",
    marginTop: 2,
  },
  card: {
    backgroundColor: theme.colors.glass.panel,
    borderColor: theme.colors.glass.border,
    borderWidth: 1,
    borderRadius: theme.radius.xl,
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
    ...glassWebFilter,
    ...Platform.select({
      web: {
        boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
      },
      default: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 14 },
        shadowOpacity: 0.35,
        shadowRadius: 28,
        elevation: 12,
      },
    }),
  },
  errorBox: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
  },
  verifyLink: {
    marginTop: 4,
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  rememberRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  rememberLabel: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  forgot: {
    paddingVertical: 2,
  },
  dividerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginVertical: 2,
  },
  dividerLine: {
    flex: 1,
    height: 1,
  },
  dividerText: {
    color: theme.colors.textMuted,
    fontSize: theme.fontSize.xs,
  },
  socialRow: {
    flexDirection: "row",
    gap: 10,
  },
  socialBtn: {
    flex: 1,
    flexDirection: "row",
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 14,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  socialLabel: {
    fontWeight: "700",
    fontSize: theme.fontSize.xs,
  },
  socialHint: {
    textAlign: "center",
    fontSize: theme.fontSize.xs,
    color: theme.colors.textMuted,
    marginTop: 2,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 4,
    marginTop: 2,
  },
  links: {
    alignItems: "center",
    gap: 10,
    marginTop: 4,
  },
  linkRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 4,
  },
});

export default function LoginScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { login: storeLogin } = useAuthStore();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [socialError, setSocialError] = useState<string | null>(null);

  function redirectForRole(role?: string) {
    if (role === "supplier") {
      router.replace("/supplier/dashboard" as never);
    } else if (role === "logistics_partner") {
      router.replace("/logistics-partner/dashboard" as never);
    } else if (role === "admin" || role === "sub_admin") {
      router.replace("/admin/dashboard" as never);
    } else {
      router.replace("/(tabs)/products" as never);
    }
  }

  async function handleLogin() {
    if (!identifier.trim() || !password) {
      setError("Email or username and password are required");
      return;
    }
    setLoading(true);
    setError(null);
    setSocialError(null);
    try {
      const user = await storeLogin(identifier.trim(), password, remember);
      redirectForRole(user.role as string);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Invalid email/username or password";
      if (/Failed to fetch|Network request failed|ECONNREFUSED/.test(msg)) {
        setError("Could not connect to the server. Please check backend service or API URL.");
      } else if (msg.includes("422") || msg.includes("401") || msg.includes("400")) {
        setError("Invalid email/username or password");
      } else if (/verif/i.test(msg)) {
        setError(msg);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  const providerCards: {
    key: SocialProvider;
    label: string;
    icon: React.ComponentProps<typeof Ionicons>["name"];
    color: string;
  }[] = [
    { key: "google", label: "Google", icon: "logo-google", color: "#DB4437" },
    { key: "facebook", label: "Facebook", icon: "logo-facebook", color: "#1877F2" },
    { key: "apple", label: "Apple", icon: "logo-apple", color: "#FFFFFF" },
  ];

  const handleSocialLogin = async (provider: (typeof providerCards)[number]) => {
    setLoading(true);
    setError(null);
    setSocialError(null);
    try {
      const res = await socialSignIn(provider.key);
      redirectForRole(res.user.role as string);
    } catch (err: unknown) {
      // Social sign-in is optional — never block the email flow.
      const message =
        err instanceof SocialSignInError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Social sign-in failed";
      setSocialError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <Stack.Screen options={{ title: "Sign In", headerShown: false }} />
      <ScrollView
        testID="auth-login-screen"
        contentContainerStyle={[s.container, styles.scroll, { backgroundColor: theme.colors.surface0 }]}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.wrap}>
          {/* Logo / Brand — single branded lockup (icon + wordmark) */}
          <View style={styles.header}>
            <View style={styles.brandLockup}>
              <View style={styles.brandBadge}>
                <Ionicons name="leaf" size={22} color={theme.colors.onBrand} />
              </View>
              <Text style={styles.brandWordmark}>ZOZI</Text>
            </View>
            <Text style={[s.textMuted, styles.tagline]}>Trust Delivered</Text>
          </View>

          {/* Welcome */}
          <View>
            <Text style={[s.text, styles.welcome]}>Welcome back</Text>
            <Text style={[s.textMuted, styles.sub]}>
              Sign in to continue your shopping experience
            </Text>
          </View>

          {/* Form */}
          <View style={styles.card}>
            {error && (
              <View
                testID="auth-login-error"
                style={[styles.errorBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}
              >
                <Ionicons name="alert-circle" size={18} color={theme.colors.danger} style={{ marginTop: 1 }} />
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.base }}>
                    {error}
                  </Text>
                  {/verif/i.test(error) && (
                    <TouchableOpacity
                      onPress={() => router.push("/(auth)/forgot-password")}
                      style={styles.verifyLink}
                      testID="auth-login-resend-verify"
                    >
                      <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                        Resend verification email
                      </Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            )}

            <Input
              label="Email or Username"
              placeholder="you@example.com or your username"
              testID="auth-login-identifier"
              value={identifier}
              onChangeText={(t) => {
                setIdentifier(t);
                setError(null);
              }}
              autoCapitalize="none"
              autoComplete="username"
            />
            <Input
              label="Password"
              placeholder="••••••••"
              testID="auth-login-password"
              value={password}
              onChangeText={(t) => {
                setPassword(t);
                setError(null);
              }}
              isPassword
            />

            <View style={styles.rowBetween}>
              <TouchableOpacity
                style={styles.rememberRow}
                onPress={() => setRemember((v) => !v)}
                activeOpacity={0.7}
                testID="auth-login-remember"
              >
                <View
                  style={[
                    styles.checkbox,
                    {
                      borderColor: theme.colors.border,
                      backgroundColor: remember ? theme.colors.brand : "transparent",
                    },
                  ]}
                >
                  {remember && <Ionicons name="checkmark" size={14} color="#fff" />}
                </View>
                <Text style={[s.text, styles.rememberLabel]}>Remember me</Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() => router.push("/(auth)/forgot-password")}
                style={styles.forgot}
                testID="auth-login-forgot-password"
              >
                <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm }}>
                  Forgot password?
                </Text>
              </TouchableOpacity>
            </View>

            <GradientButton
              label={loading ? "Signing in..." : "Sign In"}
              onPress={handleLogin}
              loading={loading}
              testID="auth-login-submit"
              style={{ marginTop: theme.spacing.xs }}
            />

            {/* Divider */}
            <View style={styles.dividerRow}>
              <View style={[styles.dividerLine, { backgroundColor: theme.colors.glass.border }]} />
              <Text style={[s.textMuted, styles.dividerText]}>or continue with</Text>
              <View style={[styles.dividerLine, { backgroundColor: theme.colors.glass.border }]} />
            </View>

            {/* Social sign-in (always available — graceful fallback if unconfigured) */}
            <View style={styles.socialRow}>
              {providerCards.map((provider) => (
                <TouchableOpacity
                  key={provider.key}
                  testID={`auth-login-${provider.key}-btn`}
                  onPress={() => handleSocialLogin(provider)}
                  disabled={loading}
                  activeOpacity={0.8}
                  style={[
                    styles.socialBtn,
                    {
                  borderColor: theme.colors.glass.border,
                  backgroundColor: theme.colors.surface2,
                      opacity: loading ? 0.6 : 1,
                    },
                  ]}
                >
                  <Ionicons
                    name={provider.icon}
                    size={20}
                    color={provider.key === "apple" ? theme.colors.text : provider.color}
                  />
                  <Text style={[s.text, styles.socialLabel]}>{provider.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {socialError && (
              <Text style={[s.textMuted, styles.socialHint]} testID="auth-login-social-error">
                {socialError}
              </Text>
            )}
          </View>

          {/* Register */}
          <View style={styles.footer}>
            <Text style={[s.textMuted]}>Don&apos;t have an account? </Text>
            <TouchableOpacity onPress={() => router.push("/(auth)/register")} testID="auth-login-register">
              <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>Register</Text>
            </TouchableOpacity>
          </View>

          {/* Seller / partner links */}
          <View style={styles.links}>
            <TouchableOpacity
              style={styles.linkRow}
              onPress={() => router.push("/supplier/login" as never)}
              testID="auth-login-supplier"
            >
              <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>
                Are you a supplier? <Text style={{ color: theme.colors.brand }}>Sign in here</Text>
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.linkRow}
              onPress={() => router.push("/logistics-partner/login" as never)}
              testID="auth-login-logistics"
            >
              <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>
                Logistics partner? <Text style={{ color: theme.colors.brand }}>Sign in here</Text>
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
