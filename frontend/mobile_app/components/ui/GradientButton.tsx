import React from "react";
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  type ViewStyle,
  type TextStyle,
} from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  /* fallback to solid brand */
}

export type GradientButtonSize = "sm" | "md" | "lg";

export interface GradientButtonProps {
  label?: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  testID?: string;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: ViewStyle;
  textStyle?: TextStyle;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  size?: GradientButtonSize;
}

const sizeMap: Record<GradientButtonSize, { paddingVertical: number; paddingHorizontal: number; fontSize: number; radius: number }> = {
  sm: { paddingVertical: 9, paddingHorizontal: 16, fontSize: 13, radius: 12 },
  md: { paddingVertical: 12, paddingHorizontal: 22, fontSize: 15, radius: 14 },
  lg: { paddingVertical: 15, paddingHorizontal: 28, fontSize: 16, radius: 16 },
};

function GradientButton({
  label,
  onPress,
  loading = false,
  disabled = false,
  testID,
  accessibilityLabel,
  accessibilityHint,
  style,
  textStyle,
  leftIcon,
  rightIcon,
  size = "md",
}: GradientButtonProps) {
  const { theme } = useThemeStore();
  const s = sizeMap[size];
  const isDisabled = disabled || loading;
  const [from, to] = theme.gradients.button;

  const inner = (
    <>
      {loading ? (
        <ActivityIndicator color={theme.colors.onBrand} size="small" accessibilityLabel="Loading" />
      ) : (
        <>
          {leftIcon}
          {label ? (
            <Text style={[{ color: theme.colors.onBrand, fontWeight: "700", fontSize: s.fontSize }, textStyle]}>
              {label}
            </Text>
          ) : null}
          {rightIcon}
        </>
      )}
    </>
  );

  const containerStyle: ViewStyle = {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: s.paddingVertical,
    paddingHorizontal: s.paddingHorizontal,
    borderRadius: s.radius,
    opacity: isDisabled ? 0.6 : 1,
  };

  if (LinearGradient && !isDisabled) {
    return (
      <TouchableOpacity
        testID={testID}
        accessibilityRole="button"
        accessibilityState={{ disabled: isDisabled }}
        accessibilityLabel={accessibilityLabel ?? label}
        accessibilityHint={accessibilityHint}
        onPress={onPress}
        disabled={isDisabled}
        activeOpacity={0.85}
        style={[styles.touchable, style]}
      >
        <LinearGradient colors={[from, to]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[containerStyle, styles.gradient]}>
          {inner}
        </LinearGradient>
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      testID={testID}
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled }}
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityHint={accessibilityHint}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.85}
      style={[containerStyle, { backgroundColor: theme.colors.brand }, styles.gradient, style]}
    >
      {inner}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  touchable: {
    alignSelf: "stretch",
  },
  gradient: {
    overflow: "hidden",
  },
});

export { GradientButton };
export default GradientButton;
