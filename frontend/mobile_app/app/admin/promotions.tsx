import React, { useEffect, useMemo } from "react";
import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { useAuthStore } from "@/lib/authStore";
import { makeStyles } from "@/theme";
import { hasAdminPermission, canAccessAdminBannerManagement, canAccessAdminFlashSales, isAdminStaffRole } from "@shared/adminPermissions";
import { AdminBannersPanel } from "./banners";
import { AdminCouponsPanel } from "./coupons";
import { AdminFlashSalesPanel } from "./flash-sales";

type PromotionsSection = "banners" | "coupons" | "flash-sales";

export default function AdminPromotionsHubScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const router = useRouter();
  const params = useLocalSearchParams<{ section?: string | string[] }>();
  const { user } = useAuthStore();
  const rawSection = Array.isArray(params.section) ? params.section[0] : params.section;

  const sections = useMemo(() => {
    const role = user?.role;
    return [
      { key: "banners" as const, label: "Banners", allowed: canAccessAdminBannerManagement(role) },
      { key: "coupons" as const, label: "Coupons", allowed: hasAdminPermission(role, "coupons.manage") },
      { key: "flash-sales" as const, label: "Flash Sales", allowed: canAccessAdminFlashSales(role) },
    ].filter((section) => section.allowed);
  }, [user?.role]);

  const activeSection = (rawSection && sections.some((section) => section.key === rawSection)
    ? rawSection
    : sections[0]?.key) as PromotionsSection | undefined;

  useEffect(() => {
    if (!isAdminStaffRole(user?.role)) {
      router.replace("/admin/login" as never);
      return;
    }
    if (!activeSection && sections[0]) {
      router.replace(`/admin/promotions?section=${sections[0].key}` as never);
      return;
    }
    if (activeSection && rawSection !== activeSection) {
      router.replace(`/admin/promotions?section=${activeSection}` as never);
    }
  }, [activeSection, rawSection, router, sections, user?.role]);

  if (!isAdminStaffRole(user?.role)) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
        <Stack.Screen options={{ title: "Promotions" }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <View testID="admin-promotions-screen" style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Promotions", headerStyle: { backgroundColor: theme.colors.surface0 }, headerTitleStyle: { color: theme.colors.text, fontWeight: "700" } }} />

      <View style={{ paddingHorizontal: theme.spacing.md, paddingTop: theme.spacing.md, paddingBottom: theme.spacing.sm }}>
        <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Promotions</Text>
        <Text style={s.textMuted}>Canonical workspace for banners, coupons, and flash-sale campaigns.</Text>
      </View>

      <ScrollView
        testID="admin-promotions-tab-bar"
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0, borderBottomWidth: 1, borderColor: theme.colors.border }}
        contentContainerStyle={{ paddingHorizontal: theme.spacing.md, paddingBottom: theme.spacing.sm, gap: 8 }}
      >
        {sections.map((section) => {
          const selected = section.key === activeSection;
          return (
            <TouchableOpacity
              key={section.key}
              testID={`admin-promotions-tab-${section.key}`}
              onPress={() => router.replace(`/admin/promotions?section=${section.key}` as never)}
              style={{
                paddingHorizontal: 14,
                paddingVertical: 8,
                borderRadius: 18,
                backgroundColor: selected ? theme.colors.brand : theme.colors.surface1,
                borderWidth: 1,
                borderColor: selected ? theme.colors.brand : theme.colors.border,
              }}
            >
              <Text style={{ color: selected ? theme.colors.onBrand : theme.colors.textMuted, fontWeight: "700", fontSize: theme.fontSize.sm }}>{section.label}</Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <View style={{ flex: 1 }}>
        {activeSection === "banners" && <AdminBannersPanel />}
        {activeSection === "coupons" && <AdminCouponsPanel />}
        {activeSection === "flash-sales" && <AdminFlashSalesPanel />}
      </View>
    </View>
  );
}