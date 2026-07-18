import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  FlatList,
  TextInput,
  TouchableOpacity,
  Alert,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import AppHeader from "@/components/ui/AppHeader";
import * as DocumentPicker from "expo-document-picker";
import { apiFetch, uploadTicketAttachment } from "@/lib/api";
import { connectUserRealtimeSocket, isTicketRealtimeMessage } from "@/lib/userRealtime";
import { useThemeStore } from "@/lib/themeStore";
import { Ionicons } from "@expo/vector-icons";
import { makeStyles, AppTheme, getStatusColor } from "@/theme";
import { createRealtimeRefreshScheduler } from "@shared/realtime";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

type Priority = "low" | "normal" | "high" | "urgent";

const PRIORITY_COLORS: Record<Priority, string> = {
  low: "#9ca3af",
  normal: "#22c55e",
  high: "#f59e0b",
  urgent: "#ef4444",
};
type Status = "open" | "pending" | "in_progress" | "resolved" | "closed";

interface TicketSummary {
  id: number;
  subject: string;
  status: Status;
  priority: Priority;
  ticket_category?: "customer" | "supplier" | "logistics_partner";
  created_at: string;
  reply_count: number;
}

// â”€â”€ Ticket List Screen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function TicketsScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await apiFetch<TicketSummary[]>("/tickets");
      setTickets(Array.isArray(data) ? data : []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load().finally(() => setLoading(false)); }, [load]);
  useEffect(() => {
    const scheduler = createRealtimeRefreshScheduler(load);

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        if (isTicketRealtimeMessage(payload)) {
          scheduler.trigger();
        }
      },
    );


    return () => {
      scheduler.cancel();
      socket?.close();
    };
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  if (loading) {
    return (
      <>
        <AppHeader showSearch={false} />
          <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
            <LoadingSpinner />
          </View>
      </>
    );
  }

  if (showCreate) {
    return (
      <CreateTicketForm
        theme={theme}
        s={s}
        onBack={() => setShowCreate(false)}
        onCreated={() => { setShowCreate(false); load(); }}
      />
    );
  }

  return (
    <>
      <AppHeader showSearch={false} />
      <FlatList
        style={[s.container, { flex: 1 }]}
        contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40, flexGrow: 1 }}
        data={tickets}
        keyExtractor={(t) => String(t.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[localStyles.ticketCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
            onPress={() => router.push({ pathname: "/ticket-detail", params: { id: String(item.id) } } as never)}
          >
            <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 6 }}>
              <Text style={[s.text, { fontWeight: "700", flex: 1, marginRight: theme.spacing.sm }]} numberOfLines={1}>
                {item.subject}
              </Text>
              <StatusBadge status={item.status} />
            </View>
            <View style={{ flexDirection: "row", gap: theme.spacing.sm, alignItems: "center" }}>
              <Badge label={item.priority} color={PRIORITY_COLORS[item.priority]} small />
              {item.ticket_category ? <Badge label={item.ticket_category.replace("_", " ")} color={theme.colors.textMuted} small /> : null}
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
                {new Date(item.created_at).toLocaleDateString()}
              </Text>
              {item.reply_count > 0 && (
                <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                  <Ionicons name="chatbubble-outline" size={14} color={theme.colors.brand} />
                  <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm }}>
                    {item.reply_count}
                  </Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={{ flex: 1, alignItems: "center", justifyContent: "center", paddingTop: 60 }}>
            <Ionicons name="ticket-outline" size={28} color={theme.colors.brand} style={{ marginBottom: 12 }} />
            <Text style={[s.text, { fontSize: theme.fontSize.md, fontWeight: "600", marginBottom: 6 }]}>No tickets yet</Text>
            <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>
              Need help? Open a support ticket.
            </Text>
            <TouchableOpacity
              style={[localStyles.createBtn, { backgroundColor: theme.colors.brand, marginTop: 20 }]}
              onPress={() => setShowCreate(true)}
            >
              <Text style={{ color: "#fff", fontWeight: "700" }}>Open a Ticket</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </>
  );
}

// â”€â”€ Create Form â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function CreateTicketForm({
  theme,
  s,
  onBack,
  onCreated,
}: {
  theme: ReturnType<typeof import("@/theme").getTheme>;
  s: ReturnType<typeof import("@/theme").makeStyles>;
  onBack: () => void;
  onCreated: () => void;
}) {
  const localStyles = createLocalStyles(theme);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [priority, setPriority] = useState<Priority>("normal");
  const [attachments, setAttachments] = useState<DocumentPicker.DocumentPickerAsset[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const priorities: Priority[] = ["low", "normal", "high", "urgent"];

  const submit = async () => {
    if (subject.trim().length < 3) return Alert.alert("Error", "Subject must be at least 3 characters.");
    if (message.trim().length < 10) return Alert.alert("Error", "Message must be at least 10 characters.");
    setSubmitting(true);
    try {
      const created = await apiFetch<{ id: number }>("/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: subject.trim(), message: message.trim(), priority }),
      });
      for (const asset of attachments) {
        await uploadTicketAttachment(created.id, {
          uri: asset.uri,
          name: asset.name || "attachment",
          mimeType: asset.mimeType,
        });
      }
      Alert.alert("Submitted", "Your ticket has been created. Our team will respond soon.");
      onCreated();
    } catch (err: any) {
      Alert.alert("Error", err?.message ?? "Network error. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <AppHeader onBack={onBack} showSearch={false} />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView style={[s.container, { flex: 1 }]} contentContainerStyle={{ padding: theme.spacing.md, gap: theme.spacing.md, paddingBottom: 40 }}>
          <Text style={[s.text, { fontWeight: "600", marginBottom: theme.spacing.xs }]}>Subject</Text>
          <TextInput
            style={[localStyles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 }]}
            value={subject}
            onChangeText={setSubject}
            placeholder="Briefly describe your issue"
            placeholderTextColor={theme.colors.textMuted}
            maxLength={200}
          />

          <Text style={[s.text, { fontWeight: "600", marginBottom: theme.spacing.xs, marginTop: theme.spacing.sm }]}>Priority</Text>
          <View style={{ flexDirection: "row", gap: theme.spacing.sm }}>
            {priorities.map((p) => (
              <TouchableOpacity
                key={p}
                style={[
                  localStyles.priorityBtn,
                  {
                    backgroundColor: priority === p ? PRIORITY_COLORS[p] + "33" : theme.colors.surface1,
                    borderColor: priority === p ? PRIORITY_COLORS[p] : theme.colors.border,
                  },
                ]}
                onPress={() => setPriority(p)}
              >
                <Text style={{ color: priority === p ? PRIORITY_COLORS[p] : theme.colors.textMuted, fontSize: theme.fontSize.sm, fontWeight: "600", textTransform: "capitalize" }}>
                  {p}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={[s.text, { fontWeight: "600", marginBottom: theme.spacing.xs, marginTop: theme.spacing.sm }]}>Message</Text>
          <TextInput
            style={[
              localStyles.input,
              localStyles.textarea,
              { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 },
            ]}
            value={message}
            onChangeText={setMessage}
            placeholder="Describe your issue in detail (min. 10 characters)"
            placeholderTextColor={theme.colors.textMuted}
            multiline
            numberOfLines={6}
            textAlignVertical="top"
            maxLength={5000}
          />
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, textAlign: "right" }}>{message.length}/5000</Text>

          <Text style={[s.text, { fontWeight: "600", marginBottom: theme.spacing.xs, marginTop: theme.spacing.sm }]}>Attachments</Text>
          <TouchableOpacity
            style={[localStyles.priorityBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
            onPress={async () => {
              const result = await DocumentPicker.getDocumentAsync({
                type: ["image/*", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
                copyToCacheDirectory: true,
                multiple: true,
              });
              if (!result.canceled && result.assets?.length) {
                setAttachments(result.assets);
              }
            }}
          >
            <Text style={{ color: theme.colors.text, fontWeight: "600" }}>
              {attachments.length > 0 ? `Selected ${attachments.length} file${attachments.length === 1 ? "" : "s"}` : "Add supporting files"}
            </Text>
          </TouchableOpacity>
          {attachments.length > 0 && (
            <View style={{ gap: theme.spacing.xs }}>
              {attachments.map((asset, index) => (
                <Text key={`${asset.uri}-${index}`} style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }} numberOfLines={1}>
                  {asset.name || `Attachment ${index + 1}`}
                </Text>
              ))}
            </View>
          )}

          <Button label="Submit Ticket" onPress={submit} loading={submitting} style={{ marginTop: theme.spacing.sm }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </>
  );
}

// â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function Badge({ label, color, small = false }: { label: string; color: string; small?: boolean }) {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  return (
    <View style={[localStyles.badge, { backgroundColor: color + "22", borderColor: color }]}>
      <Text style={[{ color, fontWeight: "600", textTransform: "capitalize" }, small ? { fontSize: theme.fontSize.xs } : { fontSize: theme.fontSize.xs }]}>
        {label}
      </Text>
    </View>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  ticketCard: {
    borderWidth: 1,
    borderRadius: theme.radius.lg,
    padding: 14,
    marginBottom: 10,
  },
  badge: {
    borderWidth: 1,
    borderRadius: 100,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 2,
  },
  createBtn: {
    paddingVertical: 14,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    alignItems: "center",
    justifyContent: "center",
  },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: theme.fontSize.base,
  },
  textarea: {
    minHeight: 140,
    paddingTop: 10,
  },
  priorityBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingVertical: theme.spacing.sm,
    alignItems: "center",
  },
});
