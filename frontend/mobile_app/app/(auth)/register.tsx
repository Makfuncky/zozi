import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useRouter, Stack, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import Logo from "@/components/Logo";
import { Input } from "@/components/ui/Input";
import { GradientButton } from "@/components/ui/GradientButton";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    flexGrow: 1,
    padding: theme.spacing.lg,
    justifyContent: "center",
    gap: theme.spacing.xl,
  },
  header: {
    alignItems: "center",
    gap: 8,
  },
  logoCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  brand: {
    fontSize: theme.fontSize["2xl"],
    fontWeight: "800",
    letterSpacing: -2,
  },
  form: {
    gap: theme.spacing.md,
    backgroundColor: theme.colors.surface1,
    borderColor: theme.colors.border,
    borderWidth: 1,
    borderRadius: theme.radius.xl,
    padding: theme.spacing.md,
  },
  errorBox: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  passwordStrength: {
    flexDirection: "row",
    gap: 4,
    marginTop: -4,
  },
  strengthBar: {
    flex: 1,
    height: 3,
    borderRadius: 2,
  },
  perks: {
    flexDirection: "row",
    justifyContent: "space-around",
    paddingVertical: 12,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
  },
  perkItem: {
    alignItems: "center",
    gap: 4,
    flex: 1,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
  },
});

export default function RegisterScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const params = useLocalSearchParams<{ ref?: string }>();
  const { register: storeRegister } = useAuthStore();

  const referralFromLink = typeof params.ref === "string" ? params.ref.trim().toUpperCase() : "";

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    referralCode: referralFromLink,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update(field: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
    setError(null);
  }

  async function handleRegister() {
    if (!form.username.trim()) return setError("Username is required");
    if (!form.email.trim()) return setError("Email is required");
    if (form.password.length < 8)
      return setError("Password must be at least 8 characters");
    if (form.password !== form.confirmPassword)
      return setError("Passwords do not match");

    setLoading(true);
    setError(null);
    try {
      await storeRegister({
        username: form.username.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        role: "customer",
        referral_code: form.referralCode.trim() || undefined,
      });
      Alert.alert(
        "Account Created!",
        "Welcome to ZOZI! A verification email has been sent — please verify your email to ensure continued access.",
        [{ text: "Continue Shopping", onPress: () => router.replace("/(tabs)/products") }]
      );
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Registration failed. Try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <Stack.Screen options={{ title: "Create Account", headerShown: false }} />
      <ScrollView
        contentContainerStyle={[s.container, styles.scroll]}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Logo size="lg" />
          <Text style={[s.subtitle, { textAlign: "center" }]}>
            Trust Delivered
          </Text>
        </View>

        <View style={styles.form}>
          {error && (
            <View
              style={[styles.errorBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}
            >
              <Ionicons name="alert-circle" size={18} color={theme.colors.danger} />
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.base, flex: 1 }}>
                {error}
              </Text>
            </View>
          )}

          <Input
            label="Username"
            placeholder="johndoe"
            value={form.username}
            onChangeText={(t) => update("username", t)}
            autoCapitalize="none"
          />
          <Input
            label="Email"
            placeholder="you@example.com"
            value={form.email}
            onChangeText={(t) => update("email", t)}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
          />
          <Input
            label="Password"
            placeholder="Min. 8 characters"
            value={form.password}
            onChangeText={(t) => update("password", t)}
            isPassword
          />
          {/* Password strength indicator */}
          {form.password.length > 0 && (
            <View style={styles.passwordStrength}>
              {[1, 2, 3, 4].map((level) => {
                const strength = (form.password.length >= 8 ? 1 : 0) + (/[A-Z]/.test(form.password) ? 1 : 0) + (/[0-9]/.test(form.password) ? 1 : 0) + (/[^A-Za-z0-9]/.test(form.password) ? 1 : 0);
                const colors = [theme.colors.danger, theme.colors.warning, theme.colors.success, theme.colors.success];
                return (
                  <View key={level} style={[styles.strengthBar, { backgroundColor: level <= strength ? colors[Math.min(strength - 1, 3)] : theme.colors.surface0 }]} />
                );
              })}
            </View>
          )}
          <Input
            label="Confirm Password"
            placeholder="Repeat password"
            value={form.confirmPassword}
            onChangeText={(t) => update("confirmPassword", t)}
            isPassword
            error={
              form.confirmPassword && form.password !== form.confirmPassword
                ? "Passwords don't match"
                : undefined
            }
          />

          <Input
            label="Referral Code (Optional)"
            placeholder="Enter invite code"
            value={form.referralCode}
            onChangeText={(t) => update("referralCode", t.toUpperCase())}
            autoCapitalize="characters"
          />

          <GradientButton
            label={loading ? "Creating account..." : "Create Account"}
            onPress={handleRegister}
            loading={loading}
            testID="auth-register-submit"
            style={{ marginTop: theme.spacing.sm }}
          />
        </View>

        {/* Member perks */}
        <View style={[styles.perks, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={styles.perkItem}>
            <Ionicons name="flash" size={18} color={theme.colors.brand} />
            <Text style={{ color: theme.colors.textMuted, fontSize: 10, textAlign: "center" }}>Exclusive{"\n"}Deals</Text>
          </View>
          <View style={styles.perkItem}>
            <Ionicons name="notifications" size={18} color={theme.colors.brand} />
            <Text style={{ color: theme.colors.textMuted, fontSize: 10, textAlign: "center" }}>Order{"\n"}Tracking</Text>
          </View>
          <View style={styles.perkItem}>
            <Ionicons name="heart" size={18} color={theme.colors.brand} />
            <Text style={{ color: theme.colors.textMuted, fontSize: 10, textAlign: "center" }}>Save{"\n"}Wishlist</Text>
          </View>
          <View style={styles.perkItem}>
            <Ionicons name="star" size={18} color={theme.colors.brand} />
            <Text style={{ color: theme.colors.textMuted, fontSize: 10, textAlign: "center" }}>Write{"\n"}Reviews</Text>
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={{ color: theme.colors.textMuted }}>
            Already have an account?{" "}
          </Text>
          <TouchableOpacity onPress={() => router.push("/(auth)/login")}>
            <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>
              Sign In
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// styles moved into component so `theme` is available
