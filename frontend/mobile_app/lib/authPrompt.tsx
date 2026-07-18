import React, { createContext, useCallback, useContext, useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { socialSignIn, SocialSignInError, type SocialProvider } from "@/lib/socialAuth";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme, glassWebFilter } from "@/theme";
import { Input } from "@/components/ui/Input";
import { GradientButton } from "@/components/ui/GradientButton";

type PendingAction = () => void;

interface AuthPromptApi {
  /** Run `action` now if signed in, otherwise open the login popup. */
  requireAuth: (action?: PendingAction) => void;
  isOpen: boolean;
  close: () => void;
}

const AuthPromptContext = createContext<AuthPromptApi | null>(null);

export function useRequireAuth(): AuthPromptApi {
  const ctx = useContext(AuthPromptContext);
  if (!ctx) {
    throw new Error("useRequireAuth must be used within <AuthPromptProvider>");
  }
  return ctx;
}

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    backdrop: {
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      zIndex: 9999,
      backgroundColor: "rgba(0,0,0,0.6)",
      justifyContent: "center",
      alignItems: "center",
      padding: theme.spacing.md,
      ...Platform.select({
        web: { position: "fixed" as const },
      }),
    },
    card: {
      width: "100%",
      maxWidth: 420,
      backgroundColor: theme.colors.glass.panel,
      borderColor: theme.colors.glass.border,
      borderWidth: 1,
      borderRadius: theme.radius.xl,
      padding: theme.spacing.lg,
      gap: theme.spacing.md,
      ...glassWebFilter,
      ...Platform.select({
        web: { boxShadow: "0 24px 60px rgba(0,0,0,0.5)" },
        default: {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 16 },
          shadowOpacity: 0.4,
          shadowRadius: 30,
          elevation: 14,
        },
      }),
    },
    title: { fontSize: theme.fontSize.xl, fontWeight: "800", textAlign: "center" },
    sub: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm, textAlign: "center", marginTop: 2 },
    errorBox: {
      borderWidth: 1,
      borderRadius: 10,
      padding: 10,
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
    },
    dividerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
    dividerLine: { flex: 1, height: 1, backgroundColor: theme.colors.glass.border },
    dividerText: { color: theme.colors.textMuted, fontSize: theme.fontSize.xs },
    socialRow: { flexDirection: "row", gap: 10 },
    socialBtn: {
      flex: 1,
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 6,
      paddingVertical: 11,
      borderRadius: 14,
      borderWidth: 1.5,
      borderColor: theme.colors.glass.border,
      backgroundColor: theme.colors.surface2,
    },
    socialLabel: { fontWeight: "700", fontSize: theme.fontSize.xs, color: theme.colors.text },
    closeRow: { flexDirection: "row", justifyContent: "center" },
    closeText: { color: theme.colors.textMuted, fontSize: theme.fontSize.base, fontWeight: "600" },
  });

export function AuthPromptProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { login: storeLogin } = useAuthStore();

  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = useCallback(() => {
    setOpen(false);
    setPending(null);
    setError(null);
    setLoading(false);
  }, []);

  const requireAuth = useCallback(
    (action?: PendingAction) => {
      if (useAuthStore.getState().isLoggedIn) {
        action?.();
        return;
      }
      setPending(action ?? null);
      setError(null);
      setOpen(true);
    },
    [],
  );

  const finish = useCallback(() => {
    const action = pending;
    setOpen(false);
    setPending(null);
    setError(null);
    setLoading(false);
    action?.();
  }, [pending]);

  async function handleLogin() {
    if (!identifier.trim() || !password) {
      setError("Email or username and password are required");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await storeLogin(identifier.trim(), password);
      finish();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Invalid email/username or password";
      if (/Failed to fetch|Network request failed|ECONNREFUSED/.test(msg)) {
        setError("Could not connect to the server. Please check backend service or API URL.");
      } else if (msg.includes("422") || msg.includes("401")) {
        setError("Invalid email/username or password");
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

  async function handleSocial(provider: (typeof providerCards)[number]) {
    setLoading(true);
    setError(null);
    try {
      await socialSignIn(provider.key);
      finish();
    } catch (err: unknown) {
      setError(
        err instanceof SocialSignInError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Social sign-in failed",
      );
    } finally {
      setLoading(false);
    }
  }

  const api: AuthPromptApi = { requireAuth, isOpen: open, close };

  return (
    <AuthPromptContext.Provider value={api}>
      {children}
      {open && (
        <KeyboardAvoidingView
          style={styles.backdrop}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={close} />
          <TouchableOpacity
            activeOpacity={1}
            style={[styles.card, { zIndex: 1 }]}
            testID="auth-prompt-card"
          >
            <Text style={[s.text, styles.title]}>Sign in to continue</Text>
            <Text style={[s.textMuted, styles.sub]}>
              Create an account or sign in to add items to your cart.
            </Text>

            {error && (
              <View
                style={[styles.errorBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}
              >
                <Ionicons name="alert-circle" size={16} color={theme.colors.danger} />
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm, flex: 1 }}>
                  {error}
                </Text>
              </View>
            )}

            <Input
              label="Email or Username"
              placeholder="you@example.com"
              value={identifier}
              onChangeText={(t) => {
                setIdentifier(t);
                setError(null);
              }}
              autoCapitalize="none"
              autoComplete="username"
              testID="auth-prompt-identifier"
            />
            <Input
              label="Password"
              placeholder="••••••••"
              value={password}
              onChangeText={(t) => {
                setPassword(t);
                setError(null);
              }}
              isPassword
              testID="auth-prompt-password"
            />

            <GradientButton
              label={loading ? "Signing in..." : "Sign In"}
              onPress={handleLogin}
              loading={loading}
              testID="auth-prompt-submit"
            />

            <View style={styles.dividerRow}>
              <View style={styles.dividerLine} />
              <Text style={[s.textMuted, styles.dividerText]}>or continue with</Text>
              <View style={styles.dividerLine} />
            </View>

            <View style={styles.socialRow}>
              {providerCards.map((provider) => (
                <TouchableOpacity
                  key={provider.key}
                  onPress={() => handleSocial(provider)}
                  disabled={loading}
                  activeOpacity={0.8}
                  style={[styles.socialBtn, { opacity: loading ? 0.6 : 1 }]}
                  testID={`auth-prompt-${provider.key}-btn`}
                >
                  <Ionicons
                    name={provider.icon}
                    size={18}
                    color={provider.key === "apple" ? theme.colors.text : provider.color}
                  />
                  <Text style={styles.socialLabel}>{provider.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.closeRow}>
              <TouchableOpacity onPress={close} testID="auth-prompt-dismiss">
                <Text style={[s.text, styles.closeText]}>Continue browsing</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.closeRow}>
              <TouchableOpacity
                onPress={() => {
                  close();
                  router.push("/(auth)/register");
                }}
              >
                <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                  Need an account? Register
                </Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      )}
    </AuthPromptContext.Provider>
  );
}
