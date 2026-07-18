import { Stack, usePathname, useRouter } from "expo-router";
import React, { useEffect } from "react";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

export default function SupplierLayout() {
  const { user, isLoading, isLoggedIn } = useAuthStore();
  const { theme } = useThemeStore();
  const router = useRouter();
  const pathname = usePathname();

  const isPublicSupplierRoute = pathname === "/supplier/login" || pathname === "/supplier/register";

  useEffect(() => {
    if (!isLoading && !isPublicSupplierRoute && (!isLoggedIn || user?.role !== "supplier")) {
      router.replace("/supplier/login" as never);
    }
  }, [isLoading, isLoggedIn, isPublicSupplierRoute, user, router]);

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
