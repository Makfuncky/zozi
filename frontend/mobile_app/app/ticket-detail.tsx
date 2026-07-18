import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Linking,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { useLocalSearchParams, useRouter } from "expo-router";
import AppHeader from "@/components/ui/AppHeader";
import { apiFetch, resolveApiAssetUrl, uploadTicketAttachment } from "@/lib/api";
import { connectUserRealtimeSocket, isTicketRealtimeMessage } from "@/lib/userRealtime";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme, getStatusColor } from "@/theme";
import { createRealtimeRefreshScheduler } from "@shared/realtime";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface Reply {
  id: number;
  username?: string;
  message: string;
  is_admin: boolean;
  created_at: string;
  attachments: Attachment[];
}

interface Attachment {
  id: number;
  original_name: string;
  file_path: string;
  created_at: string;
}

interface TicketDetail {
  id: number;
  subject: string;
  message: string;
  status: string;
  priority: string;
  ticket_category?: string;
  related_entity_type?: string | null;
  related_entity_id?: number | null;
  created_at: string;
  attachments: Attachment[];
  replies: Reply[];
}

export default function TicketDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);
  const scrollRef = useRef<ScrollView>(null);

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [replyText, setReplyText] = useState("");
  const [uploadingAttachments, setUploadingAttachments] = useState(false);
  const [sending, setSending] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await apiFetch<TicketDetail>(`/tickets/${id}`);
      setTicket(res);
    } catch { /* ignore */ }
  }, [id]);

  useEffect(() => { load().finally(() => setLoading(false)); }, [load]);

  useEffect(() => {
    const ticketId = Number(id);
    if (!Number.isFinite(ticketId)) {
      return;
    }

    const scheduler = createRealtimeRefreshScheduler(async () => {
      await load();
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 200);
    });

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        if (isTicketRealtimeMessage(payload) && payload?.ticket_id === ticketId) {
          scheduler.trigger();
        }
      },
    );


    return () => {
      scheduler.cancel();
      socket?.close();
    };
  }, [id, load]);

  const sendReply = async () => {
    const msg = replyText.trim();
    if (msg.length < 1) return;
    setSending(true);
    try {
      await apiFetch(`/tickets/${id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      setReplyText("");
      await load();
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 200);
    } catch {
      Alert.alert("Error", "Network error. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const pickAttachments = async () => {
    if (!ticket) {
      return;
    }
    const result = await DocumentPicker.getDocumentAsync({
      type: ["image/*", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
      copyToCacheDirectory: true,
      multiple: true,
    });
    if (result.canceled || !result.assets?.length) {
      return;
    }
    setUploadingAttachments(true);
    try {
      for (const asset of result.assets) {
        await uploadTicketAttachment(ticket.id, {
          uri: asset.uri,
          name: asset.name || "attachment",
          mimeType: asset.mimeType,
        });
      }
      await load();
    } catch {
      Alert.alert("Error", "Attachment upload failed. Please try again.");
    } finally {
      setUploadingAttachments(false);
    }
  };

  const headerTitle = ticket ? `Ticket #${ticket.id}` : "Ticket";
  const isClosed = ticket ? (ticket.status === "resolved" || ticket.status === "closed") : false;

  return (
    <>
      <AppHeader showSearch={false} />
      {loading ? (
        <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
          <LoadingSpinner />
        </View>
      ) : !ticket ? (
        <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
          <Text style={{ color: theme.colors.textMuted }}>Ticket not found.</Text>
        </View>
      ) : (
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView
          ref={scrollRef}
          style={[s.container, { flex: 1 }]}
          contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 120 }}
        >
          {/* Header */}
          <View style={[localStyles.headerCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontSize: theme.fontSize.md, fontWeight: "700", marginBottom: 6 }]}>{ticket.subject}</Text>
            <View style={{ flexDirection: "row", gap: theme.spacing.sm, flexWrap: "wrap", marginBottom: 10 }}>
              <View style={[localStyles.badge, { backgroundColor: getStatusColor(ticket.status, theme).bg, borderColor: getStatusColor(ticket.status, theme).color }]}>
                <Text style={{ color: getStatusColor(ticket.status, theme).color, fontWeight: "700", fontSize: theme.fontSize.sm, textTransform: "capitalize" }}>{ticket.status}</Text>
              </View>
              {ticket.ticket_category ? (
                <View style={[localStyles.badge, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={{ color: theme.colors.textMuted, fontWeight: "700", fontSize: theme.fontSize.sm, textTransform: "capitalize" }}>
                    {ticket.ticket_category.replace("_", " ")}
                  </Text>
                </View>
              ) : null}
              {ticket.related_entity_type && ticket.related_entity_id ? (
                <View style={[localStyles.badge, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={{ color: theme.colors.textMuted, fontWeight: "700", fontSize: theme.fontSize.sm }}>
                    {ticket.related_entity_type} #{ticket.related_entity_id}
                  </Text>
                </View>
              ) : null}
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, alignSelf: "center" }}>
                {new Date(ticket.created_at).toLocaleDateString()}
              </Text>
            </View>
            {/* Original message */}
            <View style={[localStyles.messageBubble, { backgroundColor: theme.colors.pillActiveBg, borderColor: theme.colors.brand }]}>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginBottom: theme.spacing.xs }}>Your original message:</Text>
              <Text style={[s.text, { fontSize: theme.fontSize.base, lineHeight: 20 }]}>{ticket.message}</Text>
            </View>
            {ticket.attachments.length > 0 && (
              <View style={{ marginTop: theme.spacing.md, gap: theme.spacing.xs }}>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, fontWeight: "700" }}>Attachments</Text>
                {ticket.attachments.map((attachment) => (
                  <TouchableOpacity
                    key={attachment.id}
                    onPress={() => {
                      const href = resolveApiAssetUrl(attachment.file_path);
                      if (href) {
                        void Linking.openURL(href);
                      }
                    }}
                  >
                    <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>{attachment.original_name}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          {/* Replies */}
          {ticket.replies.length > 0 && (
            <Text style={[s.text, { fontWeight: "700", marginTop: 20, marginBottom: 10 }]}>
              Replies ({ticket.replies.length})
            </Text>
          )}
          {ticket.replies.map((reply) => (
            <View
              key={reply.id}
              style={[
                localStyles.replyBubble,
                reply.is_admin
                  ? { backgroundColor: theme.colors.brand, alignSelf: "flex-start" }
                  : { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1, alignSelf: "flex-end" },
              ]}
            >
              {reply.is_admin && (
                <Text style={{ color: theme.colors.onBrand, fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: theme.spacing.xs }}>ZOZI Support</Text>
              )}
              <Text style={{ color: reply.is_admin ? theme.colors.onBrand : theme.colors.text, lineHeight: 20 }}>
                {reply.message}
              </Text>
              <Text style={{ color: reply.is_admin ? "rgba(255,255,255,0.6)" : theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: theme.spacing.xs, textAlign: "right" }}>
                {new Date(reply.created_at).toLocaleDateString()}
              </Text>
              {reply.attachments.length > 0 && (
                <View style={{ marginTop: theme.spacing.sm, gap: theme.spacing.xs }}>
                  {reply.attachments.map((attachment) => (
                    <TouchableOpacity
                      key={attachment.id}
                      onPress={() => {
                        const href = resolveApiAssetUrl(attachment.file_path);
                        if (href) {
                          void Linking.openURL(href);
                        }
                      }}
                    >
                      <Text style={{ color: reply.is_admin ? theme.colors.onBrand : theme.colors.brand, fontWeight: "700" }}>{attachment.original_name}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>
          ))}

          {ticket.replies.length === 0 && (
            <Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 20 }}>
              No replies yet. We'll get back to you soon!
            </Text>
          )}

          {isClosed && (
            <View style={[localStyles.closedBanner, { backgroundColor: theme.colors.statusReturned + "22", borderColor: theme.colors.statusReturned }]}>
              <Text style={{ color: theme.colors.statusReturned, textAlign: "center", fontWeight: "600" }}>
                This ticket is {ticket.status} — no further replies can be added.
              </Text>
            </View>
          )}
        </ScrollView>

        {/* Reply input */}
        {!isClosed && (
          <View style={[localStyles.replyBar, { backgroundColor: theme.colors.surface0, borderTopColor: theme.colors.border }]}>
            <TouchableOpacity
              style={[localStyles.attachmentBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }, uploadingAttachments && { opacity: 0.6 }]}
              onPress={pickAttachments}
              disabled={uploadingAttachments}
            >
              <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.sm }}>
                {uploadingAttachments ? "Uploading…" : "Files"}
              </Text>
            </TouchableOpacity>
            <TextInput
              style={[localStyles.replyInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 }]}
              value={replyText}
              onChangeText={setReplyText}
              placeholder="Write a reply…"
              placeholderTextColor={theme.colors.textMuted}
              multiline
              maxLength={5000}
            />
            <TouchableOpacity
              style={[localStyles.sendBtn, { backgroundColor: theme.colors.brand }, (sending || replyText.trim().length === 0) && { opacity: 0.5 }]}
              onPress={sendReply}
              disabled={sending || replyText.trim().length === 0}
            >
              {sending
                ? <ActivityIndicator color={theme.colors.onBrand} size="small" />
                :               <Text style={{ color: theme.colors.onBrand, fontWeight: "700", fontSize: theme.fontSize.sm }}>Send</Text>}
            </TouchableOpacity>
          </View>
        )}
      </KeyboardAvoidingView>
      )}
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  headerCard: {
    borderWidth: 1,
    borderRadius: 14,
    padding: theme.spacing.md,
  },
  badge: {
    borderWidth: 1,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  messageBubble: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
  },
  replyBubble: {
    borderRadius: theme.radius.lg,
    padding: 12,
    marginBottom: 10,
    maxWidth: "85%",
  },
  closedBanner: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginTop: 20,
  },
  replyBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: 12,
    borderTopWidth: 1,
    gap: 10,
  },
  attachmentBtn: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  replyInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: theme.spacing.sm,
    maxHeight: 100,
    fontSize: theme.fontSize.base,
  },
  sendBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    minWidth: 60,
  },
});
