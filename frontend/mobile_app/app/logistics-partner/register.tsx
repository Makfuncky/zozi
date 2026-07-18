import React, { useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme, makeStyles } from "@/theme";
import Logo from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: {
      padding: theme.spacing.lg,
      paddingBottom: 40,
      gap: 20,
      flexGrow: 1,
      justifyContent: "center",
    },
    header: { alignItems: "center", gap: 6 },
    title: { fontSize: theme.fontSize["2xl"], fontWeight: "800", letterSpacing: -0.5 },
    subtitle: { fontSize: theme.fontSize.base, textAlign: "center" },
    card: { borderRadius: 20, borderWidth: 1, padding: 20, gap: theme.spacing.md },
    errorBox: { borderWidth: 1, borderRadius: 10, padding: 12 },
    termsRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      gap: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
    },
  });

export default function LogisticsPartnerRegisterScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { register } = useAuthStore();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validate = (): string | null => {
    if (!username.trim()) return "Username is required";
    if (!/^[a-zA-Z0-9_]{3,30}$/.test(username)) {
      return "Username must be 3-30 characters using letters, numbers, or underscore";
    }
    if (!email.trim()) return "Email is required";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address";
    if (password.length < 8) return "Password must be at least 8 characters";
    if (password !== confirm) return "Passwords do not match";
    if (phone && !/^\+?[\d\s\-().]{7,20}$/.test(phone)) return "Enter a valid phone number";
    if (!termsAccepted) return "You must accept the Terms & Conditions to register";
    return null;
  };

  const handleRegister = async () => {
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const user = await register({
        username: username.trim(),
        email: email.trim().toLowerCase(),
        password,
        phone: phone.trim() || undefined,
        role: "logistics_partner",
        terms_accepted: true,
      });

      if (user.role !== "logistics_partner") {
        setError("This account does not have logistics partner access.");
        return;
      }

      Alert.alert(
        "Registration complete",
        "Your logistics partner account is ready.",
        [{ text: "Open Portal", onPress: () => router.replace("/logistics-partner/dashboard" as never) }]
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <Stack.Screen options={{ title: "Partner Registration" }} />
      <ScrollView
        style={s.container}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Logo size="lg" />
          <Text style={[s.text, styles.title]}>Create Logistics Account</Text>
          <Text style={[s.textMuted, styles.subtitle]}>
            Register your delivery portal access for shipments and fulfilment updates
          </Text>
        </View>

        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
          <Input
            label="Username"
            value={username}
            onChangeText={(value) => { setUsername(value); setError(null); }}
            placeholder="partner_dispatch"
            autoCapitalize="none"
          />
          <Input
            label="Email"
            value={email}
            onChangeText={(value) => { setEmail(value); setError(null); }}
            placeholder="partner@company.com"
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <Input
            label="Phone"
            value={phone}
            onChangeText={(value) => { setPhone(value); setError(null); }}
            placeholder="+971 50 000 0000"
            keyboardType="phone-pad"
          />
          <Input
            label="Password"
            value={password}
            onChangeText={(value) => { setPassword(value); setError(null); }}
            placeholder="••••••••"
            isPassword
          />
          <Input
            label="Confirm Password"
            value={confirm}
            onChangeText={(value) => { setConfirm(value); setError(null); }}
            placeholder="••••••••"
            isPassword
          />

          <View style={styles.termsRow}>
            <Text style={[s.textMuted, { flex: 1 }]}>I agree to the Terms & Conditions for logistics onboarding.</Text>
            <Switch value={termsAccepted} onValueChange={(value) => { setTermsAccepted(value); setError(null); }} />
          </View>

          {error && (
            <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "15", borderColor: theme.colors.danger + "40" }]}>
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm, fontWeight: "600" }}>
                {error}
              </Text>
            </View>
          )}

          <Button label="Register as Partner" onPress={handleRegister} loading={loading} />
        </View>

        <View style={[s.row, { justifyContent: "center", marginTop: 20 }]}>
          <Text style={s.textMuted}>Already have a logistics account? </Text>
          <TouchableOpacity onPress={() => router.replace("/logistics-partner/login" as never)}>
            <Text style={[s.textBrand, { fontWeight: "600" }]}>Sign In</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}