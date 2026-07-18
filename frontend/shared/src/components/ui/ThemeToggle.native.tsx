import React from "react";
import { TouchableOpacity, Text, StyleSheet } from "react-native";

interface ThemeToggleProps {
  theme: "light" | "dark";
  onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  return (
    <TouchableOpacity
      onPress={onToggle}
      style={[styles.button, theme === "dark" ? styles.dark : styles.light]}
      accessibilityRole="button"
      accessibilityLabel={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
    >
      <Text style={[styles.label, theme === "dark" ? styles.labelDark : styles.labelLight]}>
        {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  dark: {
    backgroundColor: "#1f2937",
    borderColor: "#334155",
  },
  light: {
    backgroundColor: "#e5e7eb",
    borderColor: "#d1d5db",
  },
  label: {
    fontWeight: "600",
  },
  labelDark: {
    color: "#f8fafc",
  },
  labelLight: {
    color: "#1f2937",
  },
});
