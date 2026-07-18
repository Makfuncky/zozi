import React from "react";
import type { TextInputProps, ViewStyle } from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import { View, TextInput, Text, TouchableOpacity, StyleSheet } from "react-native";

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
  containerStyle?: ViewStyle;
  rightIcon?: React.ReactNode;
  isPassword?: boolean;
}

function Input({
  label,
  error,
  hint,
  containerStyle,
  rightIcon,
  isPassword = false,
  ...props
}: InputProps) {
  const { theme } = useThemeStore();
  const [showPassword, setShowPassword] = React.useState(false);

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
      {label ? <Text style={[{ color: theme.colors.text }, styles.label]}>{label}</Text> : null}
      <View style={styles.inputWrapper}>
        <TextInput
          {...props}
          accessibilityLabel={props.accessibilityLabel ?? label}
          accessibilityHint={error || hint}
          secureTextEntry={isPassword && !showPassword}
          placeholderTextColor={theme.colors.textFaint}
          style={[
            inputStyle,
            styles.input,
            error ? { borderColor: theme.colors.danger } : undefined,
            props.style,
          ]}
        />
        {isPassword ? (
          <TouchableOpacity
            onPress={() => setShowPassword((value) => !value)}
            style={styles.eyeBtn}
            accessibilityRole="button"
            accessibilityLabel={showPassword ? "Hide password" : "Show password"}
          >
            <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>
              {showPassword ? "Hide" : "Show"}
            </Text>
          </TouchableOpacity>
        ) : null}
        {!isPassword && rightIcon ? <View style={styles.eyeBtn}>{rightIcon}</View> : null}
      </View>
      {error ? (
        <Text style={[styles.hint, { color: theme.colors.danger }]}>{error}</Text>
      ) : hint ? (
        <Text style={[styles.hint, { color: theme.colors.textMuted }]}>{hint}</Text>
      ) : null}
    </View>
  );
}

export { Input };
export default Input;

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

