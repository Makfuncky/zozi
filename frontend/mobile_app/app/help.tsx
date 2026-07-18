import React, { useCallback, useEffect, useState } from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { useRouter } from "expo-router";
import AppHeader from "@/components/ui/AppHeader";
import { getTickets, createTicket, type Ticket } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const createStyles = (theme: AppTheme) => StyleSheet.create({
    successBox: {
      padding: 10,
      borderRadius: theme.radius.md,
      borderWidth: 1,
      marginBottom: 4,
    },
  scroll: {
    padding: theme.spacing.md,
    gap: 12,
    paddingBottom: 40,
  },
  faqItem: {
    padding: 14,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
  },
  faqHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  divider: {
    height: 1,
    backgroundColor: "transparent",
    marginVertical: theme.spacing.xs,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  newBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
  },
  form: {
    padding: theme.spacing.md,
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    gap: 12,
  },
  errorBox: {
    padding: 10,
    borderRadius: theme.radius.md,
    borderWidth: 1,
  },
  priorityRow: {
    flexDirection: "row",
    gap: theme.spacing.sm,
  },
  priorityBtn: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: "center",
  },
  ticketRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    gap: 10,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.xl,
    borderWidth: 1,
  },
});

const FAQ_ITEMS = [
  {
    q: "How do I track my order?",
    a: "Go to My Orders in your profile to see real-time tracking for all your orders.",
  },
  {
    q: "Can I return a product?",
    a: "Return windows vary by product and start after delivery. Check the product details or your order page before requesting a return.",
  },
  {
    q: "How do I apply a coupon?",
    a: "Enter your coupon code at checkout before placing your order.",
  },
  {
    q: "How long does delivery take?",
    a: "Standard delivery takes 3–7 business days depending on your location.",
  },
  {
    q: "Is my payment secure?",
    a: "Yes, all payments are processed through Stripe or Tap Payments — both are PCI-DSS compliant.",
  },
];

function FaqItem({ q, a }: { q: string; a: string }) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const [open, setOpen] = useState(false);


  return (
    <TouchableOpacity
      onPress={() => setOpen(!open)}
      style={[styles.faqItem, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
      activeOpacity={0.8}
    >
      <View style={styles.faqHeader}>
        <Text style={[s.text, { flex: 1, fontWeight: "600" }]}>{q}</Text>
        <Ionicons name={open ? "chevron-up" : "chevron-down"} size={16} color={theme.colors.brand} />
      </View>
      {open && (
        <Text style={[s.textMuted, { marginTop: theme.spacing.sm, lineHeight: 20 }]}>{a}</Text>
      )}
    </TouchableOpacity>
  );
}

function TicketRow({ ticket, onPress }: { ticket: Ticket; onPress: () => void }) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);

  let statusColor: string = theme.colors.textMuted;
  let statusIcon: "time-outline" | "alert-circle-outline" | "checkmark-circle-outline" = "time-outline";
  let statusText = ticket.status.replace("_", " ");
  if (ticket.status === "open") { statusColor = theme.colors.brand; statusIcon = "time-outline"; }
  else if (ticket.status === "in_progress") { statusColor = theme.colors.warning; statusIcon = "alert-circle-outline"; }
  else if (ticket.status === "closed" || ticket.status === "resolved") { statusColor = theme.colors.success; statusIcon = "checkmark-circle-outline"; }

  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.ticketRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
      activeOpacity={0.8}
    >
      <View style={{ flex: 1, gap: theme.spacing.xs }}>
        <Text style={[s.text, { fontWeight: "600" }]} numberOfLines={1}>{ticket.subject}</Text>
        <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>
          {new Date(ticket.created_at).toLocaleDateString()}
        </Text>
      </View>
      <View style={[styles.statusBadge, { backgroundColor: statusColor + "22", borderColor: statusColor, flexDirection: "row", alignItems: "center", gap: 4 }]}> 
        <Ionicons name={statusIcon} size={12} color={statusColor} />
        <Text style={{ color: statusColor, fontSize: theme.fontSize.sm, fontWeight: "600", textTransform: "capitalize" }}>
          {statusText}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

export default function HelpScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { isLoggedIn } = useAuthStore();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [priority, setPriority] = useState<"low" | "normal" | "high" | "urgent">("normal");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const loadTickets = useCallback(async () => {
    if (!isLoggedIn) return;
    setLoadingTickets(true);
    try {
      const data = await getTickets();
      setTickets(data);
    } catch {}
    finally { setLoadingTickets(false); }
  }, [isLoggedIn]);

  useEffect(() => { loadTickets(); }, [loadTickets]);

  async function handleSubmit() {
    setFormError(null);
    setFormSuccess(null);
    if (!subject.trim()) return setFormError("Subject is required");
    if (!message.trim()) return setFormError("Message is required");
    if (subject.trim().length < 3) return setFormError("Subject must be at least 3 characters");
    if (message.trim().length < 10) return setFormError("Message must be at least 10 characters");

    setSubmitting(true);
    try {
      const ticket = await createTicket({ subject: subject.trim(), message: message.trim(), priority });
      setTickets((prev) => [ticket, ...prev]);
      setSubject("");
      setMessage("");
      setPriority("normal");
      setFormSuccess("Ticket Submitted! We'll get back to you as soon as possible.");
      setShowForm(false);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to submit ticket. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <AppHeader showSearch={false} />
      <ScrollView
        contentContainerStyle={[styles.scroll, { backgroundColor: theme.colors.surface0 }]}
        keyboardShouldPersistTaps="handled"
      >
        {/* FAQ */}
        <Text style={[s.title, { fontSize: theme.fontSize.md }]}>Frequently Asked Questions</Text>
        {FAQ_ITEMS.map((item, i) => (
          <FaqItem key={i} q={item.q} a={item.a} />
        ))}

        {/* Support tickets */}
        <View style={styles.divider} />
        <View style={styles.sectionHeader}>
          <Text style={[s.title, { fontSize: theme.fontSize.md, flex: 1 }]}>Support Tickets</Text>
          {isLoggedIn && (
            <View style={{ flexDirection: "row", gap: 8 }}>
              <TouchableOpacity
                onPress={() => router.push("/tickets" as never)}
                style={[styles.newBtn, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1 }]}
              >
                <Text style={{ color: theme.colors.textMuted, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                  All tickets
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setShowForm(!showForm)}
                style={[styles.newBtn, { backgroundColor: theme.colors.brand }]}
              >
                <Text style={{ color: theme.colors.onBrand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                  {showForm ? "Cancel" : "+ New"}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {!isLoggedIn && (
          <Text style={[s.textMuted, { textAlign: "center" }]}>
            Sign in to view or create support tickets.
          </Text>
        )}

        {isLoggedIn && showForm && (
          <View style={[styles.form, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>New Support Ticket</Text>

            {formSuccess && (
              <View                 style={[styles.successBox, { backgroundColor: theme.colors.successBg, borderColor: theme.colors.success }]}>  
                <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm }}>{formSuccess}</Text>
              </View>
            )}
            {formError && (
              <View                 style={[styles.errorBox, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}>  
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm }}>{formError}</Text>
              </View>
            )}

            <Input
              label="Subject"
              placeholder="Brief description of your issue"
              value={subject}
              onChangeText={(t) => { setSubject(t); setFormError(null); setFormSuccess(null); }}
            />
            <Input
              label="Message"
              placeholder="Describe your issue in detail..."
              value={message}
              onChangeText={(t) => { setMessage(t); setFormError(null); setFormSuccess(null); }}
              multiline
              numberOfLines={5}
            />

            {/* Priority picker */}
            <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, marginBottom: theme.spacing.xs }]}>Priority</Text>
            <View style={styles.priorityRow}>
              {(["low", "normal", "high", "urgent"] as const).map((p) => {
                const sublabels: Record<string, string> = {
                  low: "General inquiry",
                  normal: "Default",
                  high: "Affects my orders",
                  urgent: "Critical issue",
                };
                return (
                  <TouchableOpacity
                    key={p}
                    onPress={() => setPriority(p)}
                    style={[
                      styles.priorityBtn,
                      {
                        backgroundColor: priority === p ? theme.colors.brand : theme.colors.surface0,
                        borderColor: priority === p ? theme.colors.brand : theme.colors.border,
                      },
                    ]}
                  >
                    <Text style={{
                      color: priority === p ? theme.colors.onBrand : theme.colors.text,
                      fontWeight: "700",
                      fontSize: theme.fontSize.sm,
                      textTransform: "capitalize",
                    }}>{p === "normal" ? "Normal" : p.charAt(0).toUpperCase() + p.slice(1)}</Text>
                    <Text style={{
                      color: priority === p ? "rgba(255,255,255,0.75)" : theme.colors.textMuted,
                      fontSize: 10,
                      textAlign: "center",
                      marginTop: 2,
                    }}>{sublabels[p]}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <Button label="Submit Ticket" onPress={handleSubmit} loading={submitting} />
          </View>
        )}

        {isLoggedIn && (
          loadingTickets ? (
            <ActivityIndicator color={theme.colors.brand} style={{ marginTop: theme.spacing.md }} />
          ) : tickets.length === 0 ? (
            <Text style={[s.textMuted, { textAlign: "center", marginTop: theme.spacing.sm }]}>
              No tickets yet. Create one above.
            </Text>
          ) : (
            <View style={{ gap: 10 }}>
              {tickets.map((ticket) => (
                <TicketRow
                  key={ticket.id}
                  ticket={ticket}
                  onPress={() => router.push({ pathname: "/ticket-detail", params: { id: String(ticket.id) } } as never)}
                />
              ))}
            </View>
          )
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
