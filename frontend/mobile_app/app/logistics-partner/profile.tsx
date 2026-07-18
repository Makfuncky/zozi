/**
 * Logistics Partner — Profile Management
 *
 * Tabs: Overview | Business Profile | Coverage | Terms | Guide
 *
 * API:
 *   GET  /logistics-partners/profile
 *   PUT  /logistics-partners/profile
 *   GET  /logistics-partners/service-areas
 *   POST /logistics-partners/service-areas
 *   DELETE /logistics-partners/service-areas/{id}
 *   POST /logistics-partners/accept-terms
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import * as DocumentPicker from "expo-document-picker";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Modal,
  Linking,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import {
  getLogisticsPartnerProfile,
  updateLogisticsPartnerProfile,
  getLogisticsPartnerServiceAreas,
  addLogisticsPartnerServiceArea,
  removeLogisticsPartnerServiceArea,
  acceptLogisticsPartnerTerms,
  getPartnerBankAccount,
  listLogisticsPartnerDocuments,
  upsertPartnerBankAccount,
  uploadLogisticsPartnerDocument,
  deleteLogisticsPartnerDocument,
  type RecipientBankAccount,
  type LogisticsPartnerDocument,
  type LogisticsPartnerProfile,
  type LogisticsPartnerServiceArea,
} from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { AppTheme } from "@/theme";
import { isRtlLocale } from "@shared/localization";
import { Ionicons } from "@expo/vector-icons";

// ─────────────────────── Constants ──────────────────────────────────────────

type TabKey = "overview" | "profile" | "coverage" | "security" | "documents" | "banking" | "terms" | "guide";

const TABS: { key: TabKey; icon: string; label: string }[] = [
  { key: "overview", icon: "grid-outline", label: "Overview" },
  { key: "profile", icon: "person-outline", label: "Profile" },
  { key: "coverage", icon: "map-outline", label: "Coverage" },
  { key: "security", icon: "lock-closed", label: "Security" },
  { key: "documents", icon: "document-text-outline", label: "Docs" },
  { key: "banking", icon: "card-outline", label: "Banking" },
  { key: "terms", icon: "checkmark-outline", label: "Terms" },
  { key: "guide", icon: "book-outline", label: "Guide" },
];

const SERVICE_TYPES: { id: string; label: string }[] = [
  { id: "standard", label: "Standard" },
  { id: "express", label: "Express" },
  { id: "same_day", label: "Same-Day" },
  { id: "cross_border", label: "Cross-Border" },
  { id: "returns", label: "Returns" },
  { id: "cold_chain", label: "Cold Chain" },
  { id: "fragile", label: "Fragile" },
];

const LP_DOC_TYPES: { value: string; label: string }[] = [
  { value: "trade_license", label: "Trade License" },
  { value: "national_id", label: "National ID" },
  { value: "passport", label: "Passport" },
  { value: "insurance", label: "Insurance Certificate" },
  { value: "tax_certificate", label: "Tax Certificate" },
  { value: "other", label: "Other" },
];

const LP_DOC_STATUS_COLORS = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
  under_review: "warning",
} as const;

const TERMS_TEXT = `By accepting these terms, you agree to:

1. Deliver all assigned shipments within the agreed SLA timelines.
2. Handle parcels with care and report any damages immediately.
3. Use the Zozi platform exclusively for Zozi-assigned orders during active assignments.
4. Maintain accurate and up-to-date profile information.
5. Comply with all applicable local customs, import/export regulations.
6. Keep all customer information strictly confidential.
7. Report lost or undeliverable shipments within 24 hours.
8. Accept dispute resolutions as per the Zozi Partner Agreement.

Violation of these terms may result in suspension or permanent removal from the platform.`;

const GUIDE_STEPS: { title: string; detail: string }[] = [
  {
    title: "Complete Your Profile",
    detail: "Fill in all business details including contact info, address, and your service types.",
  },
  {
    title: "Add Coverage Areas",
    detail: "Add every city and country you can deliver to, including per-route charges if applicable.",
  },
  {
    title: "Accept Terms",
    detail: "Read and accept the Zozi Logistics Partner Agreement to activate your account.",
  },
  {
    title: "Await Verification",
    detail: "Our team will review your profile within 1-3 business days and notify you via email.",
  },
  {
    title: "Start Receiving Shipments",
    detail: "Once approved, shipments assigned to your coverage area will appear in your dashboard.",
  },
];

// ─────────────────────── Styles ──────────────────────────────────────────────

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.surface0 },
    tabBar: {
      flexDirection: "row",
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
      backgroundColor: theme.colors.surface1,
    },
    tabItem: {
      flex: 1,
      paddingVertical: 12,
      alignItems: "center",
      gap: 2,
    },
    tabIcon: { fontSize: 16 },
    tabLabel: { fontSize: 9, fontWeight: "700" },
    tabIndicator: {
      position: "absolute",
      bottom: 0,
      left: 0,
      right: 0,
      height: 2,
      borderRadius: 2,
    },
    scroll: { padding: theme.spacing.md, gap: 14, paddingBottom: 50 },
    card: {
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface1,
      padding: theme.spacing.md,
      gap: 12,
    },
    cardTitle: {
      fontSize: theme.fontSize.md,
      fontWeight: "800",
      letterSpacing: 0.2,
    },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    label: { fontSize: theme.fontSize.sm, fontWeight: "600" },
    value: { fontSize: theme.fontSize.sm, flex: 1, textAlign: "right" },
    chip: {
      borderRadius: 20,
      paddingHorizontal: 12,
      paddingVertical: 5,
      borderWidth: 1,
    },
    chipText: { fontSize: theme.fontSize.xs, fontWeight: "700" },
    fieldLabel: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 4 },
    input: {
      borderWidth: 1,
      borderRadius: theme.radius.lg,
      padding: theme.spacing.sm,
      fontSize: theme.fontSize.sm,
      minHeight: 42,
    },
    textArea: { minHeight: 80, textAlignVertical: "top" },
    saveBtn: {
      borderRadius: theme.radius.lg,
      paddingVertical: 14,
      alignItems: "center",
      marginTop: 6,
    },
    saveBtnText: { fontSize: theme.fontSize.md, fontWeight: "800" },
    chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    serviceChip: {
      borderRadius: theme.radius.lg,
      borderWidth: 1.5,
      paddingHorizontal: 14,
      paddingVertical: 8,
    },
    serviceChipText: { fontSize: theme.fontSize.xs, fontWeight: "700" },
    areaCard: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface2,
      padding: 12,
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    deleteBtn: {
      borderRadius: theme.radius.lg,
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderWidth: 1,
    },
    addBtn: {
      borderRadius: theme.radius.lg,
      paddingVertical: 12,
      alignItems: "center",
      borderWidth: 1.5,
      marginTop: 6,
    },
    termsBox: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      padding: theme.spacing.md,
      maxHeight: 240,
    },
    termsText: { fontSize: 13, lineHeight: 20 },
    acceptBtn: {
      borderRadius: theme.radius.lg,
      paddingVertical: 14,
      alignItems: "center",
    },
    guideStep: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      padding: theme.spacing.md,
      flexDirection: "row",
      gap: 12,
    },
    stepNum: {
      width: 28,
      height: 28,
      borderRadius: 14,
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
    },
    stepNumText: { fontSize: 12, fontWeight: "800" },
    divider: { height: 1 },
    modalOverlay: {
      flex: 1,
      backgroundColor: "rgba(0,0,0,0.55)",
      justifyContent: "flex-end",
    },
    modalSheet: {
      borderTopLeftRadius: 22,
      borderTopRightRadius: 22,
      padding: theme.spacing.lg,
      gap: 16,
    },
    modalTitle: { fontSize: theme.fontSize.lg, fontWeight: "800" },
    modalBtn: {
      borderRadius: theme.radius.lg,
      paddingVertical: 14,
      alignItems: "center",
    },
    verificationBanner: {
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      padding: theme.spacing.md,
      flexDirection: "row",
      alignItems: "flex-start",
      gap: 12,
    },
    verificationIcon: { fontSize: 24, lineHeight: 28 },
    selector: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 12,
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    typeList: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      overflow: "hidden",
      marginTop: 8,
    },
    typeOption: {
      paddingHorizontal: 12,
      paddingVertical: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: "rgba(0,0,0,0.08)",
    },
    docRow: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      padding: 12,
      gap: 10,
    },
    docMetaRow: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "flex-start",
      gap: 12,
    },
    docActionRow: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
    },
    secondaryBtn: {
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
      alignItems: "center",
      justifyContent: "center",
    },
    secondaryBtnText: {
      fontSize: theme.fontSize.sm,
      fontWeight: "700",
    },
  });

// ─────────────────────── Sub-components ─────────────────────────────────────

function InfoRow({ label, value, theme, styles }: {
  label: string;
  value?: string | null | number;
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  return (
    <View style={styles.row}>
      <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
      <Text style={[styles.value, { color: theme.colors.text }]} numberOfLines={2}>
        {value ?? "—"}
      </Text>
    </View>
  );
}

function VerificationChip({ status, theme, styles }: {
  status?: string | null;
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const chipColor =
    status === "approved" ? theme.colors.success :
    status === "rejected" ? theme.colors.danger :
    status === "pending" ? theme.colors.warning :
    theme.colors.textMuted;

  const label =
    status === "approved" ? "Approved" :
    status === "rejected" ? "Rejected" :
    status === "pending" ? "Pending Review" :
    "Not Submitted";

  return (
    <View style={[styles.chip, { borderColor: chipColor, backgroundColor: chipColor + "22" }]}>
      <Text style={[styles.chipText, { color: chipColor }]}>{label}</Text>
    </View>
  );
}

// ─────────────────────── Tabs ────────────────────────────────────────────────

function OverviewTab({ profile, theme, styles }: {
  profile: LogisticsPartnerProfile;
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const verificationStatus = profile.verification_status;
  const statusColor =
    verificationStatus === "approved" ? theme.colors.success :
    verificationStatus === "rejected" ? theme.colors.danger :
    verificationStatus === "pending" ? theme.colors.warning :
    theme.colors.textMuted;

  const icon =
    verificationStatus === "approved" ? "✓" :
    verificationStatus === "rejected" ? "✗" :
    verificationStatus === "pending" ? "⏳" :
    "○";

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      {/* Verification Banner */}
      <View style={[styles.verificationBanner, { borderColor: statusColor, backgroundColor: statusColor + "18" }]}>
        <Text style={[styles.verificationIcon, { color: statusColor }]}>{icon}</Text>
        <View style={{ flex: 1, gap: 4 }}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            Verification Status
          </Text>
          <VerificationChip status={verificationStatus} theme={theme} styles={styles} />
          {profile.verification_note ? (
            <Text style={{ fontSize: 13, color: theme.colors.textMuted, marginTop: 4 }}>
              {profile.verification_note}
            </Text>
          ) : null}
        </View>
      </View>

      {/* Identity */}
      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Identity</Text>
        <InfoRow label="Partner Name" value={profile.name} theme={theme} styles={styles} />
        <InfoRow label="Code" value={profile.code} theme={theme} styles={styles} />
        <InfoRow label="Business Type" value={profile.business_type} theme={theme} styles={styles} />
        <InfoRow label="Account Status" value={profile.status} theme={theme} styles={styles} />
      </View>

      {/* Contact */}
      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Contact</Text>
        <InfoRow label="Contact Name" value={profile.contact_name} theme={theme} styles={styles} />
        <InfoRow label="Email" value={profile.contact_email} theme={theme} styles={styles} />
        <InfoRow label="Phone" value={profile.contact_phone} theme={theme} styles={styles} />
        <InfoRow label="Website" value={profile.website} theme={theme} styles={styles} />
      </View>

      {/* Service Types */}
      {profile.service_types && profile.service_types.length > 0 && (
        <View style={styles.card}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Service Types</Text>
          <View style={styles.chipRow}>
            {profile.service_types.map((type) => (
              <View key={type} style={[styles.serviceChip, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand + "18" }]}>
                <Text style={[styles.serviceChipText, { color: theme.colors.brand }]}>
                  {SERVICE_TYPES.find((s) => s.id === type)?.label ?? type}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Terms */}
      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Terms</Text>
        <InfoRow
          label="Accepted"
          value={profile.is_terms_accepted ? `Yes (v${profile.terms_version ?? "—"})` : "Not accepted"}
          theme={theme}
          styles={styles}
        />
      </View>
    </ScrollView>
  );
}

function ProfileTab({ profile, onSaved, theme, styles }: {
  profile: LogisticsPartnerProfile;
  onSaved: (p: LogisticsPartnerProfile) => void;
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const [form, setForm] = useState({
    name: profile.name ?? "",
    contact_name: profile.contact_name ?? "",
    contact_email: profile.contact_email ?? "",
    contact_phone: profile.contact_phone ?? "",
    website: profile.website ?? "",
    business_type: profile.business_type ?? "",
    country: profile.country ?? "",
    region: profile.region ?? "",
    city: profile.city ?? "",
    address: profile.address ?? "",
    postal_code: profile.postal_code ?? "",
    tax_id: profile.tax_id ?? "",
    bio: profile.bio ?? "",
  });
  const [selectedServices, setSelectedServices] = useState<string[]>(profile.service_types ?? []);
  const [saving, setSaving] = useState(false);

  function toggleService(id: string) {
    setSelectedServices((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  }

  function update(key: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateLogisticsPartnerProfile({
        ...form,
        service_types: selectedServices,
      });
      onSaved(updated);
      Alert.alert("Saved", "Profile updated successfully.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save profile.";
      Alert.alert("Error", msg);
    } finally {
      setSaving(false);
    }
  }

  const Field = ({ label, field, multiline = false, keyboardType = "default" as "default" | "email-address" | "phone-pad" | "url" }: {
    label: string;
    field: keyof typeof form;
    multiline?: boolean;
    keyboardType?: "default" | "email-address" | "phone-pad" | "url";
  }) => (
    <View style={{ gap: 4 }}>
      <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>{label}</Text>
      <TextInput
        value={form[field]}
        onChangeText={(v) => update(field, v)}
        style={[
          styles.input,
          multiline && styles.textArea,
          { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 },
        ]}
        placeholderTextColor={theme.colors.textMuted}
        multiline={multiline}
        keyboardType={keyboardType}
      />
    </View>
  );

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Business Details</Text>
        <Field label="Company Name" field="name" />
        <Field label="Business Type" field="business_type" />
        <Field label="Tax ID" field="tax_id" />
        <Field label="About" field="bio" multiline />
      </View>

      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Contact Info</Text>
        <Field label="Contact Name" field="contact_name" />
        <Field label="Email" field="contact_email" keyboardType="email-address" />
        <Field label="Phone" field="contact_phone" keyboardType="phone-pad" />
        <Field label="Website" field="website" keyboardType="url" />
      </View>

      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Location</Text>
        <Field label="Country" field="country" />
        <Field label="Region" field="region" />
        <Field label="City" field="city" />
        <Field label="Address" field="address" />
        <Field label="Postal Code" field="postal_code" />
      </View>

      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Service Types</Text>
        <View style={styles.chipRow}>
          {SERVICE_TYPES.map((s) => {
            const active = selectedServices.includes(s.id);
            return (
              <TouchableOpacity
                key={s.id}
                onPress={() => toggleService(s.id)}
                style={[
                  styles.serviceChip,
                  {
                    borderColor: active ? theme.colors.brand : theme.colors.border,
                    backgroundColor: active ? theme.colors.brand + "22" : theme.colors.surface2,
                  },
                ]}
              >
                <Text style={[styles.serviceChipText, { color: active ? theme.colors.brand : theme.colors.textMuted }]}>
                  {s.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <TouchableOpacity
        onPress={handleSave}
        disabled={saving}
        style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]}
      >
        {saving ? (
          <ActivityIndicator color={theme.colors.onBrand} />
        ) : (
          <Text style={[styles.saveBtnText, { color: theme.colors.onBrand }]}>Save Profile</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

function CoverageTab({ theme, styles }: {
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const [areas, setAreas] = useState<LogisticsPartnerServiceArea[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newCountry, setNewCountry] = useState("");
  const [newCity, setNewCity] = useState("");
  const [newOriginCity, setNewOriginCity] = useState("");
  const [newCharge, setNewCharge] = useState("");
  const [adding, setAdding] = useState(false);

  const fetchAreas = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getLogisticsPartnerServiceAreas();
      setAreas(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAreas(); }, [fetchAreas]);

  async function handleAdd() {
    if (!newCountry.trim()) {
      Alert.alert("Required", "Please enter a country.");
      return;
    }
    setAdding(true);
    try {
      const area = await addLogisticsPartnerServiceArea({
        country: newCountry.trim(),
        city: newCity.trim() || null,
        origin_city: newOriginCity.trim() || null,
        charge: newCharge ? parseFloat(newCharge) : null,
        currency: "AED",
      });
      setAreas((prev) => [...prev, area]);
      setShowModal(false);
      setNewCountry("");
      setNewCity("");
      setNewOriginCity("");
      setNewCharge("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add area.";
      Alert.alert("Error", msg);
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: number) {
    Alert.alert("Remove Area", "Remove this coverage area?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: async () => {
          try {
            await removeLogisticsPartnerServiceArea(id);
            setAreas((prev) => prev.filter((a) => a.id !== id));
          } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to remove area.";
            Alert.alert("Error", msg);
          }
        },
      },
    ]);
  }

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            Service Areas ({areas.length})
          </Text>
        </View>
        {loading ? (
          <ActivityIndicator color={theme.colors.brand} />
        ) : areas.length === 0 ? (
          <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>No service areas added yet.</Text>
        ) : (
          areas.map((area) => (
            <View key={area.id} style={styles.areaCard}>
              <View style={{ gap: 2 }}>
                <Text style={{ fontSize: 14, fontWeight: "700", color: theme.colors.text }}>
                  {area.country}
                  {area.city ? ` → ${area.city}` : ""}
                </Text>
                {area.origin_city ? (
                  <Text style={{ fontSize: 12, color: theme.colors.textMuted }}>From: {area.origin_city}</Text>
                ) : null}
                {area.charge != null && (
                  <Text style={{ fontSize: 12, color: theme.colors.textMuted }}>
                    Charge: {area.currency ?? "AED"} {area.charge.toFixed(2)}
                  </Text>
                )}
              </View>
              <TouchableOpacity
                onPress={() => handleDelete(area.id)}
                style={[styles.deleteBtn, { borderColor: theme.colors.danger }]}
              >
                <Text style={{ fontSize: 12, fontWeight: "700", color: theme.colors.danger }}>Remove</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
        <TouchableOpacity
          onPress={() => setShowModal(true)}
          style={[styles.addBtn, { borderColor: theme.colors.brand }]}
        >
          <Text style={{ fontSize: 14, fontWeight: "700", color: theme.colors.brand }}>+ Add Area</Text>
        </TouchableOpacity>
      </View>

      {/* Add Area modal */}
      <Modal visible={showModal} transparent animationType="slide" onRequestClose={() => setShowModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { backgroundColor: theme.colors.surface1 }]}>
            <Text style={[styles.modalTitle, { color: theme.colors.text }]}>Add Coverage Area</Text>

            <View style={{ gap: 4 }}>
              <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Country *</Text>
              <TextInput
                value={newCountry}
                onChangeText={setNewCountry}
                placeholder="e.g. UAE"
                placeholderTextColor={theme.colors.textMuted}
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
              />
            </View>

            <View style={{ gap: 4 }}>
              <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Delivery City (optional)</Text>
              <TextInput
                value={newCity}
                onChangeText={setNewCity}
                placeholder="e.g. Dubai"
                placeholderTextColor={theme.colors.textMuted}
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
              />
            </View>

            <View style={{ gap: 4 }}>
              <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Pickup City (optional)</Text>
              <TextInput
                value={newOriginCity}
                onChangeText={setNewOriginCity}
                placeholder="e.g. Abu Dhabi"
                placeholderTextColor={theme.colors.textMuted}
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
              />
            </View>

            <View style={{ gap: 4 }}>
              <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Delivery Charge (AED)</Text>
              <TextInput
                value={newCharge}
                onChangeText={setNewCharge}
                placeholder="0.00"
                placeholderTextColor={theme.colors.textMuted}
                keyboardType="decimal-pad"
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
              />
            </View>

            <TouchableOpacity
              onPress={handleAdd}
              disabled={adding}
              style={[styles.modalBtn, { backgroundColor: theme.colors.brand }]}
            >
              {adding ? (
                <ActivityIndicator color={theme.colors.onBrand} />
              ) : (
                <Text style={{ fontSize: 15, fontWeight: "800", color: theme.colors.onBrand }}>Add</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setShowModal(false)} style={{ alignItems: "center", paddingVertical: 10 }}>
              <Text style={{ color: theme.colors.textMuted, fontWeight: "600" }}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

function TermsTab({ profile, onAccepted, theme, styles }: {
  profile: LogisticsPartnerProfile;
  onAccepted: () => void;
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const [accepting, setAccepting] = useState(false);
  const accepted = profile.is_terms_accepted === true;

  async function handleAccept() {
    setAccepting(true);
    try {
      await acceptLogisticsPartnerTerms();
      onAccepted();
      Alert.alert("Terms Accepted", "You have successfully accepted the Zozi Logistics Partner Agreement.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to accept terms.";
      Alert.alert("Error", msg);
    } finally {
      setAccepting(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      {accepted && (
        <View style={[styles.card, { borderColor: theme.colors.success, backgroundColor: theme.colors.success + "14" }]}>
          <Text style={{ fontSize: 14, fontWeight: "700", color: theme.colors.success }}>
            ✓ Terms Accepted
          </Text>
          <Text style={{ fontSize: 13, color: theme.colors.textMuted }}>
            Version: {profile.terms_version ?? "—"}
          </Text>
        </View>
      )}

      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Zozi Logistics Partner Agreement</Text>
        <ScrollView style={[styles.termsBox, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]} nestedScrollEnabled>
          <Text style={[styles.termsText, { color: theme.colors.text }]}>{TERMS_TEXT}</Text>
        </ScrollView>

        {!accepted && (
          <TouchableOpacity
            onPress={handleAccept}
            disabled={accepting}
            style={[styles.acceptBtn, { backgroundColor: theme.colors.brand }]}
          >
            {accepting ? (
              <ActivityIndicator color={theme.colors.onBrand} />
            ) : (
              <Text style={{ fontSize: 15, fontWeight: "800", color: theme.colors.onBrand }}>
                Accept Terms & Continue
              </Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
}

function GuideTab({ theme, styles }: { theme: AppTheme; styles: ReturnType<typeof createStyles> }) {
  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Getting Started Guide</Text>
        <Text style={{ fontSize: 13, color: theme.colors.textMuted }}>
          Follow these steps to get your logistics partner account fully active.
        </Text>
      </View>

      {GUIDE_STEPS.map((step, idx) => (
        <View key={idx} style={[styles.guideStep, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
          <View style={[styles.stepNum, { backgroundColor: theme.colors.brand }]}>
            <Text style={[styles.stepNumText, { color: theme.colors.onBrand }]}>{idx + 1}</Text>
          </View>
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={{ fontSize: 14, fontWeight: "700", color: theme.colors.text }}>{step.title}</Text>
            <Text style={{ fontSize: 13, color: theme.colors.textMuted, lineHeight: 18 }}>{step.detail}</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

// ─────────────────────── Security Tab ────────────────────────────────────────

function SecurityTab({ theme, styles, router }: {
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
  router: ReturnType<typeof useRouter>;
}) {
  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Password & Security</Text>
        <Text style={{ fontSize: 13, color: theme.colors.textMuted }}>
          Change your account password. You will need your current password to proceed.
        </Text>
        <TouchableOpacity
          onPress={() => router.push("/change-password" as never)}
          style={[styles.saveBtn, { backgroundColor: theme.colors.brand, marginTop: 8 }]}
        >
          <Text style={[styles.saveBtnText, { color: theme.colors.onBrand }]}>Change Password</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

// ─────────────────────── Banking Tab ─────────────────────────────────────────

function BankingTab({ theme, styles }: {
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const [account, setAccount] = useState<RecipientBankAccount | null>(null);
  const [form, setForm] = useState({
    beneficiary_name: "", bank_name: "", branch_name: "",
    account_number: "", iban: "", swift_code: "",
    routing_number: "", bank_country: "", currency: "AED",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getPartnerBankAccount()
      .then((data) => {
        setAccount(data);
        if (data?.id) {
          setForm({
            beneficiary_name: data.beneficiary_name || "",
            bank_name: data.bank_name || "",
            branch_name: data.branch_name || "",
            account_number: data.account_number || "",
            iban: data.iban || "",
            swift_code: data.swift_code || "",
            routing_number: data.routing_number || "",
            bank_country: data.bank_country || "",
            currency: data.currency || "AED",
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      const result = await upsertPartnerBankAccount(form);
      setAccount((prev) => ({ ...prev, ...form, configured: true, id: result.id, verification_status: result.verification_status as RecipientBankAccount["verification_status"] }));
      Alert.alert("Saved", "Bank account saved. Pending admin verification.");
    } catch (err: unknown) {
      Alert.alert("Error", err instanceof Error ? err.message : "Failed to save bank account.");
    } finally {
      setSaving(false);
    }
  }

  const statusColor =
    account?.verification_status === "verified" ? theme.colors.success :
    account?.verification_status === "rejected" ? theme.colors.danger :
    theme.colors.warning;

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator color={theme.colors.brand} />
      </View>
    );
  }

  const FIELDS: { key: keyof typeof form; label: string; placeholder: string }[] = [
    { key: "beneficiary_name", label: "Beneficiary Name", placeholder: "As shown on account" },
    { key: "bank_name", label: "Bank Name", placeholder: "e.g. First Abu Dhabi Bank" },
    { key: "branch_name", label: "Branch Name", placeholder: "e.g. Main Branch" },
    { key: "account_number", label: "Account Number", placeholder: "Account number" },
    { key: "iban", label: "IBAN", placeholder: "e.g. AE07 0331..." },
    { key: "swift_code", label: "SWIFT / BIC", placeholder: "e.g. FABEAEADXXX" },
    { key: "routing_number", label: "Routing Number", placeholder: "Optional" },
    { key: "bank_country", label: "Bank Country", placeholder: "e.g. UAE" },
    { key: "currency", label: "Currency", placeholder: "e.g. AED" },
  ];

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Payout Bank Account</Text>
          {account?.id ? (
            <View style={[styles.chip, { borderColor: statusColor, backgroundColor: statusColor + "22" }]}>
              <Text style={[styles.chipText, { color: statusColor }]}>{account.verification_status ?? "pending"}</Text>
            </View>
          ) : (
            <View style={[styles.chip, { borderColor: theme.colors.textFaint, backgroundColor: theme.colors.surface2 }]}>
              <Text style={[styles.chipText, { color: theme.colors.textMuted }]}>not configured</Text>
            </View>
          )}
        </View>
        {account?.verification_status === "rejected" && account.verification_note ? (
          <Text style={{ fontSize: 12, color: theme.colors.danger }}>Rejection reason: {account.verification_note}</Text>
        ) : null}
      </View>

      <View style={styles.card}>
        {FIELDS.map(({ key, label, placeholder }) => (
          <View key={key} style={{ gap: 4 }}>
            <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>{label}</Text>
            <TextInput
              value={form[key]}
              onChangeText={(text) => setForm((prev) => ({ ...prev, [key]: text }))}
              placeholder={placeholder}
              placeholderTextColor={theme.colors.textFaint}
              style={[styles.input, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2, color: theme.colors.text }]}
            />
          </View>
        ))}
        <TouchableOpacity
          onPress={handleSave}
          disabled={saving}
          style={[styles.saveBtn, { backgroundColor: theme.colors.brand, opacity: saving ? 0.6 : 1 }]}
        >
          <Text style={[styles.saveBtnText, { color: theme.colors.onBrand }]}>{saving ? "Saving..." : "Save Bank Account"}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

// ─────────────────────── Documents Tab ───────────────────────────────────────

function DocumentsTab({ theme, styles }: {
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
}) {
  const [documents, setDocuments] = useState<LogisticsPartnerDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [showTypePicker, setShowTypePicker] = useState(false);
  const [selectedType, setSelectedType] = useState(LP_DOC_TYPES[0].value);
  const [documentName, setDocumentName] = useState("");
  const [documentExpiry, setDocumentExpiry] = useState("");
  const [selectedFile, setSelectedFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);

  const selectedTypeLabel = useMemo(
    () => LP_DOC_TYPES.find((item) => item.value === selectedType)?.label ?? selectedType,
    [selectedType],
  );

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listLogisticsPartnerDocuments();
      setDocuments(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      Alert.alert("Error", err instanceof Error ? err.message : "Failed to load partner documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  async function chooseFile() {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["application/pdf", "image/*"],
        copyToCacheDirectory: true,
      });
      if (result.canceled || !result.assets?.length) return;
      const asset = result.assets[0];
      setSelectedFile(asset);
      if (!documentName.trim()) {
        setDocumentName((asset.name || "document").replace(/\.[^.]+$/, ""));
      }
    } catch (err: unknown) {
      Alert.alert("Error", err instanceof Error ? err.message : "Failed to choose file.");
    }
  }

  async function handleUpload() {
    if (!selectedFile) {
      Alert.alert("Required", "Choose a file before uploading.");
      return;
    }
    setUploading(true);
    try {
      await uploadLogisticsPartnerDocument({
        file: {
          uri: selectedFile.uri,
          name: selectedFile.name,
          mimeType: selectedFile.mimeType,
        },
        documentType: selectedType,
        documentName,
        expiresAt: documentExpiry.trim() || null,
      });
      setSelectedFile(null);
      setDocumentName("");
      setDocumentExpiry("");
      await fetchDocuments();
      Alert.alert("Uploaded", "Document uploaded and submitted for review.");
    } catch (err: unknown) {
      Alert.alert("Error", err instanceof Error ? err.message : "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    setDeletingId(id);
    try {
      await deleteLogisticsPartnerDocument(id);
      setDocuments((current) => current.filter((doc) => doc.id !== id));
    } catch (err: unknown) {
      Alert.alert("Error", err instanceof Error ? err.message : "Failed to delete document.");
    } finally {
      setDeletingId(null);
    }
  }

  function openDocument(url: string) {
    void Linking.openURL(url).catch(() => {
      Alert.alert("Unable to open", "This document link could not be opened on the device.");
    });
  }

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>KYC Documents</Text>
          <TouchableOpacity onPress={() => void fetchDocuments()} style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
            <Text style={[styles.secondaryBtnText, { color: theme.colors.textMuted }]}>Refresh</Text>
          </TouchableOpacity>
        </View>
        <Text style={{ fontSize: 13, color: theme.colors.textMuted }}>
          Upload and manage your compliance documents directly from mobile. Approved documents stay locked while pending or rejected ones can be replaced.
        </Text>

        <View style={{ gap: 8 }}>
          <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Document Type</Text>
          <TouchableOpacity
            onPress={() => setShowTypePicker((value) => !value)}
            style={[styles.selector, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
          >
            <Text style={{ color: theme.colors.text }}>{selectedTypeLabel}</Text>
            <Text style={{ color: theme.colors.textMuted }}>▾</Text>
          </TouchableOpacity>
          {showTypePicker ? (
            <View style={[styles.typeList, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
              {LP_DOC_TYPES.map((item) => (
                <TouchableOpacity
                  key={item.value}
                  onPress={() => {
                    setSelectedType(item.value);
                    setShowTypePicker(false);
                  }}
                  style={[styles.typeOption, selectedType === item.value && { backgroundColor: theme.colors.brand + "18" }]}
                >
                  <Text style={{ color: selectedType === item.value ? theme.colors.brand : theme.colors.text }}>{item.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          ) : null}
        </View>

        <View style={{ gap: 4 }}>
          <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Document Name</Text>
          <TextInput
            value={documentName}
            onChangeText={setDocumentName}
            placeholder="e.g. Trade License 2026"
            placeholderTextColor={theme.colors.textMuted}
            style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
          />
        </View>

        <View style={{ gap: 4 }}>
          <Text style={[styles.fieldLabel, { color: theme.colors.textMuted }]}>Expiry Date</Text>
          <TextInput
            value={documentExpiry}
            onChangeText={setDocumentExpiry}
            placeholder="YYYY-MM-DD"
            placeholderTextColor={theme.colors.textMuted}
            style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
          />
        </View>

        <TouchableOpacity onPress={chooseFile} style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
          <Text style={[styles.secondaryBtnText, { color: theme.colors.text }]}>
            {selectedFile ? `Choose File Again (${selectedFile.name || "selected"})` : "Choose File"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={handleUpload} disabled={!selectedFile || uploading} style={[styles.saveBtn, { backgroundColor: theme.colors.brand, opacity: !selectedFile || uploading ? 0.6 : 1 }]}> 
          {uploading ? <ActivityIndicator color={theme.colors.onBrand} /> : <Text style={[styles.saveBtnText, { color: theme.colors.onBrand }]}>Upload Document</Text>}
        </TouchableOpacity>

        <Text style={{ fontSize: 11, color: theme.colors.textFaint }}>
          Accepted file types: PDF, JPG, PNG, WEBP. Uploads are reviewed by admin before activation.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Submitted Documents</Text>
        {loading ? (
          <ActivityIndicator color={theme.colors.brand} />
        ) : documents.length === 0 ? (
          <Text style={{ fontSize: 13, color: theme.colors.textMuted }}>No documents uploaded yet.</Text>
        ) : (
          documents.map((doc) => {
            const colorKey = LP_DOC_STATUS_COLORS[doc.status] || "warning";
            const chipColor = theme.colors[colorKey];
            const canDelete = doc.status === "pending" || doc.status === "rejected";
            const label = LP_DOC_TYPES.find((item) => item.value === doc.document_type)?.label ?? doc.document_type;
            return (
              <View key={doc.id} style={[styles.docRow, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
                <View style={styles.docMetaRow}>
                  <View style={{ flex: 1, gap: 4 }}>
                    <Text style={{ fontSize: 14, fontWeight: "700", color: theme.colors.text }}>{doc.document_name || label}</Text>
                    <Text style={{ fontSize: 12, color: theme.colors.textMuted }}>{label}</Text>
                    {doc.expires_at ? <Text style={{ fontSize: 11, color: theme.colors.textFaint }}>Expires {new Date(doc.expires_at).toLocaleDateString()}</Text> : null}
                    {doc.review_note ? <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>Review note: {doc.review_note}</Text> : null}
                  </View>
                  <View style={[styles.chip, { borderColor: chipColor, backgroundColor: chipColor + "22" }]}>
                    <Text style={[styles.chipText, { color: chipColor }]}>{String(doc.status).replace(/_/g, " ")}</Text>
                  </View>
                </View>

                <View style={styles.docActionRow}>
                  {doc.file_url ? (
                    <TouchableOpacity onPress={() => openDocument(doc.file_url)} style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
                      <Text style={[styles.secondaryBtnText, { color: theme.colors.text }]}>Open</Text>
                    </TouchableOpacity>
                  ) : null}
                  {canDelete ? (
                    <TouchableOpacity
                      onPress={() => {
                        Alert.alert("Delete document", "Remove this document from your profile?", [
                          { text: "Cancel", style: "cancel" },
                          { text: "Delete", style: "destructive", onPress: () => void handleDelete(doc.id) },
                        ]);
                      }}
                      disabled={deletingId === doc.id}
                      style={[styles.secondaryBtn, { borderColor: theme.colors.danger, backgroundColor: theme.colors.danger + "14" }]}
                    >
                      <Text style={[styles.secondaryBtnText, { color: theme.colors.danger }]}>{deletingId === doc.id ? "Deleting..." : "Delete"}</Text>
                    </TouchableOpacity>
                  ) : null}
                </View>
              </View>
            );
          })
        )}
      </View>
    </ScrollView>
  );
}

// ─────────────────────── Screen ──────────────────────────────────────────────

export default function LogisticsPartnerProfileScreen(): React.ReactElement {
  const theme = useThemeStore((s) => s.theme);
  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);
  const router = useRouter();

  const styles = createStyles(theme);

  const [profile, setProfile] = useState<LogisticsPartnerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  const [screenTitle] = useTranslateTexts(["Partner Profile"]);

  const fetchProfile = useCallback(async () => {
    try {
      const data = await getLogisticsPartnerProfile();
      setProfile(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load profile.";
      Alert.alert("Error", msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  function handleRefresh() {
    setRefreshing(true);
    fetchProfile();
  }

  function handleAccepted() {
    if (profile) {
      setProfile({ ...profile, is_terms_accepted: true, terms_version: "1.0" });
    }
  }

  if (loading) {
    return (
      <View style={[styles.container, { alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: screenTitle, headerShown: true }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={[styles.container, { alignItems: "center", justifyContent: "center", gap: 16 }]}>
        <Stack.Screen options={{ title: screenTitle, headerShown: true }} />
        <Text style={{ color: theme.colors.textMuted, fontSize: 15 }}>Profile not found.</Text>
        <TouchableOpacity
          onPress={() => router.back()}
          style={{ paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12, backgroundColor: theme.colors.brand }}
        >
          <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { direction: isRtl ? "rtl" : "ltr" }]}>
      <Stack.Screen options={{ title: screenTitle, headerShown: true }} />

      {/* Tab bar */}
      <View style={styles.tabBar}>
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={styles.tabItem}
              onPress={() => setActiveTab(tab.key)}
            >
              <Ionicons name={tab.icon as any} size={16} color={active ? theme.colors.brand : theme.colors.textMuted} />
              <Text style={[styles.tabLabel, { color: active ? theme.colors.brand : theme.colors.textMuted }]}>
                {tab.label}
              </Text>
              {active && (
                <View style={[styles.tabIndicator, { backgroundColor: theme.colors.brand }]} />
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Tab content — wrap in ScrollView with RefreshControl for tabs that use it */}
      {activeTab === "overview" && (
        <View style={{ flex: 1 }}>
          <ScrollView
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
            contentContainerStyle={{ padding: 0 }}
          >
            <OverviewTab profile={profile} theme={theme} styles={styles} />
          </ScrollView>
        </View>
      )}
      {activeTab === "profile" && <ProfileTab profile={profile} onSaved={setProfile} theme={theme} styles={styles} />}
      {activeTab === "coverage" && <CoverageTab theme={theme} styles={styles} />}
      {activeTab === "security" && <SecurityTab theme={theme} styles={styles} router={router} />}
      {activeTab === "documents" && <DocumentsTab theme={theme} styles={styles} />}
      {activeTab === "banking" && <BankingTab theme={theme} styles={styles} />}
      {activeTab === "terms" && <TermsTab profile={profile} onAccepted={handleAccepted} theme={theme} styles={styles} />}
      {activeTab === "guide" && <GuideTab theme={theme} styles={styles} />}
    </View>
  );
}
