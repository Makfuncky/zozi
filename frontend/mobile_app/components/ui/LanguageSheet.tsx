import React from "react";
import { Modal, View, Text, TouchableWithoutFeedback, TouchableOpacity, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { useLocaleStore } from "@/lib/localeStore";
import { LANGUAGE_OPTIONS } from "@shared/localization";
import { makeStyles } from "@/theme";

/**
 * Bottom-sheet language picker. Slides up so the user can choose from the full
 * list of supported languages (not just a binary toggle).
 */
export default function LanguageSheet({ visible, onClose, onSelect }: { visible: boolean; onClose: () => void; onSelect?: (code: string) => void }) {
  const { theme } = useThemeStore();
  const { locale, setLocale } = useLocaleStore();
  const s = makeStyles(theme);

  const select = (code: any) => {
    setLocale(code);
    onSelect?.(code);
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={[StyleSheet.absoluteFill, { backgroundColor: "rgba(0,0,0,0.5)" }]} />
      </TouchableWithoutFeedback>
      <View style={[styles.sheet, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        <View style={styles.handle} />
        <View style={styles.header}>
          <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>Language</Text>
          <TouchableOpacity onPress={onClose} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }} style={[styles.closeBtn, { backgroundColor: theme.colors.surface2 }]}>
            <Ionicons name="close" size={20} color={theme.colors.text} />
          </TouchableOpacity>
        </View>
        <FlatList
          data={LANGUAGE_OPTIONS as any[]}
          keyExtractor={(l) => l.code}
          style={{ maxHeight: 420 }}
          renderItem={({ item }) => {
            const active = item.code === locale;
            return (
              <TouchableOpacity
                onPress={() => select(item.code)}
                style={[styles.row, { borderBottomColor: theme.colors.border, backgroundColor: active ? theme.colors.brand + "15" : "transparent" }]}
              >
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "600" }]}>{item.nativeName}</Text>
                  <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{item.name} · {item.code.toUpperCase()}</Text>
                </View>
                {active && <Ionicons name="checkmark-circle" size={22} color={theme.colors.brand} />}
              </TouchableOpacity>
            );
          }}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  sheet: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    borderWidth: 1,
    paddingTop: 10,
    paddingBottom: 28,
    paddingHorizontal: 16,
  },
  handle: {
    width: 42,
    height: 4,
    borderRadius: 2,
    backgroundColor: "rgba(128,128,128,0.35)",
    alignSelf: "center",
    marginBottom: 8,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 4,
    paddingBottom: 10,
  },
  closeBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    gap: 12,
    borderBottomWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 8,
  },
});
