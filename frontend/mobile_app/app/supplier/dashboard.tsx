/**
 * Supplier Dashboard — React Native (Enhanced)
 * Adds: onboarding checklist, stock alerts — matching web_app supplier/dashboard/page.tsx
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles } from "@/theme";
import { Button } from "@/components/ui/Button";
import GradientHero from "@/components/ui/GradientHero";
import { StatCard } from "@/components/ui/StatCard";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { isRtlLocale } from "@shared/localization";
import { Ionicons } from "@expo/vector-icons";

interface DashboardStats {
  total_revenue: number;
  total_orders: number;
  total_products: number;
  pending_orders: number;
}

interface StockAlert {
  type: "low_stock" | "out_of_stock" | "overstock";
  product_id: number;
  product_name: string;
  current_stock: number;
  message: string;
}

interface OnboardingStatus {
  profile_complete: boolean;
  terms_accepted: boolean;
  first_product_uploaded: boolean;
  products_count: number;
  verification_status: string;
}

interface SupplierBadgeSnapshot {
  credibility_score: number;
  badge_level: string;
  eligible_badge_level?: string | null;
}

function formatBadgeLabel(value?: string | null): string {
  const normalized = String(value || "none").trim().toLowerCase();
  if (!normalized || normalized === "none") return "No badge";
  return normalized
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function SupplierDashboard() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const formatPrice = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [
    supplierDashboardTitle,
    logoutLabel,
    welcomeBackLabel,
    supplierFallbackLabel,
    storePerformanceLabel,
    revenueLabel,
    ordersLabel,
    productsLabel,
    pendingLabel,
    productManagementLabel,
    productManagementDescriptionLabel,
    ordersDescriptionLabel,
    reportsLabel,
    reportsDescriptionLabel,
    payoutsLabel,
    payoutsDescriptionLabel,
    returnsLabel,
    returnsDescriptionLabel,
    credibilityLabel,
    credibilityDescriptionLabel,
    profileLabel,
    profileDescriptionLabel,
    accountCreatedLabel,
    welcomeToZoziLabel,
    completeBusinessProfileLabel,
    businessProfileDescriptionLabel,
    acceptTermsLabel,
    termsDescriptionLabel,
    uploadFirstProductLabel,
    firstProductDescriptionLabel,
    gettingStartedLabel,
    gettingStartedDescriptionLabel,
    goLabel,
    stockAlertsLabel,
    leftLabel,
    viewAllLabel,
    alertsLabel,
    quickActionsLabel,
    openProductManagementLabel,
    manageLabel,
    supportLabel,
    supportDescriptionLabel,
    notificationPreferencesLabel,
    notificationPreferencesDescriptionLabel,
    credibilitySnapshotLabel,
    trustScoreLabel,
    currentBadgeLabel,
    eligibleNextLabel,
    openCredibilityLabel,
  ] = useTranslateTexts([
    "Supplier Dashboard",
    "Logout",
    "Welcome back",
    "Supplier",
    "Here's how your store is performing",
    "Revenue",
    "Orders",
    "Products",
    "Pending",
    "Product Management",
    "Catalog, stock and upload tools",
    "Orders, invoices and tracking",
    "Reports",
    "Analytics, trends and exports",
    "Payouts",
    "Earnings & payment history",
    "Returns",
    "Approve returns & restock",
    "Credibility",
    "Trust score & badge level",
    "Profile",
    "Business, KYC and supplier guide",
    "Account Created",
    "Welcome to ZOZI!",
    "Complete Business Profile",
    "Add location, tax info, and bio",
    "Accept Terms & Conditions",
    "Review the supplier agreement",
    "Upload Your First Product",
    "Start selling on ZOZI",
    "Getting Started",
    "Complete these steps to start selling on ZOZI",
    "Go",
    "Stock Alerts",
    "left",
    "View all",
    "alerts",
    "Quick Actions",
    "Open Product Management",
    "Manage",
    "Support",
    "Tickets, disputes and operational follow-up",
    "Notification Preferences",
    "Delivery channels and alert settings",
    "Credibility Snapshot",
    "Trust Score",
    "Current Badge",
    "Eligible Next",
    "Open Credibility",
  ]);

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [alerts, setAlerts] = useState<StockAlert[]>([]);
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [badge, setBadge] = useState<SupplierBadgeSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function loadAll() {
    try {
      const [statsData, alertsData, ob, badgeData] = await Promise.all([
        apiFetch<DashboardStats>("/supplier/analytics/summary").catch(() => null),
        apiFetch<{ alerts: StockAlert[] }>("/supplier/inventory/alerts")
          .catch(() => ({ alerts: [] })),
        apiFetch<OnboardingStatus>("/supplier/onboarding/status").catch(() => null),
        apiFetch<SupplierBadgeSnapshot>("/supplier/badge").catch(() => null),
      ]);
      if (statsData) setStats(statsData);
      setAlerts((alertsData as any)?.alerts ?? []);
      setOnboarding(ob as OnboardingStatus | null);
      setBadge(badgeData as SupplierBadgeSnapshot | null);
    } catch {
      /* non-critical */
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadAll(); }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadAll();
  }, []);

  const menuItems: { label: string; route: string; description: string }[] = [
    { label: productManagementLabel, route: "/supplier/products", description: productManagementDescriptionLabel },
    { label: ordersLabel, route: "/supplier/orders", description: ordersDescriptionLabel },
    { label: reportsLabel, route: "/supplier/reports", description: reportsDescriptionLabel },
    { label: payoutsLabel, route: "/supplier/payouts", description: payoutsDescriptionLabel },
    { label: returnsLabel, route: "/supplier/returns", description: returnsDescriptionLabel },
    { label: credibilityLabel, route: "/supplier/credibility", description: credibilityDescriptionLabel },
    { label: profileLabel, route: "/supplier/profile", description: profileDescriptionLabel },
    { label: supportLabel, route: "/supplier/support", description: supportDescriptionLabel },
    { label: notificationPreferencesLabel, route: "/supplier/notification-preferences", description: notificationPreferencesDescriptionLabel },
  ];

  const quickActions: { label: string; icon: string; route: string }[] = [
    { label: openProductManagementLabel, icon: "add-circle-outline", route: "/supplier/products" },
    { label: ordersLabel, icon: "cube-outline", route: "/supplier/orders" },
    { label: payoutsLabel, icon: "wallet-outline", route: "/supplier/payouts" },
    { label: reportsLabel, icon: "bar-chart-outline", route: "/supplier/reports" },
  ];

  const onboardingSteps = onboarding
    ? [
        { done: true, label: accountCreatedLabel, desc: welcomeToZoziLabel },
        { done: onboarding.profile_complete, label: completeBusinessProfileLabel, desc: businessProfileDescriptionLabel, route: "/supplier/profile" },
        { done: onboarding.terms_accepted, label: acceptTermsLabel, desc: termsDescriptionLabel, route: "/supplier/profile" },
        { done: onboarding.first_product_uploaded, label: uploadFirstProductLabel, desc: firstProductDescriptionLabel, route: "/supplier/products" },
      ]
    : [];

  const showOnboarding =
    onboarding &&
    !(onboarding.profile_complete && onboarding.terms_accepted && onboarding.first_product_uploaded);

  const alertTypeColor: Record<StockAlert["type"], string> = {
    out_of_stock: theme.colors.danger,
    low_stock: theme.colors.warning,
    overstock: theme.colors.info,
  };

  return (
    <ScrollView
      testID="supplier-dashboard-screen"
      style={[s.container, isRtl ? { direction: "rtl" } : undefined]}
      contentContainerStyle={styles.scroll}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />
      }
    >
      <Stack.Screen
        options={{
          title: supplierDashboardTitle,
          headerRight: () => (
            <TouchableOpacity onPress={logout} style={{ marginRight: 12 }}>
              <Text style={{ color: "#fff", fontWeight: "600" }}>{logoutLabel}</Text>
            </TouchableOpacity>
          ),
        }}
      />

      {/* Welcome */}
      <GradientHero colors={[theme.colors.brand, theme.colors.brandDark ?? theme.colors.brand]}>
        <View style={{ flexDirection: isRtl ? "row-reverse" : "row", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <View style={{ flex: 1 }}>
            <Text style={{ color: "#fff", fontSize: 18, fontWeight: "800" }}>
              {welcomeBackLabel}, {user?.username?.split(" ")[0] ?? supplierFallbackLabel} 👋
            </Text>
            <Text style={{ color: "rgba(255,255,255,0.85)", fontSize: 13, marginTop: 2 }}>{storePerformanceLabel}</Text>
          </View>
          <Ionicons name="storefront-outline" size={34} color="#fff" />
        </View>
      </GradientHero>

      {/* Stats */}
       {loading ? (
         <ActivityIndicator color={theme.colors.brand} size="large" />
       ) : (
         <View style={{ gap: 10 }}>
           <View style={[s.row, { gap: 10 }]}>
             <StatCard label={revenueLabel} value={formatPrice(stats?.total_revenue ?? 0)} icon="wallet-outline" gradient={[theme.colors.brand, theme.colors.brandDark ?? theme.colors.brand]} />
             <StatCard label={ordersLabel} value={stats?.total_orders ?? 0} icon="cube-outline" color={theme.colors.info} />
           </View>
           <View style={[s.row, { gap: 10 }]}>
             <StatCard label={productsLabel} value={stats?.total_products ?? 0} icon="grid-outline" color={theme.colors.success} />
             <StatCard label={pendingLabel} value={stats?.pending_orders ?? 0} icon="hourglass-outline" color={theme.colors.warning} />
           </View>
         </View>
       )}

      {badge && !loading && (
        <View
          style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
        >
          <View style={{ flexDirection: isRtl ? "row-reverse" : "row", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
            <View style={{ flex: 1, gap: 4 }}>
              <Text style={[s.text, { fontWeight: "800", fontSize: 14 }]}>{credibilitySnapshotLabel}</Text>
              <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: 18 }}>
                {formatBadgeLabel(badge.badge_level)}
              </Text>
              <Text style={s.textMuted}>{trustScoreLabel}: {badge.credibility_score}/100</Text>
            </View>
            <TouchableOpacity
              testID="supplier-dashboard-open-credibility"
              onPress={() => router.push("/supplier/credibility" as never)}
              style={{ borderWidth: 1, borderColor: theme.colors.border, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 8 }}
            >
              <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: 12 }}>{openCredibilityLabel}</Text>
            </TouchableOpacity>
          </View>
          <View style={[s.row, { gap: 10 }]}> 
              <StatCard label={currentBadgeLabel} value={formatBadgeLabel(badge.badge_level)} color={theme.colors.brand} />
              <StatCard label={eligibleNextLabel} value={formatBadgeLabel(badge.eligible_badge_level)} color={theme.colors.info} />
          </View>
        </View>
      )}

      {/* Onboarding checklist */}
      {showOnboarding && (
        <View
          style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.brand + "40" }]}
        >
          <Text style={[s.text, { fontWeight: "800", fontSize: 14, marginBottom: 4 }]}>
            🚀 {gettingStartedLabel}
          </Text>
          <Text style={[s.textMuted, { fontSize: 12, marginBottom: 10 }]}>
            {gettingStartedDescriptionLabel}
          </Text>
          {onboardingSteps.map((step, i) => (
            <View
              key={i}
              style={{
                flexDirection: isRtl ? "row-reverse" : "row",
                alignItems: "flex-start",
                gap: 10,
                paddingVertical: 8,
                borderTopWidth: i > 0 ? 1 : 0,
                borderColor: theme.colors.border,
              }}
            >
              <Ionicons
                name={step.done ? "checkmark-circle" : "ellipse-outline"}
                size={16}
                color={step.done ? theme.colors.brand : theme.colors.textMuted}
              />
              <View style={{ flex: 1 }}>
                <Text
                  style={[
                    s.text,
                    {
                      fontWeight: "600",
                      fontSize: 13,
                      textDecorationLine: step.done ? "line-through" : "none",
                      color: step.done ? theme.colors.textMuted : theme.colors.text,
                    },
                  ]}
                >
                  {step.label}
                </Text>
                <Text style={[s.textMuted, { fontSize: 11 }]}>{step.desc}</Text>
              </View>
              {!step.done && (step as any).route && (
                <TouchableOpacity onPress={() => router.push((step as any).route as never)}>
                  <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: 12 }}>
                    {goLabel} {isRtl ? "←" : "→"}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Stock alerts */}
      {alerts.length > 0 && (
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.warning + "40" }]}>
          <View style={{ flexDirection: isRtl ? "row-reverse" : "row", alignItems: "center", gap: 6, marginBottom: 10 }}>
            <Ionicons name="alert-circle" size={16} color={theme.colors.textMuted} />
            <Text style={[s.text, { fontWeight: "800", fontSize: 14, flex: 1 }]}>{stockAlertsLabel}</Text>
            <View
              style={{ backgroundColor: theme.colors.warning + "22", borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2 }}
            >
              <Text style={{ color: theme.colors.warning, fontWeight: "700", fontSize: 11 }}>{alerts.length}</Text>
            </View>
          </View>
          {alerts.slice(0, 5).map((a) => (
            <View
              key={a.product_id}
              style={{
                flexDirection: isRtl ? "row-reverse" : "row",
                alignItems: "center",
                justifyContent: "space-between",
                paddingVertical: 8,
                borderTopWidth: 1,
                borderColor: theme.colors.border,
              }}
            >
              <View style={{ flexDirection: isRtl ? "row-reverse" : "row", alignItems: "center", gap: 8, flex: 1 }}>
                <View
                  style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: alertTypeColor[a.type] }}
                />
                <Text style={[s.text, { fontSize: 13, fontWeight: "600" }]} numberOfLines={1}>
                  {a.product_name}
                </Text>
              </View>
              <View
                style={{
                  backgroundColor: alertTypeColor[a.type] + "22",
                  borderRadius: 6,
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                }}
              >
                <Text style={{ color: alertTypeColor[a.type], fontSize: 11, fontWeight: "700" }}>
                  {a.current_stock} {leftLabel}
                </Text>
              </View>
            </View>
          ))}
          {alerts.length > 5 && (
            <TouchableOpacity
              onPress={() => router.push("/supplier/products" as never)}
              style={{ marginTop: 8 }}
            >
              <Text style={{ color: theme.colors.brand, fontSize: 12, fontWeight: "700", textAlign: "center" }}>
                {viewAllLabel} {alerts.length} {alertsLabel} {isRtl ? "←" : "→"}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Quick Actions */}
      <SectionHeader title={quickActionsLabel} icon="flash-outline" />
      <View style={styles.quickGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.route}
            onPress={() => router.push(action.route as never)}
            activeOpacity={0.8}
            style={[styles.quickCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
          >
            <View style={[styles.quickIcon, { backgroundColor: theme.colors.brand + "18" }]}>
              <Ionicons name={action.icon as any} size={18} color={theme.colors.brand} />
            </View>
            <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]} numberOfLines={1}>{action.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Button
        testID="supplier-dashboard-open-products"
        label={openProductManagementLabel}
        onPress={() => router.push("/supplier/products" as never)}
        style={{ borderRadius: theme.radius.lg }}
      />

      {/* Menu */}
      <SectionHeader title={manageLabel} icon="list-outline" />
      {menuItems.map((item) => (
        <TouchableOpacity
          key={item.route}
          onPress={() => router.push(item.route as never)}
          style={[styles.menuItem, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
          activeOpacity={0.7}
        >
          <View style={{ flex: 1 }}>
            <Text style={[s.text, { fontWeight: "600", fontSize: theme.fontSize.base }]}>{item.label}</Text>
            <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>{item.description}</Text>
          </View>
          <Text style={[s.textMuted, { fontSize: theme.fontSize.md }]}>{isRtl ? "‹" : "›"}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    padding: 16,
    gap: 12,
    paddingBottom: 40,
  },
  quickGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    justifyContent: "space-between",
  },
  quickCard: {
    width: "47%",
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
  },
  quickIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    gap: 12,
  },
});
