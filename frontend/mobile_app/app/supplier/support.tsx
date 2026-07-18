import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  TextInput,
} from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { toast } from "@/lib/toastStore";

type SupportView = "tickets" | "disputes";
type TicketPriority = "low" | "normal" | "high" | "urgent";

interface TicketSummary {
  id: number;
  subject: string;
  status: string;
  priority: TicketPriority;
  ticket_category?: string;
  created_at: string;
  reply_count?: number;
}

interface SupplierDispute {
  id: number;
  dispute_type: string;
  priority: string;
  status: string;
  title?: string | null;
  description: string;
  related_order_id?: number | null;
  created_at?: string | null;
  admin_notes?: string | null;
  resolution_notes?: string | null;
}

interface SupplierDisputePayload {
  data?: SupplierDispute[];
}

interface DisputeFormState {
  dispute_type: string;
  priority: TicketPriority;
  title: string;
  description: string;
  related_order_id: string;
}

const DISPUTE_TYPES = [
  { value: "return", label: "Return" },
  { value: "payout", label: "Payout" },
  { value: "order", label: "Order" },
  { value: "other", label: "Other" },
] as const;

const PRIORITIES: TicketPriority[] = ["low", "normal", "high", "urgent"];

const STATUS_COLORS: Record<string, string> = {
  open: "#32CD32",
  pending: "#f59e0b",
  in_progress: "#0ea5e9",
  under_review: "#0ea5e9",
  resolved: "#22c55e",
  closed: "#6b7280",
  rejected: "#ef4444",
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 12, paddingBottom: 40 },
    hero: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    statsRow: { flexDirection: "row", gap: 10, flexWrap: "wrap" },
    statCard: { flexGrow: 1, minWidth: 100, borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
    statValue: { fontSize: theme.fontSize.lg, fontWeight: "800" },
    segmented: { flexDirection: "row", borderRadius: theme.radius.lg, borderWidth: 1, padding: 4, gap: 6 },
    segmentButton: { flex: 1, borderRadius: theme.radius.md, paddingVertical: 10, alignItems: "center" },
    card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 12 },
    helperCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 10 },
    ticketRow: { borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 6 },
    badge: { borderRadius: 999, paddingHorizontal: 8, paddingVertical: 2, alignSelf: "flex-start" },
    optionRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    optionChip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8 },
    helperChip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 10, paddingVertical: 6 },
    input: {
      borderWidth: 1,
      borderRadius: theme.radius.lg,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      backgroundColor: theme.colors.surface0,
      color: theme.colors.text,
    },
  });

function createDefaultDisputeForm(): DisputeFormState {
  return {
    dispute_type: "other",
    priority: "normal",
    title: "",
    description: "",
    related_order_id: "",
  };
}

export default function SupplierSupportScreen() {
  const params = useLocalSearchParams<{ section?: string }>();
  const router = useRouter();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);

  const [view, setView] = useState<SupportView>(params.section === "disputes" ? "disputes" : "tickets");
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [disputes, setDisputes] = useState<SupplierDispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [disputeForm, setDisputeForm] = useState<DisputeFormState>(createDefaultDisputeForm());

  useEffect(() => {
    setView(params.section === "disputes" ? "disputes" : "tickets");
  }, [params.section]);

  const loadWorkspace = useCallback(async (silent = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [ticketData, disputeData] = await Promise.all([
        apiFetch<TicketSummary[]>("/tickets").catch(() => []),
        apiFetch<SupplierDisputePayload>("/supplier/disputes").catch(() => ({ data: [] })),
      ]);
      setTickets(Array.isArray(ticketData) ? ticketData : []);
      setDisputes(Array.isArray(disputeData.data) ? disputeData.data : []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  const ticketSummary = useMemo(() => ({
    open: tickets.filter((ticket) => ticket.status === "open").length,
    active: tickets.filter((ticket) => ticket.status === "in_progress").length,
    resolved: tickets.filter((ticket) => ticket.status === "resolved" || ticket.status === "closed").length,
  }), [tickets]);

  const disputeSummary = useMemo(() => ({
    pending: disputes.filter((dispute) => dispute.status === "pending").length,
    review: disputes.filter((dispute) => dispute.status === "under_review").length,
    resolved: disputes.filter((dispute) => dispute.status === "resolved").length,
  }), [disputes]);
  const urgentTicketCount = useMemo(() => tickets.filter((ticket) => ticket.priority === "high" || ticket.priority === "urgent").length, [tickets]);
  const openDisputeCount = useMemo(() => disputes.filter((dispute) => dispute.status !== "resolved" && dispute.status !== "closed").length, [disputes]);

  const switchView = (nextView: SupportView) => {
    setView(nextView);
    router.replace(nextView === "disputes" ? "/supplier/support?section=disputes" as never : "/supplier/support" as never);
  };

  const updateDisputeField = (field: keyof DisputeFormState, value: string) => {
    setDisputeForm((current) => ({ ...current, [field]: value }));
  };

  const submitDispute = async () => {
    if (!disputeForm.description.trim()) {
      toast.error("Describe the issue before submitting a dispute");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch("/supplier/disputes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dispute_type: disputeForm.dispute_type,
          priority: disputeForm.priority,
          title: disputeForm.title.trim() || undefined,
          description: disputeForm.description.trim(),
          related_order_id: disputeForm.related_order_id.trim() ? Number(disputeForm.related_order_id) : undefined,
        }),
      });
      toast.success("Dispute submitted for admin review");
      setDisputeForm(createDefaultDisputeForm());
      setView("disputes");
      await loadWorkspace(true);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to submit dispute");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView
      testID="supplier-support-screen"
      style={s.container}
      contentContainerStyle={styles.scroll}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void loadWorkspace(true)} tintColor={theme.colors.brand} />}
    >
      <Stack.Screen options={{ title: "Support" }} />

      <View style={[styles.hero, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
        <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>Supplier Support</Text>
        <Text style={s.textMuted}>Keep ticket follow-up and supplier disputes in one mobile workspace.</Text>
      </View>

      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.statValue, { color: theme.colors.brand }]}>{ticketSummary.open}</Text>
          <Text style={s.textMuted}>Open tickets</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.statValue, { color: theme.colors.warning }]}>{disputeSummary.pending + disputeSummary.review}</Text>
          <Text style={s.textMuted}>Active disputes</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.statValue, { color: theme.colors.success }]}>{ticketSummary.resolved + disputeSummary.resolved}</Text>
          <Text style={s.textMuted}>Resolved items</Text>
        </View>
      </View>

      <View style={[styles.segmented, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
        {[
          { key: "tickets", label: "Support Requests" },
          { key: "disputes", label: "Dispute Cases" },
        ].map((item) => (
          <TouchableOpacity
            key={item.key}
            testID={`supplier-support-tab-${item.key}`}
            style={[styles.segmentButton, { backgroundColor: view === item.key ? theme.colors.brand : "transparent" }]}
            onPress={() => switchView(item.key as SupportView)}
          >
            <Text style={{ color: view === item.key ? theme.colors.onBrand : theme.colors.text, fontWeight: "700" }}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={[styles.helperCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
        <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Fastest path for supplier issues</Text>
        <Text style={s.textMuted}>
          Use support requests for operational blockers and use disputes when you need an admin decision on payouts, returns, or order exceptions.
        </Text>
        <View style={styles.optionRow}>
          <View style={[styles.helperChip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{urgentTicketCount} urgent tickets</Text>
          </View>
          <View style={[styles.helperChip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{openDisputeCount} open disputes</Text>
          </View>
        </View>
        {view === "tickets" ? (
          <Button label="Create or Review Tickets" onPress={() => router.push("/tickets" as never)} />
        ) : null}
      </View>

      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" />
      ) : view === "tickets" ? (
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Support Requests</Text>
          <Text style={s.textMuted}>Open the full ticket center to create or manage operational help requests.</Text>
          <Button testID="supplier-support-open-ticket-center" label="Open Ticket Center" onPress={() => router.push("/tickets" as never)} />
          {tickets.length > 0 ? tickets.slice(0, 5).map((ticket) => (
            <TouchableOpacity
              key={ticket.id}
              style={[styles.ticketRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}
              onPress={() => router.push({ pathname: "/ticket-detail", params: { id: String(ticket.id) } } as never)}
            >
              <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 8 }}>
                <Text style={[s.text, { flex: 1, fontWeight: "700" }]} numberOfLines={1}>#{ticket.id} {ticket.subject}</Text>
                <View style={[styles.badge, { backgroundColor: (STATUS_COLORS[ticket.status] || theme.colors.textMuted) + "22" }]}> 
                  <Text style={{ color: STATUS_COLORS[ticket.status] || theme.colors.textMuted, fontSize: theme.fontSize.xs, fontWeight: "700" }}>{ticket.status.replace(/_/g, " ")}</Text>
                </View>
              </View>
              <Text style={s.textMuted}>Priority {ticket.priority} · {new Date(ticket.created_at).toLocaleDateString()}</Text>
            </TouchableOpacity>
          )) : (
            <Text style={s.textMuted}>No support tickets yet.</Text>
          )}
        </View>
      ) : (
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>New dispute case</Text>
          <Text style={s.textMuted}>Add the order reference if the case is tied to a shipment, return, or payout so admins can resolve it faster.</Text>
          <View style={styles.optionRow}>
            {DISPUTE_TYPES.map((type) => (
              <TouchableOpacity
                key={type.value}
                style={[
                  styles.optionChip,
                  { borderColor: disputeForm.dispute_type === type.value ? theme.colors.brand : theme.colors.border, backgroundColor: disputeForm.dispute_type === type.value ? theme.colors.brand + "18" : theme.colors.surface0 },
                ]}
                onPress={() => updateDisputeField("dispute_type", type.value)}
              >
                <Text style={{ color: disputeForm.dispute_type === type.value ? theme.colors.brand : theme.colors.text, fontWeight: "600" }}>{type.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <View style={styles.optionRow}>
            {PRIORITIES.map((priority) => (
              <TouchableOpacity
                key={priority}
                style={[
                  styles.optionChip,
                  { borderColor: disputeForm.priority === priority ? theme.colors.brand : theme.colors.border, backgroundColor: disputeForm.priority === priority ? theme.colors.brand + "18" : theme.colors.surface0 },
                ]}
                onPress={() => updateDisputeField("priority", priority)}
              >
                <Text style={{ color: disputeForm.priority === priority ? theme.colors.brand : theme.colors.text, fontWeight: "600" }}>{priority}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <TextInput testID="supplier-support-dispute-title" value={disputeForm.title} onChangeText={(value) => updateDisputeField("title", value)} placeholder="Short title (optional)" placeholderTextColor={theme.colors.textMuted} style={[styles.input, { borderColor: theme.colors.border }]} />
          <TextInput testID="supplier-support-related-order" value={disputeForm.related_order_id} onChangeText={(value) => updateDisputeField("related_order_id", value)} placeholder="Related order ID (optional)" placeholderTextColor={theme.colors.textMuted} keyboardType="number-pad" style={[styles.input, { borderColor: theme.colors.border }]} />
          <TextInput testID="supplier-support-dispute-description" value={disputeForm.description} onChangeText={(value) => updateDisputeField("description", value)} placeholder="Describe the issue and what resolution you need" placeholderTextColor={theme.colors.textMuted} multiline numberOfLines={5} style={[styles.input, { borderColor: theme.colors.border, minHeight: 110, textAlignVertical: "top" }]} />
          <Button testID="supplier-support-submit-dispute" label={submitting ? "Submitting..." : "Submit Dispute"} onPress={() => void submitDispute()} disabled={submitting} />

          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md, marginTop: 4 }]}>Recent disputes</Text>
          {disputes.length > 0 ? disputes.slice(0, 5).map((dispute) => (
            <View key={dispute.id} style={[styles.ticketRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 8 }}>
                <Text style={[s.text, { flex: 1, fontWeight: "700" }]} numberOfLines={1}>#{dispute.id} {dispute.title || dispute.dispute_type}</Text>
                <View style={[styles.badge, { backgroundColor: (STATUS_COLORS[dispute.status] || theme.colors.textMuted) + "22" }]}> 
                  <Text style={{ color: STATUS_COLORS[dispute.status] || theme.colors.textMuted, fontSize: theme.fontSize.xs, fontWeight: "700" }}>{dispute.status.replace(/_/g, " ")}</Text>
                </View>
              </View>
              <Text style={s.textMuted} numberOfLines={3}>{dispute.description}</Text>
              <Text style={s.textMuted}>Priority {dispute.priority}{dispute.related_order_id ? ` · Order #${dispute.related_order_id}` : ""}</Text>
            </View>
          )) : (
            <Text style={s.textMuted}>No disputes submitted yet.</Text>
          )}
        </View>
      )}
    </ScrollView>
  );
}