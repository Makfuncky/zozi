import React from "react";
import { useThemeStore } from "@/lib/themeStore";
import { TouchableOpacity, Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export function ThemeToggle() {
  const { mode, toggle, theme } = useThemeStore();

  return (
    <TouchableOpacity
      onPress={toggle}
      style={[styles.button, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
      accessibilityRole="button"
      accessibilityLabel={`Switch to ${mode === "dark" ? "light" : "dark"} theme`}
    >
      <Ionicons
        name={mode === "dark" ? "sunny-outline" : "moon-outline"}
        size={16}
        color={theme.colors.text}
      />
      <Text style={[styles.label, { color: theme.colors.text }]}>
        {mode === "dark" ? "Light" : "Dark"}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    justifyContent: "center",
  },
  label: {
    fontWeight: "600",
  },
});
