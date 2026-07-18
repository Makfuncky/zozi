import React, { useState } from "react";
import { View, Text, ScrollView, KeyboardAvoidingView, Platform, StyleSheet } from "react-native";

import { Stack, useRouter } from "expo-router";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import Logo from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: { padding: theme.spacing.lg, paddingBottom: 40, gap: 20, flexGrow: 1, justifyContent: "center" },
  header: { alignItems: "center", gap: 6 },
  title: { fontSize: theme.fontSize["2xl"], fontWeight: "800", letterSpacing: -0.5 },
  subtitle: { fontSize: theme.fontSize.base, textAlign: "center" },
  card: { borderRadius: 20, borderWidth: 1, padding: 20, gap: theme.spacing.md },
  errorBox: { borderWidth: 1, borderRadius: 10, padding: 12 },
});

export default function SupplierLoginScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { login, isLoading } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleLogin() {
    if (!email.trim()) return setError("Email is required");
    if (!password) return setError("Password is required");
    setError(null);

    try {
      const user = await login(email.trim(), password);
      if (user.role !== "supplier") {
        setError("This account does not have supplier access.");
        return;
      }
      router.replace("/supplier/dashboard" as never);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed. Check your credentials.");
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <Stack.Screen options={{ title: "Supplier Login" }} />
      <ScrollView
        style={s.container}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Logo size="lg" />
          <Text style={[s.text, styles.title]}>Supplier Portal</Text>
          <Text style={[s.textMuted, styles.subtitle]}>
            Sign in to manage your products and orders
          </Text>
        </View>

        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input
            label="Email"
            value={email}
            onChangeText={(t) => { setEmail(t); setError(null); }}
            placeholder="your@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <Input
            label="Password"
            value={password}
            onChangeText={(t) => { setPassword(t); setError(null); }}
            placeholder="••••••••"
            secureTextEntry
          />

          {error && (
            <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm }}>{error}</Text>
            </View>
          )}

          <Button label="Sign In as Supplier" onPress={handleLogin} loading={isLoading} />
        </View>

        <View style={[s.row, { justifyContent: "center", marginTop: 20 }]}>
          <Text style={s.textMuted}>Not a supplier? </Text>
          <Text
            style={[s.textBrand, { fontWeight: "600" }]}
            onPress={() => router.replace("/(auth)/login" as never)}
          >
            Customer Login
          </Text>
        </View>

        <View style={[s.row, { justifyContent: "center", marginTop: 12 }]}>
          <Text style={s.textMuted}>New supplier? </Text>
          <Text
            style={[s.textBrand, { fontWeight: "600" }]}
            onPress={() => router.push("/supplier/register" as never)}
          >
            Register here
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
