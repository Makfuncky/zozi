import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Image,
  ActivityIndicator,
} from "react-native";
import DocumentPicker from "@/lib/documentPicker";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import AppHeader from "@/components/ui/AppHeader";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

// ── Inline address book helpers (mirrored from web_app/src/lib/addressBook.ts) ──

interface DeliveryDetails {
  fullName: string;
  phone: string;
  street: string;
  city: string;
  zip: string;
  country: string;
  deliveryLocation: string;
  deliveryNote: string;
}

const EMPTY: DeliveryDetails = {
  fullName: "", phone: "", street: "", city: "",
  zip: "", country: "UAE", deliveryLocation: "", deliveryNote: "",
};

function parseAddressBook(raw?: string | null): DeliveryDetails {
  if (!raw) return { ...EMPTY };
  try {
    const parsed = JSON.parse(raw);
    const src = Array.isArray(parsed)
      ? parsed.find((a: any) => a?.is_default) || parsed[0]
      : (parsed?.default_shipping || parsed);
    if (!src || typeof src !== "object") return { ...EMPTY };
    return {
      fullName: src.full_name || src.fullName || "",
      phone: src.phone || "",
      street: src.street || "",
      city: src.city || "",
      zip: src.zip || src.postal_code || "",
      country: src.country || "UAE",
      deliveryLocation: src.delivery_location || src.deliveryLocation || "",
      deliveryNote: src.delivery_note || src.deliveryNote || "",
    };
  } catch { return { ...EMPTY }; }
}

function stringifyAddressBook(d: DeliveryDetails): string {
  return JSON.stringify({
    default_shipping: {
      full_name: d.fullName, phone: d.phone, street: d.street,
      city: d.city, zip: d.zip, country: d.country,
      delivery_location: d.deliveryLocation, delivery_note: d.deliveryNote,
    },
  });
}

// ── Styles ────────────────────────────────────────────────────────────────────

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 18, paddingBottom: 50 },
    avatarSection: {
      alignItems: "center",
      gap: theme.spacing.sm,
      paddingVertical: theme.spacing.md,
    },
    avatar: { width: 90, height: 90, borderRadius: 45 },
    avatarFallback: {
      width: 90, height: 90, borderRadius: 45,
      alignItems: "center", justifyContent: "center",
    },
    changePhotoBtn: {
      paddingHorizontal: 16, paddingVertical: 6,
      borderRadius: 20, borderWidth: 1,
    },
    card: {
      borderRadius: theme.radius.xl, borderWidth: 1,
      padding: theme.spacing.md, gap: 12,
    },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", letterSpacing: 0.5, marginBottom: 2 },
    input: {
      borderWidth: 1, borderRadius: theme.radius.md,
      paddingHorizontal: 12, paddingVertical: 10,
      fontSize: theme.fontSize.sm,
    },
    verifyRow: {
      flexDirection: "row", alignItems: "center",
      justifyContent: "space-between",
      paddingVertical: 10, borderRadius: theme.radius.md,
      paddingHorizontal: 12, borderWidth: 1, gap: 8,
    },
    saveBtn: {
      borderRadius: theme.radius.lg,
      paddingVertical: 14, alignItems: "center",
    },
    saveBtnText: { fontSize: theme.fontSize.md, fontWeight: "700", color: "#fff" },
    sectionTitle: {
      fontSize: theme.fontSize.xs, fontWeight: "700",
      letterSpacing: 1, marginBottom: 4, paddingHorizontal: 2,
    },
  });

// ── Component ─────────────────────────────────────────────────────────────────

export default function EditProfileScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user, refresh: refreshAuth } = useAuthStore();

  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [resendingVerification, setResendingVerification] = useState(false);

  // Profile fields
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  // Delivery address
  const [fullName, setFullName] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [zip, setZip] = useState("");
  const [country, setCountry] = useState("UAE");
  const [deliveryLocation, setDeliveryLocation] = useState("");
  const [deliveryNote, setDeliveryNote] = useState("");

  // Full user object with address_book
  const [fullUser, setFullUser] = useState<any>(null);

  useEffect(() => {
    // Pre-populate from authStore immediately
    if (user) {
      setUsername(user.username || "");
      setEmail(user.email || "");
      setPhone(user.phone || "");
    }
    // Fetch full profile (includes address_book)
    apiFetch<any>("/auth/me")
      .then((me) => {
        setFullUser(me);
        const addr = parseAddressBook(me.address_book);
        setFullName(addr.fullName);
        setStreet(addr.street);
        setCity(addr.city);
        setZip(addr.zip);
        setCountry(addr.country);
        setDeliveryLocation(addr.deliveryLocation);
        setDeliveryNote(addr.deliveryNote);
      })
      .catch(() => {});
  }, [user]);

  async function pickAndUploadAvatar() {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        types: ["image/*"],
      });
      if (result.canceled || !result.assets?.length) return;
      const asset = result.assets[0];
      setAvatarUploading(true);
      const form = new FormData();
      form.append("file", {
        uri: asset.uri,
        name: asset.name || "avatar.jpg",
        type: asset.mimeType || "image/jpeg",
      } as any);
      await apiFetch("/auth/me/avatar", { method: "POST", body: form });
      await refreshAuth();
      setMsg("Profile photo updated!");
    } catch {
      setError("Failed to upload photo");
    } finally {
      setAvatarUploading(false);
    }
  }

  async function saveProfile() {
    setMsg(""); setError("");
    setSaving(true);
    try {
      await apiFetch("/auth/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          phone: phone || null,
          address_book: stringifyAddressBook({
            fullName, phone, street, city, zip, country, deliveryLocation, deliveryNote,
          }),
        }),
      });
      await refreshAuth();
      setMsg("Profile updated successfully!");
    } catch (err: any) {
      setError(err?.detail || err?.message || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  async function resendVerification() {
    setResendingVerification(true);
    try {
      await apiFetch("/auth/resend-verification", { method: "POST" });
      Alert.alert("Verification Sent", "Check your email for the verification link.");
    } catch {
      Alert.alert("Error", "Failed to send verification email.");
    } finally {
      setResendingVerification(false);
    }
  }

  const avatarUri = (fullUser?.profile_image || user?.profile_image) as string | undefined;
  const isVerified = fullUser?.email_verified ?? user?.email_verified ?? false;

  return (
    <>
      <AppHeader showSearch={false} />
      <ScrollView
        style={s.container}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Avatar */}
        <View style={styles.avatarSection}>
          {avatarUri ? (
            <Image source={{ uri: avatarUri }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatarFallback, { backgroundColor: theme.colors.brand + "33" }]}>
              <Text style={{ fontSize: 40 }}>👤</Text>
            </View>
          )}
          <TouchableOpacity
            style={[styles.changePhotoBtn, { borderColor: theme.colors.brand }]}
            onPress={pickAndUploadAvatar}
            disabled={avatarUploading}
          >
            {avatarUploading ? (
              <ActivityIndicator size="small" color={theme.colors.brand} />
            ) : (
              <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                📷 Change Photo
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Feedback */}
        {msg ? (
          <Text style={{ color: theme.colors.success, textAlign: "center", fontWeight: "600" }}>{msg}</Text>
        ) : null}
        {error ? (
          <Text style={{ color: theme.colors.danger, textAlign: "center" }}>{error}</Text>
        ) : null}

        {/* Email verification status */}
        <View style={[styles.verifyRow, {
          backgroundColor: isVerified ? theme.colors.success + "18" : theme.colors.warning + "18",
          borderColor: isVerified ? theme.colors.success : theme.colors.warning,
        }]}>
          <Text style={{ fontSize: 18 }}>{isVerified ? "✅" : "⚠️"}</Text>
          <Text style={[s.text, { flex: 1, fontSize: theme.fontSize.sm }]}>
            {isVerified ? "Email verified" : "Email not verified"}
          </Text>
          {!isVerified && (
            <TouchableOpacity onPress={resendVerification} disabled={resendingVerification}>
              {resendingVerification ? (
                <ActivityIndicator size="small" color={theme.colors.brand} />
              ) : (
                <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.xs }}>
                  Resend
                </Text>
              )}
            </TouchableOpacity>
          )}
        </View>

        {/* Personal Info */}
        <View>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>PERSONAL INFO</Text>
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Username</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                autoCorrect={false}
                placeholder="Username"
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Email</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                placeholder="Email"
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Phone</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={phone}
                onChangeText={setPhone}
                keyboardType="phone-pad"
                placeholder="+971 ..."
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
          </View>
        </View>

        {/* Delivery Address */}
        <View>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>DELIVERY ADDRESS</Text>
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Full Name</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={fullName}
                onChangeText={setFullName}
                placeholder="Recipient full name"
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Street / Building</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={street}
                onChangeText={setStreet}
                placeholder="Street address, apartment, villa..."
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View style={{ flexDirection: "row", gap: 10 }}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.label, { color: theme.colors.textMuted }]}>City</Text>
                <TextInput
                  style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                  value={city}
                  onChangeText={setCity}
                  placeholder="Dubai"
                  placeholderTextColor={theme.colors.textFaint}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.label, { color: theme.colors.textMuted }]}>ZIP / Postal</Text>
                <TextInput
                  style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                  value={zip}
                  onChangeText={setZip}
                  keyboardType="numeric"
                  placeholder="00000"
                  placeholderTextColor={theme.colors.textFaint}
                />
              </View>
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Country</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={country}
                onChangeText={setCountry}
                placeholder="UAE"
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Delivery Location / Area</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={deliveryLocation}
                onChangeText={setDeliveryLocation}
                placeholder="e.g. Downtown, JBR, Marina..."
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Delivery Note</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2, height: 72, textAlignVertical: "top" }]}
                value={deliveryNote}
                onChangeText={setDeliveryNote}
                placeholder="Gate code, landmark, instructions..."
                placeholderTextColor={theme.colors.textFaint}
                multiline
                numberOfLines={3}
              />
            </View>
          </View>
        </View>

        {/* Save */}
        <TouchableOpacity
          style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]}
          onPress={saveProfile}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.saveBtnText}>💾 Save Profile</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </>
  );
}
