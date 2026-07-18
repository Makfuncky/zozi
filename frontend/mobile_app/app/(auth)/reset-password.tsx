import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from "react-native";
import { useRouter, Stack, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { resetPassword } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    flexGrow: 1,
    padding: theme.spacing.lg,
    justifyContent: "center",
    gap: 20,
  },
  header: {
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  successBox: {
    gap: 12,
    alignItems: "center",
  },
  errorBox: {
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
});

export default function ResetPasswordScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { token } = useLocalSearchParams<{ token: string }>();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!password) return setError("Password is required");
    if (password.length < 8) return setError("Password must be at least 8 characters");
    if (password !== confirm) return setError("Passwords do not match");
    if (!token) return setError("Invalid or missing reset token");

    setLoading(true);
    setError(null);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Could not reset password. The link may have expired."
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
      <Stack.Screen options={{ title: "Reset Password" }} />
      <ScrollView
        testID="auth-reset-password-screen"
        contentContainerStyle={[s.container, styles.scroll]}
        keyboardShouldPersistTaps="handled"
      >
        {done ? (
          <View testID="auth-reset-password-success" style={styles.successBox}>
            <Ionicons name="checkmark-circle" size={Number(theme.fontSize["3xl"])} color={theme.colors.success} style={{ textAlign: "center" }} />
            <Text style={[s.title, { textAlign: "center" }]}>Password Reset!</Text>
            <Text style={[s.textMuted, { textAlign: "center" }]}>
              Your password has been updated. Please sign in with your new password.
            </Text>
            <Button
              label="Back to Sign In"
              onPress={() => router.replace("/(auth)/login")}
              style={{ marginTop: theme.spacing.md }}
            />
          </View>
        ) : (
          <>
            <View style={styles.header}>
              <Text style={{ fontSize: theme.fontSize["2xl"], textAlign: "center" }}>🔐</Text>
              <Text style={[s.title, { textAlign: "center" }]}>Set New Password</Text>
              <Text style={[s.textMuted, { textAlign: "center" }]}>
                Choose a strong password with at least 8 characters.
              </Text>
            </View>

            {error && (
              <View
                testID="auth-reset-password-error"
                style={[styles.errorBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}
              >
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.base }}>{error}</Text>
              </View>
            )}

            <Input
              label="New Password"
              placeholder="••••••••"
              testID="auth-reset-password-password"
              value={password}
              onChangeText={(t) => { setPassword(t); setError(null); }}
              isPassword
            />
            <Input
              label="Confirm Password"
              placeholder="••••••••"
              testID="auth-reset-password-confirm"
              value={confirm}
              onChangeText={(t) => { setConfirm(t); setError(null); }}
              isPassword
            />

            <Button
              testID="auth-reset-password-submit"
              label="Reset Password"
              onPress={handleSubmit}
              loading={loading}
            />
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
