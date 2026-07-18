import React from "react";
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from "react-native";
import { brand, light, dark, getGlass } from "../../theme.native";

export type ButtonVariant = "default" | "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps {
  label?: string;
  onPress: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  mode?: "dark" | "light";
}

const palette = {
  dark: {
    surface: dark.surface1,
    text: dark.text,
    brand: brand.primary,
    accent: brand.accent,
    danger: dark.surface3,
    textOnBrand: dark.onBrand ?? "#fff",
    textOnAccent: dark.onAccent ?? "#fff",
  },
  light: {
    surface: light.surface1,
    text: light.text,
    brand: brand.primary,
    accent: brand.accent,
    danger: light.surface3,
    textOnBrand: light.onBrand ?? "#fff",
    textOnAccent: light.onAccent ?? "#fff",
  },
};

function getVariantStyle(variant: ButtonVariant, mode: "dark" | "light") {
  const colors = palette[mode];
  switch (variant) {
    case "secondary":
      return {
        backgroundColor: "transparent",
        borderColor: colors.brand,
        borderWidth: 1,
        color: colors.brand,
      };
    case "ghost":
      return {
        backgroundColor: "transparent",
        borderColor: "transparent",
        color: colors.text,
      };
    case "danger":
      return {
        backgroundColor: "#ef4444",
        borderColor: "#ef4444",
        color: colors.textOnBrand,
      };
    case "default":
    case "primary":
    default:
      return {
        backgroundColor: colors.brand,
        borderColor: colors.brand,
        color: colors.textOnBrand,
      };
  }
}

const sizeMap: Record<ButtonSize, {paddingVertical:number; paddingHorizontal:number; fontSize:number}> = {
  sm: { paddingVertical: 7, paddingHorizontal: 14, fontSize: 12 },
  md: { paddingVertical: 11, paddingHorizontal: 20, fontSize: 14 },
  lg: { paddingVertical: 14, paddingHorizontal: 27, fontSize: 15 },
};

export default function Button({
  label,
  onPress,
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  style,
  textStyle,
  leftIcon,
  rightIcon,
  mode = "dark",
}: ButtonProps) {
  const isDisabled = disabled || loading;
  const variantStyle = getVariantStyle(variant, mode);
  const sizeStyle = sizeMap[size];

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.75}
      style={[
        styles.base,
        { backgroundColor: variantStyle.backgroundColor, borderColor: variantStyle.borderColor },
        {
          paddingVertical: sizeStyle.paddingVertical,
          paddingHorizontal: sizeStyle.paddingHorizontal,
          borderRadius: 12,
        },
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === "secondary" || variant === "ghost" ? palette[mode].brand : "#ffffff"}
          size="small"
        />
      ) : (
        <>
          {leftIcon}
          <Text
            style={[
              {
                color: variantStyle.color,
                fontWeight: "600",
                fontSize: sizeStyle.fontSize,
              },
              textStyle,
            ]}
          >
            {label}
          </Text>
          {rightIcon}
        </>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderRadius: 12,
    borderWidth: 1,
  },
  disabled: {
    opacity: 0.5,
  },
});
