import { Stack } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";

export default function AuthLayout() {
  const { theme } = useThemeStore();
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.surface0 },
        headerTintColor: theme.colors.text,
        headerShadowVisible: false,
        contentStyle: { backgroundColor: theme.colors.surface0 },
      }}
    />
  );
}
