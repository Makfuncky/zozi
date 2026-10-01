import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  onPress?: () => void;
  theme?: "light" | "dark";
  showWordmark?: boolean;
}

export default function Logo({ size = "md", onPress, theme = "light", showWordmark = true }: LogoProps) {
  const sizes = {
    sm: { width: 58, height: 48, fontSize: 16 },
    md: { width: 82, height: 64, fontSize: 22 },
    lg: { width: 110, height: 84, fontSize: 30 },
  };

  const { width, height, fontSize } = sizes[size];

  const content = (
    <View style={[styles.container, { width, height }]}>
      <View style={styles.logoMark}>
        <Text style={[styles.zoziText, { fontSize, color: theme === "light" ? "#1A5204" : "#EEFF99" }]}>
          ZOZI
        </Text>
      </View>
    </View>
  );

  if (!onPress) {
    return content;
  }

  return (
    <TouchableOpacity style={styles.touchable} onPress={onPress}>
      {content}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  logoMark: {
    backgroundColor: "#7CFC00",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  zoziText: {
    fontWeight: "900",
    letterSpacing: -1,
  },
  touchable: {
    flexDirection: "row",
    alignItems: "center",
  },
});