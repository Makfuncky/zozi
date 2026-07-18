import React, { useEffect, useState, useCallback, useRef } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, RefreshControl, Animated } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { getNotifications, markAllNotificationsRead, deleteNotification } from "@/lib/api";
import type { Notification } from "@/lib/api";
import { useTranslateTexts } from "@/lib/useTranslate";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    flex: 1,
    padding: theme.spacing.md,
    paddingBottom: 48,
  },
  section: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  sectionTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: "700",
    marginBottom: theme.spacing.md,
  },
  notificationItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  notificationItemLast: {
    borderBottomWidth: 0,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontWeight: "600",
    marginBottom: 4,
  },
  notificationMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  notificationTime: {
    fontSize: theme.fontSize.xs,
  },
  unreadIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 4,
  },
  headerRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  headerBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
});

export default function NotificationsScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [markingRead, setMarkingRead] = useState(false);

  const [unreadCount] = useTranslateTexts(["Unread"]);

  const loadNotifications = async () => {
    try {
      const data = await getNotifications();
      setNotifications(data || []);
    } catch (err) {
      console.warn("Failed to load notifications", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadNotifications();
  };

  const handleMarkAllRead = async () => {
    if (markingRead || notifications.length === 0) return;
    setMarkingRead(true);
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (err) {
      console.warn("Failed to mark all read", err);
    } finally {
      setMarkingRead(false);
    }
  };

  const handleDelete = async (id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    try {
      await deleteNotification(id);
    } catch (err) {
      // Revert on error
      console.warn("Failed to delete notification", err);
    }
  };

  const unreadCountValue = notifications.filter((n) => !n.read).length;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <ScreenHeader title="Notifications" />

      {loading ? (
        <View style={[styles.scroll, { justifyContent: "center", alignItems: "center" }]}>
          <ActivityIndicator size="large" color={theme.colors.brand} />
        </View>
      ) : notifications.length === 0 ? (
        <EmptyState
          title="No notifications yet"
          subtitle="When you receive notifications, they'll appear here."
          icon="notifications-outline"
        />
      ) : (
        <FlatList
          style={styles.scroll}
          data={notifications}
          keyExtractor={(item) => String(item.id)}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={theme.colors.brand} />
          }
          contentContainerStyle={{ paddingBottom: 48 }}
          renderItem={({ item: notification, index }) => (
            <NotificationRow
              key={notification.id}
              notification={notification}
              index={index}
              isLast={index === notifications.length - 1}
              borderColor={theme.colors.border}
              brandColor={theme.colors.brand}
              surfaceColor={theme.colors.surface2}
              textMutedColor={theme.colors.textMuted}
              onDelete={handleDelete}
              s={s}
              styles={styles}
            />
          )}
        />
      )}
    </View>
  );
}

type NotificationRowProps = {
  notification: Notification;
  index: number;
  isLast: boolean;
  borderColor: string;
  brandColor: string;
  surfaceColor: string;
  textMutedColor: string;
  onDelete: (id: number) => void;
  s: ReturnType<typeof makeStyles>;
  styles: ReturnType<typeof createStyles>;
};

function NotificationRow({ notification, index, isLast, borderColor, brandColor, surfaceColor, textMutedColor, onDelete, s, styles }: NotificationRowProps) {
  const fade = useRef(new Animated.Value(0)).current;
  const slide = useRef(new Animated.Value(16)).current;
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.delay(index * 40),
      Animated.parallel([
        Animated.timing(fade, { toValue: 1, duration: 280, useNativeDriver: true }),
        Animated.timing(slide, { toValue: 0, duration: 280, useNativeDriver: true }),
      ]),
    ]).start();
  }, [index, fade, slide]);

  useEffect(() => {
    if (notification.read) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1.35, duration: 700, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1, duration: 700, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [notification.read, pulse]);

  const iconName =
    notification.type === "order"
      ? "cube-outline"
      : notification.type === "promotion"
      ? "pricetag-outline"
      : "notifications";

  return (
    <Animated.View
      style={[
        styles.notificationItem,
        isLast && styles.notificationItemLast,
        { borderBottomColor: borderColor, opacity: fade, transform: [{ translateY: slide }] },
      ]}
    >
      <View style={[styles.iconBox, { backgroundColor: notification.read ? surfaceColor : brandColor + "22" }]}>
        <Ionicons name={iconName} size={18} color={notification.read ? textMutedColor : brandColor} />
      </View>
      <View style={styles.notificationContent}>
        <Text style={[s.text, styles.notificationTitle]} numberOfLines={2}>
          {notification.title}
        </Text>
        <Text style={[s.textMuted, styles.notificationTime]} numberOfLines={2}>
          {notification.message}
        </Text>
        <View style={styles.notificationMeta}>
          <Text style={[s.textMuted, styles.notificationTime]}>
            {new Date(notification.created_at).toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
          </Text>
          {!notification.read && (
            <Animated.View style={[styles.unreadIndicator, { backgroundColor: brandColor, transform: [{ scale: pulse }] }]} />
          )}
        </View>
      </View>
      <TouchableOpacity
        onPress={() => onDelete(notification.id)}
        style={{ padding: 4 }}
        testID={`notifications-delete-${notification.id}`}
      >
        <Ionicons name="trash-outline" size={18} color={textMutedColor} />
      </TouchableOpacity>
    </Animated.View>
  );
}