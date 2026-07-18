import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Linking,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

const FAQ = [
  {
    q: "Where is supplier onboarding now?",
    a: "Profile is the new control center. Account, business details, storefront content, KYC documents, coverage, terms, and the guide all live together there.",
  },
  {
    q: "How should I upload products now?",
    a: "Use Product Management. It is the main place for product creation, gallery photos, AI-assisted category suggestions, sizes, and listing updates.",
  },
  {
    q: "When does an order become Prepared?",
    a: "After the supplier packs the parcel and uploads parcel proof, the order enters the prepared stage. It only becomes shipped once logistics receives the parcel.",
  },
  {
    q: "Where do invoices and logistics go now?",
    a: "Invoices stay accessible from Orders, while Logistics remains a secondary workspace for shipment assignment and carrier details.",
  },
  {
    q: "How do products reach customer surfaces?",
    a: "Active supplier listings with clean media and size data flow into supplier pages, customer detail pages, and public search results together.",
  },
];

const SETUP_STEPS = [
  "Review Account, Business & Location details",
  "Upload KYC documents and coverage settings",
  "Accept Supplier Terms & Conditions",
  "Create your first product with gallery photos and sizes",
  "Learn the Prepared to Shipped handoff flow",
  "Check Reports and Payouts before launch",
];

const GUIDE_SECTIONS = [
  {
    title: "Profile is now the supplier workspace",
    body: "Use the Profile action strip to move between account details, business location, storefront content, security, payout visibility, KYC documents, coverage, terms, and the guide.",
  },
  {
    title: "Product Management owns listing creation",
    body: "Create products with a main image, extra gallery photos, AI-assisted category suggestions, color, and clean size entries so supplier and customer views stay aligned.",
  },
  {
    title: "Orders now manage the packing handoff",
    body: "Parcel proof belongs in Orders. Upload the packed parcel photo there, move the order into Prepared, and let logistics receipt move the shipment into Shipped.",
  },
  {
    title: "Coverage controls discovery",
    body: "Operating regions decide where customers can find your storefront and products. Keep coverage current whenever your fulfillment footprint changes.",
  },
  {
    title: "Reports and Payouts should be read together",
    body: "Reports explain performance, and Payouts shows what is available after fees and release rules. Use both before changing pricing or inventory decisions.",
  },
];

const ACTION_CARDS = [
  { label: "Business Profile", description: "Complete storefront, coverage, and supplier identity details.", route: "/supplier/profile", icon: "business-outline", tone: "info" },
  { label: "KYC Documents", description: "Upload licenses, IDs, and certificates with review visibility.", route: "/supplier/documents", icon: "document-text-outline", tone: "warning" },
  { label: "Product Management", description: "Launch or update listings with media, sizes, and pricing.", route: "/supplier/products", icon: "pricetags-outline", tone: "success" },
  { label: "Orders Workspace", description: "Handle prepared-to-shipped handoff and parcel proof from one place.", route: "/supplier/orders", icon: "cube-outline", tone: "shipped" },
  { label: "Payouts & Reports", description: "Review cash release timing before you change inventory or pricing.", route: "/supplier/payouts", icon: "wallet-outline", tone: "danger" },
];

export default function SupplierGuideScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const styles = makeStyles(theme);
  const router = useRouter();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const TONE_COLORS: Record<string, string> = {
    info: theme.colors.info,
    warning: theme.colors.warning,
    success: theme.colors.success,
    shipped: theme.colors.statusShipped,
    danger: theme.colors.danger,
  };

  return (
    <>
      <Stack.Screen options={{ title: "Supplier Guide" }} />
      <ScrollView style={[styles.container, { flex: 1 }]} contentContainerStyle={{ padding: theme.spacing.md }}>
        {/* Header */}
        <Text style={[styles.text, localStyles.heading]}>Welcome to ZOZI Supplier</Text>
        <Text style={[styles.text, localStyles.subheading]}>
          Follow this guide to get your store set up and start selling.
        </Text>

        <View style={[localStyles.launchCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={localStyles.launchHeader}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.text, localStyles.launchEyebrow, { color: theme.colors.brand }]}>Launch Sequence</Text>
              <Text style={[styles.text, localStyles.launchTitle]}>Profile, compliance, catalog, then fulfillment.</Text>
              <Text style={[styles.text, { color: theme.colors.textMuted }]}>The mobile supplier flow is strongest when you treat Profile as the control plane and Orders as the shipment handoff workspace.</Text>
            </View>
            <View style={[localStyles.launchBadge, { backgroundColor: theme.colors.brand + "18" }]}>
              <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: theme.fontSize.xs }}>6-step setup</Text>
            </View>
          </View>
          <View style={localStyles.launchMetrics}>
            {[
              { label: "Core Stations", value: "5" },
              { label: "Required Docs", value: "3+" },
              { label: "Launch Risks", value: "KYC / Coverage" },
            ].map((metric) => (
              <View key={metric.label} style={[localStyles.metricCard, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                <Text style={[styles.text, localStyles.metricValue]}>{metric.value}</Text>
                <Text style={[styles.text, { color: theme.colors.textMuted, fontSize: theme.fontSize.xs }]}>{metric.label}</Text>
              </View>
            ))}
          </View>
        </View>

        <Text style={[styles.text, localStyles.sectionTitle]}>Run Your Supplier Workspace</Text>
        <View style={localStyles.actionGrid}>
          {ACTION_CARDS.map((card) => {
            const toneColor = TONE_COLORS[card.tone];
            return (
            <TouchableOpacity
              key={card.label}
              activeOpacity={0.85}
              onPress={() => router.push(card.route as never)}
              style={[localStyles.actionCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
            >
              <View style={[localStyles.actionIcon, { backgroundColor: toneColor + "1b" }]}>
                <Ionicons name={card.icon as any} size={18} color={toneColor} />
              </View>
              <Text style={[styles.text, { fontWeight: "700" }]}>{card.label}</Text>
              <Text style={[styles.text, { color: theme.colors.textMuted, fontSize: theme.fontSize.sm }]}>{card.description}</Text>
            </TouchableOpacity>
            );
          })}
        </View>

        {/* Setup Checklist */}
        <Text style={[styles.text, localStyles.sectionTitle]}>Getting Started Checklist</Text>
        {SETUP_STEPS.map((step, i) => (
          <View key={i} style={[localStyles.checkItem, { borderColor: theme.colors.border }]}>
            <View style={[localStyles.stepNum, { backgroundColor: theme.colors.brand }]}>
              <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>{i + 1}</Text>
            </View>
            <Text style={[styles.text, { flex: 1, marginLeft: 12 }]}>{step}</Text>
          </View>
        ))}

        {/* Tips */}
        <Text style={[styles.text, localStyles.sectionTitle]}>Tips for Success</Text>
        {[
          "Use a strong main product photo first. AI suggestions are better when the hero image is clear.",
          "Keep KYC, coverage, and terms current inside Profile so approval work does not stall later.",
          "Enter sizes as a structured list instead of freeform prose so customers can actually select them.",
          "Treat parcel proof as the handoff trigger. Prepared should come before Shipped.",
          "Review Reports and Payouts together before changing pricing or stock strategy.",
        ].map((tip, i) => (
          <View key={i} style={localStyles.tipRow}>
            <Text style={{ color: theme.colors.brand, marginRight: theme.spacing.sm, fontSize: theme.fontSize.md }}>•</Text>
            <Text style={[styles.text, { flex: 1 }]}>{tip}</Text>
          </View>
        ))}

        <Text style={[styles.text, localStyles.sectionTitle]}>How the New System Works</Text>
        {GUIDE_SECTIONS.map((section, index) => (
          <View key={index} style={[localStyles.faqCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
            <Text style={[styles.text, { fontWeight: "700", marginBottom: theme.spacing.xs }]}>{section.title}</Text>
            <Text style={[styles.text, { color: theme.colors.textMuted }]}>{section.body}</Text>
          </View>
        ))}

        {/* FAQ */}
        <Text style={[styles.text, localStyles.sectionTitle]}>Frequently Asked Questions</Text>
        {FAQ.map((faq, i) => (
          <TouchableOpacity
            key={i}
            style={[localStyles.faqCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
            onPress={() => setOpenFaq(openFaq === i ? null : i)}
          >
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Text style={[styles.text, { fontWeight: "600", flex: 1, marginRight: theme.spacing.sm }]}>{faq.q}</Text>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.md }}>{openFaq === i ? "−" : "+"}</Text>
            </View>
            {openFaq === i && (
              <Text style={[styles.text, { marginTop: theme.spacing.sm, color: theme.colors.textMuted }]}>{faq.a}</Text>
            )}
          </TouchableOpacity>
        ))}

        {/* Support */}
        <View style={[localStyles.supportBox, { backgroundColor: theme.colors.brand + "15", borderColor: theme.colors.brand }]}>
          <Text style={[styles.text, { fontWeight: "700", marginBottom: theme.spacing.xs }]}>Need more help?</Text>
          <TouchableOpacity onPress={() => Linking.openURL("mailto:suppliers@zozi.app")}>
            <Text style={{ color: theme.colors.brand }}>Contact supplier support: suppliers@zozi.app</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  heading: { fontSize: theme.fontSize.xl, fontWeight: "700", marginBottom: theme.spacing.xs },
  subheading: { fontSize: theme.fontSize.base, marginBottom: 20, opacity: 0.6 },
  sectionTitle: { fontSize: theme.fontSize.md, fontWeight: "700", marginTop: theme.spacing.lg, marginBottom: 12 },
  launchCard: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: 12,
    marginBottom: theme.spacing.sm,
  },
  launchHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 10,
  },
  launchEyebrow: {
    fontSize: theme.fontSize.xs,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  launchTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: "800",
    marginBottom: 4,
  },
  launchBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  launchMetrics: {
    flexDirection: "row",
    gap: 8,
  },
  metricCard: {
    flex: 1,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    padding: 10,
    gap: 2,
  },
  metricValue: {
    fontSize: theme.fontSize.md,
    fontWeight: "800",
  },
  actionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  actionCard: {
    width: "48%",
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: 12,
    gap: 8,
  },
  actionIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  checkItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  stepNum: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
  },
  tipRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: theme.spacing.sm,
  },
  faqCard: {
    borderWidth: 1,
    borderRadius: theme.radius.md,
    padding: 12,
    marginBottom: theme.spacing.sm,
  },
  supportBox: {
    borderWidth: 1,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.xl,
  },
});
