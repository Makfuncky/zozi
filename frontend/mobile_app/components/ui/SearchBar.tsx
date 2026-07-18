import React from "react";
import { View, TextInput, TouchableOpacity, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  onSubmit?: () => void;
  onFocus?: () => void;
  onBlur?: () => void;
  containerStyle?: object;
  inputStyle?: object;
  theme?: {
    colors?: { surface2?: string; text?: string; textMuted?: string; border?: string };
    fontSize?: { base?: number };
    fontFamily?: { body?: string };
  };
  leftComponent?: React.ReactNode;
  rightComponent?: React.ReactNode;
}

export default function SearchBar({
  value,
  onChange,
  onClear,
  placeholder,
  onSubmit,
  onFocus,
  onBlur,
  containerStyle,
  inputStyle,
  theme: themeProp,
  leftComponent,
  rightComponent,
}: SearchBarProps) {
  const { theme: storeTheme } = useThemeStore();
  const theme = themeProp ?? storeTheme;
  const bgColor = theme?.colors?.surface2 ?? "#0f172a";
  const textColor = theme?.colors?.text ?? "#f8fafc";
  const placeholderColor = theme?.colors?.textMuted ?? "#9ca3af";
  const size = theme?.fontSize?.base ?? 14;
  const font = theme?.fontFamily?.body ?? undefined;

  return (
    <View accessibilityRole="search" accessibilityLabel={placeholder ?? "Search"} style={styles.containerOuter}>
      {leftComponent ? <View style={styles.sideSlot}>{leftComponent}</View> : null}

      <View style={[styles.container, { backgroundColor: bgColor, borderColor: theme?.colors?.border ?? "#1f2937" }, containerStyle]}>
        <Ionicons name="search-outline" size={size + 4} color={placeholderColor} />
        <TextInput
          value={value}
          onChangeText={onChange}
          placeholder={placeholder ?? "Search products..."}
          placeholderTextColor={placeholderColor}
          style={[
            styles.input,
            { color: textColor, fontSize: size, fontFamily: font },
            inputStyle,
          ]}
          autoCorrect={false}
          returnKeyType="search"
          onSubmitEditing={() => onSubmit?.()}
          onFocus={() => onFocus?.()}
          onBlur={() => onBlur?.()}
        />
        {!!value && (
          <TouchableOpacity onPress={onClear} style={styles.clearButton} accessibilityLabel="Clear search">
            <Ionicons name="close-circle" size={16} color={placeholderColor} />
          </TouchableOpacity>
        )}
      </View>

      {rightComponent ? <View style={styles.sideSlot}>{rightComponent}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  containerOuter: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  container: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  icon: {
    color: "#9ca3af",
    fontSize: 18,
  },
  input: {
    flex: 1,
    color: "#f8fafc",
    fontSize: 14,
    minHeight: 20,
  },
  clearButton: {
    padding: 4,
  },
  clearText: {
    color: "#9ca3af",
    fontSize: 11,
  },
  sideSlot: {
    minWidth: 44,
    alignItems: "center",
    justifyContent: "center",
  },
});