// Admin Login (React Native)
import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import Logo from "@/components/Logo";
import { Ionicons } from "@expo/vector-icons";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export default function AdminLoginPage() {
  const { theme } = useThemeStore();
  const { login } = useAuthStore();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("Please enter email and password.");
      return;
    }
    setLoading(true);
    try {
      await login(email.trim(), password);
      const { user: updatedUser } = useAuthStore.getState();
      if (updatedUser?.role !== "admin") {
        const { logout } = useAuthStore.getState();
        await logout();
        setError("Access denied. Admin account required.");
        return;
      }
      router.replace("/admin/dashboard" as never);
    } catch (err: any) {
      const msg = err?.message ?? "";
      if (msg.includes("401") || msg.includes("Unauthorized") || msg.includes("incorrect")) {
        setError("Invalid email or password.");
      } else if (msg.includes("403") || msg.includes("Forbidden")) {
        setError("Access denied. Admin account required.");
      } else {
        setError("Login failed. Please check your connection and try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.colors.surface0 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Stack.Screen options={{ title: "Admin Login" }} />
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {/* Logo / title */}
        <View style={styles.logoArea}>
          <Logo size="lg" />
          <Text style={[styles.header, { color: theme.colors.text }]}>Admin Portal</Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: 14, textAlign: "center", marginTop: 4 }}>
            Sign in with your administrator credentials
          </Text>
        </View>

        {/* Error message */}
        {error ? (
          <View style={[styles.errorBox, { borderColor: theme.colors.danger, backgroundColor: `${theme.colors.danger}18` }]}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
              <Ionicons name="alert-circle" size={14} color={theme.colors.danger} />
              <Text style={{ color: theme.colors.danger, fontSize: 14 }}>{error}</Text>
            </View>
          </View>
        ) : null}

        {/* Email */}
        <Input
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="admin@zozi.com"
          placeholderTextColor={theme.colors.textMuted}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          returnKeyType="next"
          editable={!loading}
          containerStyle={styles.fieldGroup}
        />

        {/* Password */}
        <Input
          label="Password"
          value={password}
          onChangeText={setPassword}
          placeholder="••••••••"
          isPassword
          returnKeyType="done"
          onSubmitEditing={handleLogin}
          editable={!loading}
          containerStyle={styles.fieldGroup}
        />

        {/* Login button */}
        <Button
          label={loading ? "Signing in…" : "Sign In"}
          onPress={handleLogin}
          loading={loading}
          disabled={loading}
          size="lg"
          style={[styles.btn, { marginTop: 8 }]}
          accessibilityHint="Sign in to the admin portal"
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  logoArea: {
    alignItems: "center",
    marginBottom: 32,
  },
  header: {
    fontSize: 24,
    fontWeight: "700",
    marginTop: 12,
  },
  errorBox: {
    width: "100%",
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  fieldGroup: {
    width: "100%",
    marginBottom: 14,
  },
  btn: {
    width: "100%",
  },
});
