import { Stack, usePathname, useRouter } from "expo-router";
import React, { useEffect } from "react";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

export default function LogisticsPartnerLayout() {
  const { user, isLoading, isLoggedIn } = useAuthStore();
  const { theme } = useThemeStore();
  const router = useRouter();
  const pathname = usePathname();

  const isPublicLogisticsRoute = pathname === "/logistics-partner/login" || pathname === "/logistics-partner/register";

  useEffect(() => {
    if (isLoading) return;
    if (isPublicLogisticsRoute) return;
    const allowed =
      isLoggedIn &&
      (user?.role === "logistics_partner" ||
        user?.role === "admin" ||
        user?.role === "sub_admin");
    if (!allowed) {
      router.replace("/logistics-partner/login" as never);
    }
  }, [isLoading, isLoggedIn, isPublicLogisticsRoute, user, router]);

  if (isLoading) return <LoadingSpinner fullscreen />;

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.brand },
        headerTintColor: theme.colors.onBrand,
        headerTitleStyle: { fontWeight: "700" },
      }}
    />
  );
}
