import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import ScreenHeader from "@/components/ui/ScreenHeader";

export default function ChangePasswordScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [current, setCurrent] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const strength = (() => {
    if (newPwd.length === 0) return null;
    let score = 0;
    if (newPwd.length >= 8) score++;
    if (/[A-Z]/.test(newPwd)) score++;
    if (/[0-9]/.test(newPwd)) score++;
    if (/[^A-Za-z0-9]/.test(newPwd)) score++;
    if (score <= 1) return { label: "Weak", color: theme.colors.danger };
    if (score === 2) return { label: "Fair", color: theme.colors.warning };
    if (score === 3) return { label: "Good", color: theme.colors.brand };
    return { label: "Strong", color: theme.colors.success };
  })();

  const submit = async () => {
    if (!current.trim()) return Alert.alert("Error", "Please enter your current password.");
    if (newPwd.length < 8) return Alert.alert("Error", "New password must be at least 8 characters.");
    if (newPwd !== confirm) return Alert.alert("Error", "New passwords do not match.");

    setSaving(true);
    try {
      await apiFetch<{ detail?: string }>("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: current, new_password: newPwd }),
      });
      Alert.alert("Success", "Password changed successfully.", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch {
      Alert.alert("Error", "Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <ScreenHeader title="Change Password" />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView style={[s.container, { flex: 1 }]} contentContainerStyle={{ padding: 20, gap: theme.spacing.md, paddingBottom: 40 }}>
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.base, marginBottom: theme.spacing.xs }}>
            Choose a strong password with at least 8 characters, including uppercase letters, numbers, and symbols.
          </Text>

          {/* Current Password */}
          <View>
            <Text style={[s.text, { fontWeight: "600", marginBottom: 6 }]}>Current Password</Text>
            <View style={[localStyles.inputRow, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
              <TextInput
                style={[localStyles.input, { color: theme.colors.text }]}
                value={current}
                onChangeText={setCurrent}
                placeholder="Enter current password"
                placeholderTextColor={theme.colors.textMuted}
                secureTextEntry={!showCurrent}
                autoCapitalize="none"
              />
              <TouchableOpacity onPress={() => setShowCurrent((v) => !v)}>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.md }}>{showCurrent ? "🙉" : "🙈"}</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* New Password */}
          <View>
            <Text style={[s.text, { fontWeight: "600", marginBottom: 6 }]}>New Password</Text>
            <View style={[localStyles.inputRow, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
              <TextInput
                style={[localStyles.input, { color: theme.colors.text }]}
                value={newPwd}
                onChangeText={setNewPwd}
                placeholder="Min. 8 characters"
                placeholderTextColor={theme.colors.textMuted}
                secureTextEntry={!showNew}
                autoCapitalize="none"
              />
              <TouchableOpacity onPress={() => setShowNew((v) => !v)}>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.md }}>{showNew ? "🙉" : "🙈"}</Text>
              </TouchableOpacity>
            </View>
            {strength && (
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 6 }}>
                <View style={{ flex: 1, height: theme.spacing.xs, borderRadius: 2, backgroundColor: theme.colors.border, overflow: "hidden" }}>
                  <View style={{ width: strength.label === "Weak" ? "25%" : strength.label === "Fair" ? "50%" : strength.label === "Good" ? "75%" : "100%", height: theme.spacing.xs, backgroundColor: strength.color }} />
                </View>
                <Text style={{ color: strength.color, fontSize: theme.fontSize.sm, fontWeight: "700" }}>{strength.label}</Text>
              </View>
            )}
          </View>

          {/* Confirm Password */}
          <View>
            <Text style={[s.text, { fontWeight: "600", marginBottom: 6 }]}>Confirm New Password</Text>
            <View style={[
              localStyles.inputRow,
              {
                borderColor: confirm && newPwd !== confirm ? theme.colors.danger : theme.colors.border,
                backgroundColor: theme.colors.surface1,
              },
            ]}>
              <TextInput
                style={[localStyles.input, { color: theme.colors.text }]}
                value={confirm}
                onChangeText={setConfirm}
                placeholder="Re-enter new password"
                placeholderTextColor={theme.colors.textMuted}
                secureTextEntry={!showConfirm}
                autoCapitalize="none"
              />
              <TouchableOpacity onPress={() => setShowConfirm((v) => !v)}>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.md }}>{showConfirm ? "🙉" : "🙈"}</Text>
              </TouchableOpacity>
            </View>
            {confirm && newPwd !== confirm && (
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm, marginTop: theme.spacing.xs }}>Passwords do not match</Text>
            )}
            {confirm && newPwd === confirm && confirm.length > 0 && (
              <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm, marginTop: theme.spacing.xs }}>✓ Passwords match</Text>
            )}
          </View>

          <TouchableOpacity
            style={[localStyles.btn, { backgroundColor: theme.colors.brand }, saving && { opacity: 0.6 }]}
            onPress={submit}
            disabled={saving}
          >
            {saving
              ? <ActivityIndicator color="#fff" size="small" />
              : <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>Change Password</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: theme.spacing.xs,
  },
  input: { flex: 1, fontSize: theme.fontSize.base, paddingVertical: 10 },
  btn: { paddingVertical: theme.spacing.md, borderRadius: theme.radius.lg, alignItems: "center", justifyContent: "center" },
});
