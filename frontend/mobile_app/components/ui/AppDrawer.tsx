import React, { useEffect, useRef } from "react";
import {
  Modal,
  View,
  Text,
  TouchableWithoutFeedback,
  TouchableOpacity,
  Animated,
  StyleSheet,
  Platform,
  type ViewStyle,
} from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

interface AppDrawerProps {
  visible: boolean;
  onClose: () => void;
  side?: "left" | "right";
  title?: string;
  children: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
}

/**
 * Frosted side drawer used for the left (navigation) and right (account)
 * hamburger panels. Slides in from the requested edge with a dimmed overlay.
 */
export default function AppDrawer({
  visible,
  onClose,
  side = "left",
  title,
  children,
  style,
}: AppDrawerProps) {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const translate = useRef(new Animated.Value(side === "left" ? -420 : 420)).current;
  const overlayOpacity = useRef(new Animated.Value(0)).current;
  const [mounted, setMounted] = React.useState(visible);

  React.useEffect(() => {
    if (visible) {
      setMounted(true);
      translate.setValue(side === "left" ? -420 : 420);
      overlayOpacity.setValue(0);
      Animated.parallel([
        Animated.timing(translate, {
          toValue: 0,
          duration: 260,
          useNativeDriver: true,
        } as any),
        Animated.timing(overlayOpacity, {
          toValue: 1,
          duration: 220,
          useNativeDriver: true,
        } as any),
      ]).start();
    } else if (mounted) {
      Animated.parallel([
        Animated.timing(translate, {
          toValue: side === "left" ? -420 : 420,
          duration: 220,
          useNativeDriver: true,
        } as any),
        Animated.timing(overlayOpacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        } as any),
      ]).start(({ finished }) => {
        if (finished) setMounted(false);
      });
    }
  }, [visible, side, translate, overlayOpacity, mounted]);

  if (!mounted) return null;

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <View style={StyleSheet.absoluteFill}>
        <TouchableWithoutFeedback onPress={onClose}>
          <Animated.View
            style={[
              StyleSheet.absoluteFillObject,
              { backgroundColor: theme.colors.glass.overlay, opacity: overlayOpacity },
            ]}
          />
        </TouchableWithoutFeedback>

        <Animated.View
          style={[
            styles.panel,
            side === "left"
              ? {
                  left: 0,
                  borderTopRightRadius: 26,
                  borderBottomRightRadius: 26,
                }
              : {
                  right: 0,
                  borderTopLeftRadius: 26,
                  borderBottomLeftRadius: 26,
                },
            {
              backgroundColor: theme.colors.glass.panelStrong,
              borderColor: theme.colors.glass.border,
              transform: [{ translateX: translate }],
              ...Platform.select({
                web: {
                  backdropFilter: "blur(22px) saturate(150%)",
                  boxShadow:
                    side === "left"
                      ? "12px 0 44px rgba(0,0,0,0.5)"
                      : "-12px 0 44px rgba(0,0,0,0.5)",
                },
                default: {
                  shadowColor: "#000",
                  shadowOffset: { width: 0, height: 0 },
                  shadowOpacity: 0.5,
                  shadowRadius: 30,
                  elevation: 30,
                },
              }),
            },
            style,
          ]}
        >
          <View style={styles.handle} />
          <View style={styles.header}>
            <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>
              {title}
            </Text>
            <TouchableOpacity
              onPress={onClose}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              style={[styles.closeBtn, { backgroundColor: theme.colors.surface2 }]}
            >
              <Ionicons name="close" size={20} color={theme.colors.text} />
            </TouchableOpacity>
          </View>
          <View style={styles.body}>{children}</View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  panel: {
    position: "absolute",
    top: 0,
    bottom: 0,
    width: "82%",
    maxWidth: 340,
    borderWidth: 1,
    paddingTop: 14,
    paddingBottom: 24,
  },
  handle: {
    width: 42,
    height: 4,
    borderRadius: 2,
    backgroundColor: "rgba(255,255,255,0.18)",
    alignSelf: "center",
    marginBottom: 8,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 18,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.08)",
  },
  closeBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  body: {
    flex: 1,
    paddingTop: 8,
  },
});
