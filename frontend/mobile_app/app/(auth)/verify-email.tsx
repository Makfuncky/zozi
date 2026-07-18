import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
} from "react-native";
import { useRouter, Stack, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { verifyEmail } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

type VerifyState = "verifying" | "success" | "error";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    flexGrow: 1,
    padding: theme.spacing.lg,
    justifyContent: "center",
  },
  center: {
    alignItems: "center",
    gap: theme.spacing.sm,
  },
});

export default function VerifyEmailScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { token } = useLocalSearchParams<{ token: string }>();

  const [state, setState] = useState<VerifyState>("verifying");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setErrorMsg("No verification token found in the link.");
      setState("error");
      return;
    }
    verifyEmail(token)
      .then(() => setState("success"))
      .catch((err: unknown) => {
        setErrorMsg(
          err instanceof Error ? err.message : "Verification failed. The link may have expired."
        );
        setState("error");
      });
  }, [token]);

  return (
    <ScrollView contentContainerStyle={[s.container, styles.scroll]}>
      <Stack.Screen options={{ title: "Verify Email" }} />
      {state === "verifying" && (
        <View style={styles.center}>
          <LoadingSpinner />
          <Text style={[s.textMuted, { marginTop: theme.spacing.md }]}>Verifying your email…</Text>
        </View>
      )}

      {state === "success" && (
        <View style={styles.center}>
            <Ionicons name="checkmark-circle" size={Number(theme.fontSize["3xl"])} color={theme.colors.success} style={{ textAlign: "center" }} />
          <Text style={[s.title, { textAlign: "center", marginTop: 12 }]}>Email Verified!</Text>
          <Text style={[s.textMuted, { textAlign: "center", marginTop: theme.spacing.sm }]}>
            Your email address has been confirmed. You can now sign in.
          </Text>
          <Button
            label="Sign In"
            onPress={() => router.replace("/(auth)/login")}
            style={{ marginTop: theme.spacing.lg }}
          />
        </View>
      )}

      {state === "error" && (
        <View style={styles.center}>
          <Text style={{ fontSize: theme.fontSize["3xl"], textAlign: "center" }}>❌</Text>
          <Text style={[s.title, { textAlign: "center", marginTop: 12, color: theme.colors.danger }]}>
            Verification Failed
          </Text>
          <Text style={[s.textMuted, { textAlign: "center", marginTop: theme.spacing.sm }]}>
            {errorMsg}
          </Text>
          <Button
            label="Back to Sign In"
            onPress={() => router.replace("/(auth)/login")}
            variant="secondary"
            style={{ marginTop: theme.spacing.lg }}
          />
        </View>
      )}
    </ScrollView>
  );
}
