/**
 * NewsletterSignup — mobile newsletter subscription component.
 * Shows a compact, attractive email subscription form with app-store style.
 */
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { apiFetch } from "@/lib/api";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  LinearGradient = null;
}

// Dimensions available for responsive layout if needed

interface Props {
  variant?: "card" | "inline" | "banner";
}

export default function NewsletterSignup({ variant = "card" }: Props) {
  const { theme } = useThemeStore();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubscribe = async () => {
    const trimmed = email.trim();
    if (!trimmed) return;
    // Basic email check
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setResult({ type: "error", text: "Please enter a valid email address." });
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      await apiFetch("/email/newsletter/subscribe", {
        method: "POST",
        body: JSON.stringify({ email: trimmed, source: "mobile_app" }),
      });
      setResult({ type: "success", text: "Subscribed! Check your inbox." });
      setEmail("");
    } catch {
      setResult({ type: "error", text: "Could not subscribe. Try again." });
    } finally {
      setLoading(false);
    }
  };

  if (result?.type === "success") {
    return (
      <View style={[styles.successContainer, { backgroundColor: theme.colors.success + "18", borderColor: theme.colors.success + "44" }]}>
        <Ionicons name="checkmark-circle" size={28} color={theme.colors.success} />
        <Text style={{ color: theme.colors.success, fontWeight: "700", fontSize: 15, marginTop: 4 }}>
          {result.text}
        </Text>
      </View>
    );
  }

  const Wrapper = LinearGradient || View;
  const wrapperProps = LinearGradient
    ? { colors: [theme.colors.brand + "22", theme.colors.brand + "08"], start: { x: 0, y: 0 }, end: { x: 1, y: 1 } }
    : { style: { backgroundColor: theme.colors.brand + "12" } };

  if (variant === "banner") {
    return (
      <Wrapper {...wrapperProps} style={[styles.bannerContainer, wrapperProps.style]}>
        <View style={styles.bannerRow}>
          <View style={[styles.iconCircle, { backgroundColor: theme.colors.brand + "22" }]}>
            <Ionicons name="mail" size={20} color={theme.colors.brand} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 14 }}>Get exclusive deals</Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: 11, marginTop: 1 }}>Subscribe for offers & updates</Text>
          </View>
        </View>
        <View style={styles.inputRow}>
          <TextInput
            style={[styles.bannerInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
            value={email}
            onChangeText={setEmail}
            placeholder="your@email.com"
            placeholderTextColor={theme.colors.textMuted}
            keyboardType="email-address"
            autoCapitalize="none"
            returnKeyType="send"
            onSubmitEditing={handleSubscribe}
          />
          <TouchableOpacity
            style={[styles.bannerBtn, { backgroundColor: theme.colors.brand }]}
            onPress={handleSubscribe}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Ionicons name="arrow-forward" size={18} color="#fff" />
            )}
          </TouchableOpacity>
        </View>
        {result?.type === "error" && (
          <Text style={{ color: theme.colors.danger, fontSize: 11, marginTop: 4 }}>{result.text}</Text>
        )}
      </Wrapper>
    );
  }

  return (
    <Wrapper {...wrapperProps} style={[styles.cardContainer, wrapperProps.style, { borderColor: theme.colors.border }]}>
      {/* Header */}
      <View style={styles.cardHeader}>
        <View style={[styles.iconCircle, { backgroundColor: theme.colors.brand + "22" }]}>
          <Ionicons name="mail-unread" size={24} color={theme.colors.brand} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: 16 }}>Stay in the loop</Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: 12, marginTop: 2 }}>
            Get exclusive deals, new arrivals & sale alerts
          </Text>
        </View>
      </View>

      {/* Input */}
      <View style={styles.inputRow}>
        <TextInput
          style={[styles.cardInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
          value={email}
          onChangeText={setEmail}
          placeholder="Enter your email"
          placeholderTextColor={theme.colors.textMuted}
          keyboardType="email-address"
          autoCapitalize="none"
          returnKeyType="send"
          onSubmitEditing={handleSubscribe}
        />
        <TouchableOpacity
          style={[styles.subscribeBtn, { backgroundColor: theme.colors.brand }]}
          onPress={handleSubscribe}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={{ color: "#fff", fontWeight: "700", fontSize: 14 }}>Subscribe</Text>
          )}
        </TouchableOpacity>
      </View>

      {result?.type === "error" && (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Ionicons name="alert-circle" size={14} color={theme.colors.danger} />
          <Text style={{ color: theme.colors.danger, fontSize: 11 }}>{result.text}</Text>
        </View>
      )}

      <Text style={{ color: theme.colors.textMuted, fontSize: 10, textAlign: "center" }}>
        No spam, unsubscribe anytime.
      </Text>
    </Wrapper>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
    gap: 12,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  inputRow: {
    flexDirection: "row",
    gap: 8,
  },
  cardInput: {
    flex: 1,
    borderWidth: 1.5,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 11,
    fontSize: 14,
  },
  subscribeBtn: {
    paddingHorizontal: 18,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  bannerContainer: {
    borderRadius: 14,
    padding: 14,
    gap: 10,
  },
  bannerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  bannerInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 13,
  },
  bannerBtn: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  successContainer: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 20,
    alignItems: "center",
    gap: 4,
  },
});
