import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Alert,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

interface SupplierTermsStatus {
  is_terms_accepted?: boolean;
  terms_accepted_at?: string | null;
  terms_version?: string | null;
}

interface AcceptTermsResponse {
  terms_version?: string | null;
}

const TERMS_SECTIONS = [
  {
    title: "1. Eligibility",
    body: "You must be at least 18 years old and legally authorised to sell products in your jurisdiction. By registering as a ZOZI supplier, you confirm that you meet these requirements and that all information you provide is accurate and truthful.",
  },
  {
    title: "2. Product Listings",
    body: "All products listed must be authentic, accurately described, and compliant with applicable laws and regulations. Counterfeit, illegal, or dangerous goods are strictly prohibited and will result in immediate account suspension and potential legal action. ZOZI reserves the right to remove any product listing at its sole discretion.",
  },
  {
    title: "3. Pricing & Platform Commission",
    body: "ZOZI charges a platform commission on each completed sale. Commission rates are displayed in your supplier dashboard and may be updated with 30 days' written notice to the email address on your account. Pricing must be in AED unless otherwise agreed.",
  },
  {
    title: "4. Order Fulfilment",
    body: "Suppliers are solely responsible for fulfilling orders within their stated lead times. Products must be dispatched in appropriate packaging. Repeated fulfilment failures may result in penalties, account suspension, or termination.",
  },
  {
    title: "5. Returns & Refunds",
    body: "Suppliers must honour ZOZI's customer return and refund policy for all orders placed through the platform. Suppliers are responsible for return shipping costs when a return is due to supplier error. ZOZI may deduct the cost of refunds from future payouts where the supplier is at fault.",
  },
  {
    title: "6. Payouts",
    body: "Payouts are processed on a rolling schedule, typically every 14 days, after the commission has been deducted. ZOZI reserves the right to withhold payouts pending investigation of disputes, fraud, or policy violations. Minimum payout threshold is AED 50.",
  },
  {
    title: "7. Data & Privacy",
    body: "Customer personal data obtained through ZOZI may only be used to fulfil the specific order for which it was provided. You must not use customer data for unsolicited marketing, data brokering, or any third-party sharing.",
  },
  {
    title: "8. Intellectual Property",
    body: "By uploading product images and descriptions to ZOZI, you grant ZOZI a non-exclusive, royalty-free licence to use this content for the purpose of marketing and displaying your products on the platform.",
  },
  {
    title: "9. Prohibited Conduct",
    body: "Suppliers must not attempt to circumvent the platform, conduct off-platform transactions, manipulate reviews or ratings, or engage in any form of fraudulent activity. Violations will result in immediate account termination without payout.",
  },
  {
    title: "10. Account Termination",
    body: "ZOZI reserves the right to suspend or permanently terminate supplier accounts that violate these terms, with or without prior notice. Suppliers may terminate their account by contacting support, subject to settlement of all outstanding obligations.",
  },
  {
    title: "11. Changes to Terms",
    body: "ZOZI may update these terms at any time. Suppliers will be notified via email and dashboard notification at least 14 days before changes take effect. Continued use of the platform after the effective date constitutes acceptance of the updated terms.",
  },
];

export default function SupplierTermsScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const styles = makeStyles(theme);

  const [loading, setLoading] = useState(true);
  const [accepted, setAccepted] = useState(false);
  const [acceptedAt, setAcceptedAt] = useState<string | null>(null);
  const [termsVersion, setTermsVersion] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);

  useEffect(() => {
    apiFetch<SupplierTermsStatus>("/supplier/profile/business")
      .then((d) => {
        if (d) {
          setAccepted(!!d.is_terms_accepted);
          setAcceptedAt(d.terms_accepted_at ?? null);
          setTermsVersion(d.terms_version ?? null);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      const d = await apiFetch<AcceptTermsResponse>("/supplier/terms/accept", { method: "POST" });
      setAccepted(true);
      setTermsVersion(d.terms_version ?? "1.0");
      setAcceptedAt(new Date().toISOString());
      Alert.alert("Accepted", "Terms & Conditions accepted successfully.");
    } catch {
      Alert.alert("Error", "Network error. Please try again.");
    } finally {
      setAccepting(false);
    }
  };

  if (loading) {
    return (
      <>
        <Stack.Screen options={{ title: "Terms & Conditions" }} />
        <View style={[styles.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
          <ActivityIndicator color={theme.colors.brand} size="large" />
        </View>
      </>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: "Terms & Conditions" }} />
      <ScrollView style={[styles.container, { flex: 1 }]} contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40 }}>
        {/* Status banner */}
        <View
          style={[
            localStyles.banner,
            {
              backgroundColor: accepted ? theme.colors.success + "20" : "#f59e0b20",
              borderColor: accepted ? theme.colors.success : "#f59e0b",
            },
          ]}
        >
          <Text
            style={{
              color: accepted ? theme.colors.success : "#f59e0b",
              fontWeight: "700",
              fontSize: theme.fontSize.sm,
            }}
          >
            {accepted
              ? `✔ Accepted — v${termsVersion ?? "1.0"} · ${
                  acceptedAt ? new Date(acceptedAt).toLocaleDateString() : ""
                }`
              : "⚠ You have not yet accepted the Terms & Conditions"}
          </Text>
        </View>

        {/* Document header */}
        <View style={[localStyles.docHeader, { borderBottomColor: theme.colors.border }]}>
          <Text style={[styles.text, { fontSize: theme.fontSize.md, fontWeight: "700" }]}>
            ZOZI Supplier Terms & Conditions
          </Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 2 }}>
            Version 1.0 · Effective January 2025
          </Text>
        </View>

        {/* T&C sections */}
        {TERMS_SECTIONS.map((section) => (
          <View key={section.title} style={{ marginBottom: theme.spacing.md }}>
            <Text style={[styles.text, { fontWeight: "700", marginBottom: theme.spacing.xs }]}>{section.title}</Text>
            <Text style={{ color: theme.colors.textMuted, lineHeight: 20, fontSize: theme.fontSize.sm }}>{section.body}</Text>
          </View>
        ))}

        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginBottom: theme.spacing.lg }}>
          For questions about these terms, contact us at supplier-support@zozi.com
        </Text>

        {/* Accept button — only shown if not yet accepted */}
        {!accepted && (
          <TouchableOpacity
            style={[
              localStyles.acceptBtn,
              { backgroundColor: theme.colors.brand },
              accepting && { opacity: 0.6 },
            ]}
            onPress={handleAccept}
            disabled={accepting}
          >
            {accepting ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.base }}>
                I Accept these Terms & Conditions
              </Text>
            )}
          </TouchableOpacity>
        )}
        {!accepted && (
          <Text style={{ textAlign: "center", color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: theme.spacing.sm }}>
            By tapping above you confirm you have read and agree to all terms above.
          </Text>
        )}
      </ScrollView>
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  banner: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: theme.spacing.md,
  },
  docHeader: {
    paddingBottom: 12,
    marginBottom: theme.spacing.md,
    borderBottomWidth: 1,
  },
  acceptBtn: {
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.lg,
    alignItems: "center",
    justifyContent: "center",
  },
});
