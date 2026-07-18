import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { dark, light } from "../../theme.native";

interface ErrorAlertProps {
  message: string;
  type?: "error" | "success" | "info";
}

const getStyles = (type: "error" | "success" | "info", mode: "dark" | "light") => {
  const colors = mode === "light" ? light : dark;
  const base = {
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  };

  switch (type) {
    case "error":
      return {
        ...base,
        backgroundColor: colors.danger + "1A", // 10% opacity
        borderColor: colors.danger + "4D", // 30% opacity
      };
    case "success":
      return {
        ...base,
        backgroundColor: colors.success + "1A",
        borderColor: colors.success + "4D",
      };
    case "info":
      return {
        ...base,
        backgroundColor: colors.info + "1A",
        borderColor: colors.info + "4D",
      };
  }
};

export default function ErrorAlert({
  message,
  type = "error",
}: ErrorAlertProps) {
  if (!message) return null;

  // For simplicity, use dark theme
  const styles = getStyles(type, "dark");
  const textColor = dark.danger; // Use error color for text

  return (
    <View style={styles}>
      <Text style={{ fontSize: 14, color: textColor }}>{message}</Text>
    </View>
  );
}