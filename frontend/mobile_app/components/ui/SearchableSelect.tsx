import React from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { useThemeStore } from "@/lib/themeStore";

interface SearchableSelectProps {
  label: string;
  value: string;
  options: string[];
  placeholder: string;
  searchPlaceholder: string;
  emptyLabel: string;
  allowCustomEntry?: boolean;
  onChange: (value: string) => void;
}

export function SearchableSelect({
  label,
  value,
  options,
  placeholder,
  searchPlaceholder,
  emptyLabel,
  allowCustomEntry = false,
  onChange,
}: SearchableSelectProps) {
  const { theme } = useThemeStore();
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");

  const filteredOptions = React.useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return options;
    return options.filter((option) => option.toLowerCase().includes(normalizedQuery));
  }, [options, query]);

  const handleSelect = (nextValue: string) => {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  };

  const showCustomAction = allowCustomEntry && query.trim().length > 0 && !options.some((option) => option.toLowerCase() === query.trim().toLowerCase());

  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: theme.colors.text }]}>{label}</Text>
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={() => setOpen((current) => !current)}
        style={[
          styles.trigger,
          {
            backgroundColor: theme.colors.surface2,
            borderColor: theme.colors.border,
          },
        ]}
      >
        <Text style={{ color: value ? theme.colors.text : theme.colors.textFaint, fontSize: 13 }}>
          {value || placeholder}
        </Text>
      </TouchableOpacity>
      {open ? (
        <View style={[styles.panel, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={searchPlaceholder}
            placeholderTextColor={theme.colors.textFaint}
            style={[
              styles.searchInput,
              {
                backgroundColor: theme.colors.surface2,
                borderColor: theme.colors.border,
                color: theme.colors.text,
              },
            ]}
          />
          <ScrollView style={styles.optionList} nestedScrollEnabled>
            {filteredOptions.map((option) => {
              const active = option.toLowerCase() === value.trim().toLowerCase();
              return (
                <TouchableOpacity
                  key={option}
                  onPress={() => handleSelect(option)}
                  style={[
                    styles.option,
                    active
                      ? { backgroundColor: `${theme.colors.brand}22`, borderColor: theme.colors.brand }
                      : { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border },
                  ]}
                >
                  <Text style={{ color: active ? theme.colors.brand : theme.colors.text, fontSize: 12, fontWeight: "600" }}>{option}</Text>
                </TouchableOpacity>
              );
            })}
            {showCustomAction ? (
              <TouchableOpacity
                onPress={() => handleSelect(query.trim())}
                style={[styles.option, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}
              >
                <Text style={{ color: theme.colors.text, fontSize: 12, fontWeight: "600" }}>Use "{query.trim()}"</Text>
              </TouchableOpacity>
            ) : null}
            {filteredOptions.length === 0 && !showCustomAction ? (
              <Text style={{ color: theme.colors.textMuted, fontSize: 12, paddingVertical: 6 }}>{emptyLabel}</Text>
            ) : null}
          </ScrollView>
        </View>
      ) : null}
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
  trigger: {
    borderRadius: 16,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  panel: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 10,
    gap: 8,
  },
  searchInput: {
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
  },
  optionList: {
    maxHeight: 180,
  },
  option: {
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 8,
  },
});