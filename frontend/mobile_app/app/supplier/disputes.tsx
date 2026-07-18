import { useEffect } from "react";
import { View, Text } from "react-native";
import { Stack, useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";

export default function SupplierDisputesRedirectScreen() {
  const router = useRouter();
  const { theme } = useThemeStore();
  const s = makeStyles(theme);

  useEffect(() => {
    router.replace("/supplier/support?section=disputes" as never);
  }, [router]);

  return (
    <View style={[s.container, { alignItems: "center", justifyContent: "center" }]}>
      <Stack.Screen options={{ title: "Disputes" }} />
      <Text style={s.text}>Opening supplier disputes...</Text>
    </View>
  );
}