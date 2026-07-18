import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from "react-native";
import { useRouter, Stack } from "expo-router";
import { forgotPassword } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    flexGrow: 1,
    padding: theme.spacing.md,
    justifyContent: "center",
    gap: 12,
  },
  header: {
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  errorBox: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
  },
  successBox: {
    alignItems: "center",
    gap: 12,
    paddingHorizontal: theme.spacing.sm,
  },
});

export default function ForgotPasswordScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!email.trim()) return setError("Email is required");
    setLoading(true);
    setError(null);
    try {
      await forgotPassword(email.trim().toLowerCase());
      setSent(true);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Could not send reset email."
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
      <Stack.Screen options={{ title: "Forgot Password" }} />
      <ScrollView
        testID="auth-forgot-password-screen"
        contentContainerStyle={[s.container, styles.scroll]}
        keyboardShouldPersistTaps="handled"
      >
        {sent ? (
          <View testID="auth-forgot-password-success" style={styles.successBox}>
            <Text style={{ fontSize: theme.fontSize["2xl"], textAlign: "center" }}>✉️</Text>
            <Text style={[s.title, { textAlign: "center" }]}>Check your email</Text>
            <Text style={[s.textMuted, { textAlign: "center" }]}>
              We sent a password reset link to {email}
            </Text>
            <Button
              label="Back to Sign In"
              onPress={() => router.replace("/(auth)/login")}
              variant="secondary"
              style={{ marginTop: theme.spacing.md }}
            />
          </View>
        ) : (
          <>
            <View style={styles.header}>
              <Text style={[s.title, { textAlign: "center" }]}>
                Forgot password?
              </Text>
              <Text style={[s.textMuted, { textAlign: "center" }]}>
                Enter your email and we'll send you a reset link.
              </Text>
            </View>

            {error && (
              <View
                testID="auth-forgot-password-error"
                style={[styles.errorBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}
              >
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.base }}>
                  {error}
                </Text>
              </View>
            )}

            <Input
              label="Email"
              placeholder="you@example.com"
              testID="auth-forgot-password-email"
              value={email}
              onChangeText={(t) => { setEmail(t); setError(null); }}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <Button
              testID="auth-forgot-password-submit"
              label="Send Reset Link"
              onPress={handleSubmit}
              loading={loading}
            />
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// styles moved inside component so `theme` is available
