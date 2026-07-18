/**
 * AuthRequiredModal — prompts the user to login/register when trying
 * to perform an action that requires authentication (e.g., wishlist, cart, review).
 * Shows an attractive bottom-sheet style modal with login/register tabs.
 */
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Modal,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { toast } from "@/lib/toastStore";

interface Props {
  visible: boolean;
  onClose: () => void;
  /** Optional callback when auth succeeds—allows caller to retry the blocked action */
  onAuthenticated?: () => void;
  /** Message telling user why login is needed */
  reason?: string;
}

export default function AuthRequiredModal({ visible, onClose, onAuthenticated, reason }: Props) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setUsername("");
    setConfirmPw("");
    setError("");
    setShowPw(false);
  };

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setError("Please fill in all fields.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await login(email.trim(), password);
      toast.success("Welcome back!");
      resetForm();
      onClose();
      onAuthenticated?.();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!username.trim() || !email.trim() || !password || !confirmPw) {
      setError("Please fill in all fields.");
      return;
    }
    if (password !== confirmPw) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim(),
          password,
        }),
      });
      // Auto-login after register
      await login(email.trim(), password);
      toast.success("Account created successfully!");
      resetForm();
      onClose();
      onAuthenticated?.();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <TouchableOpacity style={styles.backdropTouchable} activeOpacity={1} onPress={onClose} />
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          style={styles.sheetWrapper}
        >
          <View style={[styles.sheet, { backgroundColor: theme.colors.surface1 }]}>
            {/* Drag Handle */}
            <View style={[styles.dragHandle, { backgroundColor: theme.colors.border }]} />

            {/* Close button */}
            <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
              <Ionicons name="close" size={22} color={theme.colors.textMuted} />
            </TouchableOpacity>

            {/* Header */}
            <View style={styles.header}>
              <View style={[styles.iconCircle, { backgroundColor: theme.colors.brand + "18" }]}>
                <Ionicons name="lock-open" size={28} color={theme.colors.brand} />
              </View>
              <Text style={[styles.title, { color: theme.colors.text }]}>
                {tab === "login" ? "Welcome Back" : "Create Account"}
              </Text>
              {reason ? (
                <Text style={[styles.reason, { color: theme.colors.textMuted }]}>{reason}</Text>
              ) : (
                <Text style={[styles.reason, { color: theme.colors.textMuted }]}>
                  Sign in to continue shopping
                </Text>
              )}
            </View>

            {/* Tab Toggle */}
            <View style={[styles.tabRow, { backgroundColor: theme.colors.surface0 }]}>
              <TouchableOpacity
                style={[styles.tab, tab === "login" && { backgroundColor: theme.colors.brand }]}
                onPress={() => { setTab("login"); setError(""); }}
              >
                <Text style={{ color: tab === "login" ? "#fff" : theme.colors.text, fontWeight: "700", fontSize: 14 }}>
                  Login
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, tab === "register" && { backgroundColor: theme.colors.brand }]}
                onPress={() => { setTab("register"); setError(""); }}
              >
                <Text style={{ color: tab === "register" ? "#fff" : theme.colors.text, fontWeight: "700", fontSize: 14 }}>
                  Register
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={{ maxHeight: 300 }} showsVerticalScrollIndicator={false}>
              {/* Error */}
              {error ? (
                <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "14" }]}>
                  <Ionicons name="alert-circle" size={16} color={theme.colors.danger} />
                  <Text style={{ color: theme.colors.danger, flex: 1, fontSize: 13 }}>{error}</Text>
                </View>
              ) : null}

              {/* Login Form */}
              {tab === "login" && (
                <View style={styles.form}>
                  <TextInput
                    style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
                    value={email}
                    onChangeText={setEmail}
                    placeholder="Email or username"
                    placeholderTextColor={theme.colors.textMuted}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    textContentType="emailAddress"
                  />
                  <View>
                    <TextInput
                      style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0, paddingRight: 44 }]}
                      value={password}
                      onChangeText={setPassword}
                      placeholder="Password"
                      placeholderTextColor={theme.colors.textMuted}
                      secureTextEntry={!showPw}
                      textContentType="password"
                      returnKeyType="go"
                      onSubmitEditing={handleLogin}
                    />
                    <TouchableOpacity
                      style={styles.eyeBtn}
                      onPress={() => setShowPw(!showPw)}
                    >
                      <Ionicons name={showPw ? "eye-off" : "eye"} size={20} color={theme.colors.textMuted} />
                    </TouchableOpacity>
                  </View>

                  <TouchableOpacity
                    style={[styles.submitBtn, { backgroundColor: theme.colors.brand }]}
                    onPress={handleLogin}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text style={styles.submitText}>Sign In</Text>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={() => { onClose(); router.push("/(auth)/forgot-password"); }}
                    style={{ alignSelf: "center", paddingVertical: 8 }}
                  >
                    <Text style={{ color: theme.colors.brand, fontSize: 13 }}>Forgot Password?</Text>
                  </TouchableOpacity>
                </View>
              )}

              {/* Register Form */}
              {tab === "register" && (
                <View style={styles.form}>
                  <TextInput
                    style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
                    value={username}
                    onChangeText={setUsername}
                    placeholder="Username"
                    placeholderTextColor={theme.colors.textMuted}
                    autoCapitalize="none"
                    textContentType="username"
                  />
                  <TextInput
                    style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
                    value={email}
                    onChangeText={setEmail}
                    placeholder="Email"
                    placeholderTextColor={theme.colors.textMuted}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    textContentType="emailAddress"
                  />
                  <View>
                    <TextInput
                      style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0, paddingRight: 44 }]}
                      value={password}
                      onChangeText={setPassword}
                      placeholder="Password (min 8 chars)"
                      placeholderTextColor={theme.colors.textMuted}
                      secureTextEntry={!showPw}
                      textContentType="newPassword"
                    />
                    <TouchableOpacity
                      style={styles.eyeBtn}
                      onPress={() => setShowPw(!showPw)}
                    >
                      <Ionicons name={showPw ? "eye-off" : "eye"} size={20} color={theme.colors.textMuted} />
                    </TouchableOpacity>
                  </View>
                  <TextInput
                    style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
                    value={confirmPw}
                    onChangeText={setConfirmPw}
                    placeholder="Confirm Password"
                    placeholderTextColor={theme.colors.textMuted}
                    secureTextEntry={!showPw}
                    textContentType="newPassword"
                    returnKeyType="go"
                    onSubmitEditing={handleRegister}
                  />

                  <TouchableOpacity
                    style={[styles.submitBtn, { backgroundColor: theme.colors.brand }]}
                    onPress={handleRegister}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text style={styles.submitText}>Create Account</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  backdropTouchable: {
    flex: 1,
  },
  sheetWrapper: {
    maxHeight: "80%",
  },
  sheet: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingBottom: 30,
    paddingTop: 12,
  },
  dragHandle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: "center",
    marginBottom: 8,
  },
  closeBtn: {
    position: "absolute",
    top: 14,
    right: 16,
    zIndex: 10,
    padding: 4,
  },
  header: {
    alignItems: "center",
    gap: 6,
    marginBottom: 16,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
  },
  reason: {
    fontSize: 13,
    textAlign: "center",
  },
  tabRow: {
    flexDirection: "row",
    borderRadius: 12,
    padding: 3,
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
  },
  form: {
    gap: 12,
  },
  input: {
    borderWidth: 1.5,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 13,
    fontSize: 15,
  },
  eyeBtn: {
    position: "absolute",
    right: 14,
    top: 14,
  },
  submitBtn: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 4,
  },
  submitText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: 16,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderRadius: 10,
    marginBottom: 8,
  },
});
