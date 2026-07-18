import React, { useRef, useState, useEffect, useCallback } from "react";
import { ActivityIndicator, FlatList, Image, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { useLocalSearchParams, useRouter } from "expo-router";
import { getChatbotReplyKey } from "@shared/chatbot";
import type { ChatbotResponsePayload, ChatbotResultMode, ChatbotSearchResult } from "@shared/chatbot";
import { apiFetch, resolveApiAssetUrl } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateText, useTranslateTexts } from "@/lib/useTranslate";
import { useThemeStore } from "@/lib/themeStore";
import { Ionicons } from "@expo/vector-icons";
import { makeStyles, AppTheme } from "@/theme";
import { useChatbotStore, ChatMessage } from "@/lib/chatbotStore";
import ScreenHeader from "@/components/ui/ScreenHeader";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    bubbleRow: {
      flexDirection: "row",
      marginVertical: 2,
    },
    botRow: {
      justifyContent: "flex-start",
    },
    userRow: {
      justifyContent: "flex-end",
    },
    bubble: {
      maxWidth: "82%",
      borderRadius: 18,
      borderWidth: 1,
      padding: 12,
      gap: theme.spacing.xs,
    },
    bubbleText: {
      fontSize: theme.fontSize.base,
      lineHeight: 20,
    },
    timeText: {
      fontSize: theme.fontSize.xs,
      marginTop: theme.spacing.xs,
      alignSelf: "flex-end",
    },
    productCard: {
      flexDirection: "row",
      alignItems: "flex-start",
      padding: theme.spacing.sm,
      borderRadius: 10,
      borderWidth: 1,
      gap: theme.spacing.sm,
    },
    productThumb: {
      width: 40,
      height: 40,
      borderRadius: theme.radius.md,
      alignItems: "center",
      justifyContent: "center",
    },
    typingBar: {
      flexDirection: "row",
      alignItems: "center",
      gap: theme.spacing.sm,
      padding: 10,
      paddingHorizontal: theme.spacing.md,
      borderTopWidth: 1,
    },
    inputBar: {
      flexDirection: "row",
      alignItems: "flex-end",
      padding: 10,
      borderTopWidth: 1,
      gap: theme.spacing.sm,
    },
    input: {
      flex: 1,
      borderRadius: 20,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: 10,
      fontSize: theme.fontSize.base,
      maxHeight: 100,
    },
    sendBtn: {
      width: 44,
      height: 44,
      borderRadius: 22,
      alignItems: "center",
      justifyContent: "center",
    },
    onlineDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
    },
    chipRow: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: theme.spacing.xs,
      marginTop: theme.spacing.xs,
    },
    chip: {
      borderWidth: 1,
      borderRadius: 999,
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: 4,
    },
    promptButton: {
      borderWidth: 1,
      borderRadius: 999,
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: 6,
    },
    resultLabel: {
      fontSize: theme.fontSize.xs,
      fontWeight: "700",
      letterSpacing: 1,
      textTransform: "uppercase",
    },
  });

type SearchResult = ChatbotSearchResult;

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  time: string;
  products?: SearchResult[];
  suggestedPrompts?: string[];
  resultMode?: ChatbotResultMode;
  translateText?: boolean;
  translatePrompts?: boolean;
}

function timeNow(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function MessageBubble({
  msg,
  onProductPress,
  recordProductClick,
  onPromptPress,
  typing,
  formatPrice,
}: {
  msg: Message;
  onProductPress: (id: number) => void;
  recordProductClick: (id: number) => void;
  onPromptPress: (prompt: string) => void;
  typing: boolean;
  formatPrice: (amount: number) => string;
}) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const translatedBotText = useTranslateText(msg.translateText ? msg.text : null);
  const translatedPrompts = useTranslateTexts(msg.translatePrompts ? msg.suggestedPrompts ?? [] : []);
  const closeMatchesLabel = useTranslateText(msg.resultMode === "close" ? "Close matches" : null);
  const displayText = msg.translateText ? translatedBotText : msg.text;
  const getProductTags = (product: SearchResult): string[] => {
    const tags = [product.brand, product.category, product.color].filter(
      (value): value is string => Boolean(value && value.trim())
    );
    if (product.sizes?.length) {
      tags.push(`Sizes: ${product.sizes.slice(0, 3).join(", ")}`);
    }
    return tags.slice(0, 4);
  };

  return (
    <View style={[styles.bubbleRow, msg.isBot ? styles.botRow : styles.userRow]}>
      <View
        style={[
          styles.bubble,
          msg.isBot
            ? { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }
            : { backgroundColor: theme.colors.brand },
        ]}
      >
        <Text style={[styles.bubbleText, { color: msg.isBot ? theme.colors.text : theme.colors.onBrand }]}>
          {displayText}
        </Text>

        {msg.products && msg.products.length > 0 && (
          <View style={{ gap: theme.spacing.sm, marginTop: theme.spacing.sm }}>
            {msg.resultMode === "close" && closeMatchesLabel ? (
              <Text style={[styles.resultLabel, { color: theme.colors.textFaint }]}>{closeMatchesLabel}</Text>
            ) : null}

            {msg.products.map((product) => (
              <TouchableOpacity
                key={product.id}
                onPress={() => {
                  recordProductClick(product.id);
                  onProductPress(product.id);
                }}
                style={[
                  styles.productCard,
                  { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border },
                ]}
                activeOpacity={0.8}
              >
                <View style={[styles.productThumb, { backgroundColor: theme.colors.pillActiveBg }]}> 
                  {product.image_url ? (
                    <Image
                      source={{ uri: resolveApiAssetUrl(product.image_url) ?? undefined }}
                      style={{ width: 40, height: 40, borderRadius: theme.radius?.md ?? 8 }}
                      resizeMode="cover"
                    />
                  ) : (
                    <Ionicons name="bag-outline" size={18} color={theme.colors.textMuted} />
                  )}
                </View>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={[s.text, { fontSize: theme.fontSize.sm, fontWeight: "600" }]} numberOfLines={1}>
                    {product.name}
                  </Text>
                  <Text style={{ fontSize: theme.fontSize.sm, color: theme.colors.brand, fontWeight: "700" }}>
                    {formatPrice(product.price)}
                  </Text>
                  <View style={styles.chipRow}>
                    {typeof product.rating === "number" && product.rating > 0 && (
                      <View style={[styles.chip, { backgroundColor: theme.colors.pillActiveBg, borderColor: `${theme.colors.brand}33` }]}>
                        <Text style={{ fontSize: theme.fontSize.xs, color: theme.colors.brand, fontWeight: "700" }}>
                          {product.rating.toFixed(1)} star
                        </Text>
                      </View>
                    )}
                    {getProductTags(product).map((tag) => (
                      <View key={`${product.id}-${tag}`} style={[styles.chip, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
                        <Text style={{ fontSize: theme.fontSize.xs, color: theme.colors.textMuted }}>
                          {tag}
                        </Text>
                      </View>
                    ))}
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {msg.isBot && msg.suggestedPrompts && msg.suggestedPrompts.length > 0 && (
          <View style={styles.chipRow}>
            {msg.suggestedPrompts.map((prompt, index) => (
              <TouchableOpacity
                key={`${msg.id}-${prompt}`}
                onPress={() => onPromptPress(prompt)}
                disabled={typing}
                style={[styles.promptButton, { backgroundColor: theme.colors.pillActiveBg, borderColor: `${theme.colors.brand}33`, opacity: typing ? 0.6 : 1 }]}
              >
                <Text style={{ fontSize: theme.fontSize.xs, color: theme.colors.brand, fontWeight: "700" }}>
                  {translatedPrompts[index] ?? prompt}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <Text style={[styles.timeText, { color: msg.isBot ? theme.colors.textFaint : "rgba(255,255,255,0.6)" }]}> 
          {msg.time}
        </Text>
      </View>
    </View>
  );
}

export default function ChatbotScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const params = useLocalSearchParams<{ supplier?: string | string[] }>();
  const tr = useLocaleStore((state) => state.t);
  const formatPrice = useCurrencyStore((state) => state.format);
  const supplierParam = Array.isArray(params.supplier) ? params.supplier[0] : params.supplier;
  const parsedSupplierId = Number(supplierParam);
  const scopedSupplierId = Number.isInteger(parsedSupplierId) && parsedSupplierId > 0 ? parsedSupplierId : null;

  // Chatbot persistence
  const { sessions, getSession, createSession, addMessage, setActiveSession, getActiveSession } = useChatbotStore();
  const activeSession = getActiveSession();

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (activeSession) {
      return activeSession.messages;
    }
    return [
      {
        id: "1",
        isBot: true,
        text: tr("chatbotGreeting"),
        time: timeNow(),
        resultMode: "none",
        translateText: false,
        translatePrompts: false,
      },
    ];
  });
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(activeSession?.id);
  const listRef = useRef<FlatList>(null);

  // Initialize session once on mount. Reading the store via getState() avoids
  // depending on a freshly-derived `activeSession` object, which would otherwise
  // re-run this effect on every render and cause an infinite setState loop.
  const didInit = useRef(false);
  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;
    const store = useChatbotStore.getState();
    if (!store.activeSessionId) {
      const newSession = store.createSession();
      setSessionId(newSession.id);
      store.setActiveSession(newSession.id);
    } else {
      const session = store.getSession(store.activeSessionId);
      if (session && session.messages.length > 0) {
        // Load messages from existing session (mark bot messages for translation)
        const loadedMessages = session.messages.map((m) => ({
          ...m,
          translateText: m.isBot && !m.translateText,
        }));
        setMessages(loadedMessages);
        setSessionId(session.id);
      }
    }
  }, []);

  // Sync messages to store when they change
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      // Update the session with current messages
      useChatbotStore.setState((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? { ...s, messages, updatedAt: new Date().toISOString() } : s
        ),
      }));
    }
  }, [sessionId, messages]);

  function recordProductClick(productId: number) {
    if (!sessionId) return;
    void apiFetch(`/chatbot/record-click/${productId}`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId }),
    }).catch(() => {
      // Ignore analytics failures during navigation.
    });
  }

  function addBotMessage(
    text: string,
    products?: SearchResult[],
    suggestedPrompts?: string[],
    resultMode: ChatbotResultMode = "none",
    options: { translateText?: boolean; translatePrompts?: boolean } = {}
  ) {
    const msg: ChatMessage = {
      id: generateId(),
      isBot: true,
      text,
      time: timeNow(),
      products,
      suggestedPrompts,
      resultMode,
      translateText: options.translateText ?? false,
      translatePrompts: options.translatePrompts ?? false,
    };
    setMessages((prev) => [...prev, msg]);
    setTyping(false);
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
  }

  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  }

  function addFallbackReply(query: string) {
    addBotMessage(tr(getChatbotReplyKey(query)));
  }

  async function sendMessage(rawQuery: string) {
    const query = rawQuery.trim();
    if (!query || typing) return;

    const userMsg: ChatMessage = {
      id: generateId(),
      isBot: false,
      text: query,
      time: timeNow(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);

    // Create session if needed
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      const newSession = createSession(query);
      currentSessionId = newSession.id;
      setSessionId(currentSessionId);
      setActiveSession(currentSessionId);
    } else {
      // Update session title if it's the first user message
      const currentSession = getSession(currentSessionId);
      if (currentSession && currentSession.messages.length === 0) {
        const title = query.length > 30 ? query.slice(0, 30) + "..." : query;
        useChatbotStore.getState().updateSessionTitle(currentSessionId, title);
      }
    }

    try {
      const supplierScopeQuery = scopedSupplierId ? `?supplier_id=${scopedSupplierId}` : "";
      const data = await apiFetch<ChatbotResponsePayload>(`/chatbot/message${supplierScopeQuery}`, {
        method: "POST",
        body: JSON.stringify({ message: query, session_id: currentSessionId }),
      });

      if (data.session_id && !currentSessionId) {
        setSessionId(data.session_id);
        setActiveSession(data.session_id);
      }

      addBotMessage(
        data.reply,
        data.products && data.products.length > 0 ? data.products : undefined,
        data.suggested_prompts,
        data.result_mode ?? (data.products?.length ? "exact" : "none"),
        { translateText: true, translatePrompts: true }
      );
    } catch {
      setTimeout(() => addFallbackReply(query), 500);
    }
  }

  async function send() {
    await sendMessage(input);
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.colors.surface0 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={90}
    >
      <ScreenHeader
        title={scopedSupplierId ? "Supplier Assistant" : tr("chatbotTitle")}
        subtitle={tr("chatbotOnline")}
        rightIcon="time-outline"
        onRightPress={() => router.push("/chatbot-history" as never)}
      />

      <FlatList
        ref={listRef}
        data={messages}
        ListHeaderComponent={
          scopedSupplierId ? (
            <View
              style={{
                marginBottom: theme.spacing.sm,
                alignSelf: "flex-start",
                borderRadius: 999,
                borderWidth: 1,
                borderColor: `${theme.colors.brand}44`,
                backgroundColor: theme.colors.pillActiveBg,
                paddingHorizontal: theme.spacing.sm,
                paddingVertical: 6,
              }}
            >
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>
                Supplier-focused chat is enabled. Personal details stay private.
              </Text>
            </View>
          ) : null
        }
        keyExtractor={(m) => String(m.id)}
        contentContainerStyle={{ padding: 14, gap: 10, paddingBottom: theme.spacing.xs }}
        renderItem={({ item }) => (
          <MessageBubble
            msg={item}
            formatPrice={formatPrice}
            recordProductClick={recordProductClick}
            onPromptPress={(prompt) => void sendMessage(prompt)}
            typing={typing}
            onProductPress={(id) => router.push(`/(tabs)/products/${id}` as never)}
          />
        )}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
      />

      {typing && (
        <View style={[styles.typingBar, { borderTopColor: theme.colors.border }]}> 
          <ActivityIndicator size="small" color={theme.colors.brand} />
          <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>{tr("loading")}</Text>
        </View>
      )}

      <View style={[styles.inputBar, { backgroundColor: theme.colors.surface1, borderTopColor: theme.colors.border }]}> 
        <TextInput
          style={[styles.input, { color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
          placeholder={tr("chatbotPlaceholder")}
          placeholderTextColor={theme.colors.textMuted}
          value={input}
          onChangeText={setInput}
          returnKeyType="send"
          onSubmitEditing={send}
          editable={!typing}
          multiline
        />
        <TouchableOpacity
          onPress={send}
          disabled={!input.trim() || typing}
          style={[
            styles.sendBtn,
            {
              backgroundColor:
                input.trim() && !typing ? theme.colors.brand : theme.colors.border,
            },
          ]}
        >
          <Text style={{ color: theme.colors.onBrand, fontSize: theme.fontSize.md }}>Go</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
