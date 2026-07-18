import React, { useCallback, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { useChatbotStore, ChatSession } from "@/lib/chatbotStore";
import { EmptyState } from "@/components/ui/EmptyState";
import ScreenHeader from "@/components/ui/ScreenHeader";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surface0,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  headerTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: "700",
    color: theme.colors.text,
  },
  newBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.pillActiveBg,
  },
  newBtnText: {
    color: theme.colors.brand,
    fontWeight: "600",
    fontSize: theme.fontSize.base,
  },
  sessionItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  sessionItemLast: {
    borderBottomWidth: 0,
  },
  sessionInfo: {
    flex: 1,
    marginRight: theme.spacing.md,
  },
  sessionTitle: {
    fontSize: theme.fontSize.base,
    fontWeight: "600",
    color: theme.colors.text,
    marginBottom: 2,
  },
  sessionPreview: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textMuted,
  },
  sessionMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.spacing.sm,
    marginTop: 2,
  },
  sessionTime: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textFaint,
  },
  sessionBadge: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: theme.colors.brand,
  },
  actionBtn: {
    padding: theme.spacing.sm,
  },
});

export default function ChatbotHistoryScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const {
    sessions,
    createSession,
    setActiveSession,
    deleteSession,
    getSession,
  } = useChatbotStore();

  const [refreshing, setRefreshing] = useState(false);

  const handleNewSession = useCallback(() => {
    const newSession = createSession();
    setActiveSession(newSession.id);
    router.push({
      pathname: "/chatbot",
      params: { new: "true" },
    } as never);
  }, [createSession, setActiveSession, router]);

  const handleSelectSession = useCallback(
    (id: string) => {
      setActiveSession(id);
      router.push({
        pathname: "/chatbot",
        params: { sessionId: id },
      } as never);
    },
    [setActiveSession, router]
  );

  const handleDeleteSession = useCallback(
    (id: string) => {
      Alert.alert(
        "Delete Conversation",
        "This will permanently delete this conversation. This action cannot be undone.",
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Delete",
            style: "destructive",
            onPress: () => deleteSession(id),
          },
        ]
      );
    },
    [deleteSession]
  );

  const renderSession = useCallback(
    ({ item }: { item: ChatSession }) => {
      const lastMessage = item.messages[item.messages.length - 1];
      const isUnread = item.messages.length === 0; // New session indicator

      return (
        <TouchableOpacity
          style={[styles.sessionItem, isUnread && { backgroundColor: theme.colors.surface1 }]}
          onPress={() => handleSelectSession(item.id)}
          activeOpacity={0.7}
        >
          <View style={styles.sessionInfo}>
            <Text
              style={styles.sessionTitle}
              numberOfLines={1}
            >
              {item.title}
            </Text>
            <Text
              style={styles.sessionPreview}
              numberOfLines={2}
            >
              {lastMessage ? (lastMessage.isBot ? lastMessage.text : `You: ${lastMessage.text}`) : "No messages yet"}
            </Text>
            <View style={styles.sessionMeta}>
              <Text style={styles.sessionTime}>
                {new Date(item.updatedAt).toLocaleDateString([], {
                  month: "short",
                  day: "numeric",
                })}
              </Text>
              {isUnread && <View style={styles.sessionBadge} />}
            </View>
          </View>
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => handleDeleteSession(item.id)}
            testID={`chatbot-delete-${item.id}`}
          >
            <Ionicons
              name="trash-outline"
              size={20}
              color={theme.colors.textMuted}
            />
          </TouchableOpacity>
        </TouchableOpacity>
      );
    },
    [handleSelectSession, handleDeleteSession, theme]
  );

  const keyExtractor = useCallback((item: ChatSession) => String(item.id), []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 500);
  }, []);

  return (
    <View style={styles.container}>
      <ScreenHeader
        title="Chat History"
        rightIcon="add"
        rightLabel="New Chat"
        onRightPress={handleNewSession}
      />

      {sessions.length === 0 ? (
        <EmptyState
          title="No conversations yet"
          subtitle="Start a new chat with your AI shopping assistant to see history here."
          icon={<Ionicons name="chatbubble-ellipses" size={40} color={theme.colors.brand} />}
          action={{ label: "Start First Chat", onPress: handleNewSession }}
        />
      ) : (
        <FlatList
          data={sessions}
          keyExtractor={keyExtractor}
          renderItem={renderSession}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.colors.brand}
            />
          }
          contentContainerStyle={{ paddingBottom: theme.spacing.xl }}
        />
      )}
    </View>
  );
}