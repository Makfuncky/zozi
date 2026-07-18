import React, { useState } from "react";
import {
  View,
  TextInput,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInputProps,
  ViewStyle,
} from "react-native";

interface InputProps extends TextInputProps {
  theme: {
    colors: {
      text: string;
      textFaint: string;
      danger: string;
      textMuted: string;
      surface2: string;
      border: string;
    };
    radius: { lg: number };
    spacing: { md: number; sm?: number };
    fontSize: { base: number };
    fontWeight: { semibold: string };
  };
  label?: string;
  error?: string;
  hint?: string;
  containerStyle?: ViewStyle;
  rightIcon?: React.ReactNode;
  isPassword?: boolean;
}

export default function Input({
  theme,
  label,
  error,
  hint,
  containerStyle,
  rightIcon,
  isPassword = false,
  style,
  ...props
}: InputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const inputStyle = {
    backgroundColor: theme.colors.surface2,
    color: theme.colors.text,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: error ? theme.colors.danger : theme.colors.border,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm || 7,
    fontSize: Math.max(12, (theme.fontSize.base || 14) - 1),
  };

  return (
    <View style={[styles.container, containerStyle]}>
      {label && <Text style={[{ color: theme.colors.text }, styles.label]}>{label}</Text>}
      <View style={styles.inputWrapper}>
        <TextInput
          {...props}
          secureTextEntry={isPassword && !showPassword}
          placeholderTextColor={theme.colors.textFaint}
          style={[
            inputStyle,
            styles.input,
            error ? { borderColor: theme.colors.danger } : undefined,
            style,
          ]}
        />
        {isPassword && (
          <TouchableOpacity
            onPress={() => setShowPassword((v) => !v)}
            style={styles.eyeBtn}
          >
            <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>
              {showPassword ? "Hide" : "Show"}
            </Text>
          </TouchableOpacity>
        )}
        {!isPassword && rightIcon && <View style={styles.eyeBtn}>{rightIcon}</View>}
      </View>
      {error ? (
        <Text style={[styles.hint, { color: theme.colors.danger }]}>{error}</Text>
      ) : (
        hint && <Text style={[styles.hint, { color: theme.colors.textMuted }]}>{hint}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 6,
  },
  label: {
    fontWeight: "500",
    fontSize: 13,
  },
  inputWrapper: {
    position: "relative",
  },
  input: {
    flex: 1,
  },
  eyeBtn: {
    position: "absolute",
    right: 12,
    top: 0,
    bottom: 0,
    justifyContent: "center",
  },
  hint: {
    fontSize: 11,
  },
});
