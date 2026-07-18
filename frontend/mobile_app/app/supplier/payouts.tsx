import React, { useCallback, useEffect, useState } from "react";
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TextInput, TouchableOpacity, Alert } from "react-native";

import { Stack } from "expo-router";
import {
  getSupplierFinanceSettlements,
  getSupplierFinanceSummary,
  getSupplierPayouts,
  getSupplierBankAccount,
  upsertSupplierBankAccount,
  type SupplierFinanceSettlement,
  type SupplierFinanceSummary,
  type SupplierPayout,
  type RecipientBankAccount,
} from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles, AppTheme, getStatusColor } from "@/theme";
import { EmptyState } from "@/components/ui/EmptyState";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    padding: theme.spacing.md,
    gap: 14,
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: 12,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  metric: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: 12,
    minWidth: "46%",
    flex: 1,
    gap: 4,
  },
  row: {
    borderRadius: 14,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: 10,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: theme.spacing.xs,
    borderRadius: 20,
    borderWidth: 1,
  },
});

const STATUS_TONE: Record<string, string> = {
  pending: "warning",
  paid: "success",
  completed: "success",
  cancelled: "danger",
  eligible: "processing",
  processing: "processing",
  settled: "success",
  reversed: "danger",
};

function statusColorFor(status: string | null | undefined, theme: AppTheme): string {
  const tone = STATUS_TONE[status ?? ""];
  switch (tone) {
    case "warning": return theme.colors.warning;
    case "success": return theme.colors.success;
    case "danger": return theme.colors.danger;
    case "processing": return theme.colors.statusProcessing;
    default: return theme.colors.textMuted;
  }
}

function paymentMethodLabel(value?: string | null): string {
  if (value === "cod") return "Cash on Delivery";
  if (value === "tap") return "Tap";
  if (value === "card") return "Card";
  return "Unspecified";
}

function routeLabel(item: SupplierFinanceSettlement): string {
  const route = [item.partner_name, item.service_area_label].filter(Boolean).join(" • ");
  const destination = [item.destination_city, item.destination_country].filter(Boolean).join(", ");
  return route || destination || "Allocation snapshot pending";
}

function destinationLabel(item: SupplierFinanceSettlement): string | null {
  const destination = [item.destination_city, item.destination_country].filter(Boolean).join(", ");
  return destination || null;
}

function allocationSourceLabel(value?: string | null): string | null {
  if (!value) return null;
  return value.replace(/_/g, " ");
}

function formatPercent(value?: number | null): string | null {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  return `${value.toFixed(1)}%`;
}

function PayoutRow({ item }: { item: SupplierPayout }) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const formatMoney = useCurrencyStore((state) => state.format);
  const statusColor = statusColorFor(item.status, theme);
  const completedAt = item.paid_at || item.processed_at;

  return (
    <View style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
      <View style={{ flex: 1, gap: theme.spacing.xs }}>
        <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md, color: theme.colors.brand }]}>
          {formatMoney(item.amount)}
        </Text>
        <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>
          Requested {new Date(item.created_at).toLocaleDateString()}
        </Text>
        {completedAt && (
          <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, color: theme.colors.success }]}>
            Paid {new Date(completedAt).toLocaleDateString()}
          </Text>
        )}
        {item.reference ? (
          <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>Reference {item.reference}</Text>
        ) : null}
        {item.notes ? (
          <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>{item.notes}</Text>
        ) : null}
      </View>
      <View style={[styles.badge, { backgroundColor: statusColor + "22", borderColor: statusColor }]}>
        <Text style={{ color: statusColor, fontSize: theme.fontSize.sm, fontWeight: "600", textTransform: "capitalize" }}>
          {item.status}
        </Text>
      </View>
    </View>
  );
}

function SettlementRow({ item }: { item: SupplierFinanceSettlement }) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const formatMoney = useCurrencyStore((state) => state.format);
  const statusColor = statusColorFor(item.status, theme);
  const refundColor = statusColorFor(item.refund_status || "", theme);
  const destination = destinationLabel(item);
  const allocationSource = allocationSourceLabel(item.allocation_source);
  const commissionRate = formatPercent(item.commission_rate);

  return (
    <View style={[styles.row, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
      <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 10 }}>
        <View style={{ flex: 1, gap: 4 }}>
          <Text style={[s.text, { fontWeight: "800", color: theme.colors.text }]}>Order #{item.order_id}</Text>
          <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{routeLabel(item)}</Text>
          <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{paymentMethodLabel(item.payment_method)}</Text>
          {destination ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Destination {destination}</Text> : null}
          {allocationSource ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Allocation {allocationSource}</Text> : null}
        </View>
        <View style={[styles.badge, { backgroundColor: `${statusColor}22`, borderColor: statusColor }]}>
          <Text style={{ color: statusColor, fontSize: theme.fontSize.xs, fontWeight: "700", textTransform: "capitalize" }}>
            {item.status}
          </Text>
        </View>
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 12 }}>
        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Gross {formatMoney(item.gross_amount)}</Text>
        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Commission {formatMoney(item.commission_deducted)}</Text>
        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>VAT {formatMoney(item.vat_amount || 0)}</Text>
        {commissionRate ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Commission Rate {commissionRate}</Text> : null}
        {item.delivery_total != null ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Delivery Total {formatMoney(item.delivery_total)}</Text> : null}
      </View>
      <Text style={[s.text, { fontWeight: "700", color: theme.colors.brand }]}>
        Net {formatMoney(item.net_amount)}
      </Text>
      {item.refund_status ? (
        <View style={{ gap: 6 }}>
          <View style={[styles.badge, { alignSelf: "flex-start", backgroundColor: `${refundColor}22`, borderColor: refundColor }]}>
            <Text style={{ color: refundColor, fontSize: theme.fontSize.xs, fontWeight: "700" }}>
              Refund {item.refund_status} · {formatMoney(item.supplier_reversal_amount || 0)}
            </Text>
          </View>
          {item.customer_refund_amount != null ? (
            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Customer refund {formatMoney(item.customer_refund_amount)}</Text>
          ) : null}
        </View>
      ) : null}
      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Created {new Date(item.created_at).toLocaleDateString()}</Text>
    </View>
  );
}

export default function SupplierPayoutsScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const formatMoney = useCurrencyStore((state) => state.format);

  const [summary, setSummary] = useState<SupplierFinanceSummary | null>(null);
  const [settlements, setSettlements] = useState<SupplierFinanceSettlement[]>([]);
  const [payouts, setPayouts] = useState<SupplierPayout[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bank account state
  const [bankAccount, setBankAccount] = useState<RecipientBankAccount | null>(null);
  const [bankExpanded, setBankExpanded] = useState(false);
  const [bankForm, setBankForm] = useState({
    beneficiary_name: "", bank_name: "", branch_name: "", account_number: "",
    iban: "", swift_code: "", routing_number: "", currency: "OMR", bank_country: "",
  });
  const [bankSaving, setBankSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [summaryData, settlementData, payoutData, bankData] = await Promise.all([
        getSupplierFinanceSummary(),
        getSupplierFinanceSettlements(),
        getSupplierPayouts(),
        getSupplierBankAccount().catch(() => null),
      ]);
      setSummary(summaryData);
      setSettlements(settlementData);
      setPayouts(payoutData);
      if (bankData && bankData.id) {
        setBankAccount(bankData);
        setBankForm({
          beneficiary_name: bankData.beneficiary_name || "",
          bank_name: bankData.bank_name || "",
          branch_name: bankData.branch_name || "",
          account_number: bankData.account_number || "",
          iban: bankData.iban || "",
          swift_code: bankData.swift_code || "",
          routing_number: bankData.routing_number || "",
          currency: bankData.currency || "OMR",
          bank_country: bankData.bank_country || "",
        });
      }
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load payouts");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const totalPaid = payouts
    .filter((p) => ["paid", "completed"].includes(p.status))
    .reduce((acc, p) => acc + p.amount, 0);

  const totalPending = payouts
    .filter((p) => ["pending", "processing"].includes(p.status))
    .reduce((acc, p) => acc + p.amount, 0);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Finance & Payouts" }} />

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.colors.brand} />
        </View>
      ) : error ? (
        <EmptyState
          title="Error"
          subtitle={error}
          action={{ label: "Retry", onPress: load }}
        />
      ) : !summary && payouts.length === 0 && settlements.length === 0 ? (
        <EmptyState
          title="No finance data yet"
          subtitle="Your settlements and payout requests will appear here after orders are delivered."
          icon={<Ionicons name="logo-usd" size={30} color={theme.colors.textMuted} />}
        />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefreshing(true); load(); }}
              colors={[theme.colors.brand]}
            />
          }
        >
          {summary && (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Supplier Finance Summary</Text>
              <View style={styles.grid}>
                {[
                  { label: "Gross Revenue", value: formatMoney(summary.total_gross_revenue), tone: theme.colors.text },
                  { label: "Net Earnings", value: formatMoney(summary.total_net_earnings), tone: theme.colors.brand },
                  { label: "Pending Settlement", value: formatMoney(summary.pending_settlement), tone: theme.colors.warning },
                  { label: "Settled", value: formatMoney(summary.total_settled), tone: theme.colors.success },
                  { label: "VAT On Orders", value: formatMoney(summary.total_vat_on_orders || 0), tone: theme.colors.statusProcessing },
                  { label: "Refund Reversals", value: formatMoney(summary.total_refund_reversals || 0), tone: theme.colors.danger },
                ].map(({ label, value, tone }) => (
                  <View key={label} style={[styles.metric, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                    <Text style={{ color: tone, fontSize: theme.fontSize.lg, fontWeight: "800" }}>{value}</Text>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                  </View>
                ))}
              </View>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Orders contributing to summary: {summary.total_orders}</Text>
            </View>
          )}

          {summary?.bank_instruction ? (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{summary.bank_instruction.title || "Payout Reference Guide"}</Text>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                {summary.bank_instruction.reference_help || "Use this reference when asking Zozi finance to trace a payout."}
              </Text>
              <Text style={[s.text, { fontWeight: "800", color: theme.colors.brand }]}>Reference {summary.bank_instruction.reference_value || "Pending"}</Text>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Bank {summary.bank_instruction.bank_name || summary.bank_instruction.account_label || "Zozi treasury"}</Text>
              {summary.bank_instruction.account_number || summary.bank_instruction.iban ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                  Account {summary.bank_instruction.account_number || summary.bank_instruction.iban}
                </Text>
              ) : null}
              {(summary.bank_instruction.support_email || summary.bank_instruction.support_phone) && (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                  Support {[summary.bank_instruction.support_email, summary.bank_instruction.support_phone].filter(Boolean).join(" • ")}
                </Text>
              )}
              {summary.bank_instruction.instructions ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{summary.bank_instruction.instructions}</Text>
              ) : null}
            </View>
          ) : null}

          {/* ─── Payout Bank Account ────────────────────────────── */}
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <TouchableOpacity onPress={() => setBankExpanded((p) => !p)} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Payout Bank Account</Text>
              <View style={[styles.badge, {
                backgroundColor: bankAccount?.verification_status === "verified" ? theme.colors.success + "22" : bankAccount?.verification_status === "rejected" ? theme.colors.danger + "22" : theme.colors.warning + "22",
                borderColor: bankAccount?.verification_status === "verified" ? theme.colors.success : bankAccount?.verification_status === "rejected" ? theme.colors.danger : theme.colors.warning,
              }]}>
                <Text style={{ fontSize: theme.fontSize.xs, fontWeight: "700", color: bankAccount?.verification_status === "verified" ? theme.colors.success : bankAccount?.verification_status === "rejected" ? theme.colors.danger : theme.colors.warning }}>
                  {bankAccount?.id ? bankAccount.verification_status : "not configured"}
                </Text>
              </View>
            </TouchableOpacity>

            {bankExpanded && (
              <View style={{ gap: 10 }}>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                  Submit your bank account details for payout transfers. Reviewed by the Zozi finance team.
                </Text>
                {bankAccount?.verification_status === "rejected" && bankAccount.verification_note ? (
                  <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.xs, fontWeight: "600" }}>Rejection reason: {bankAccount.verification_note}</Text>
                ) : null}
                {(["beneficiary_name", "bank_name", "branch_name", "account_number", "iban", "swift_code", "routing_number", "currency", "bank_country"] as const).map((key) => (
                  <View key={key} style={{ gap: 4 }}>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", letterSpacing: 1 }]}>
                      {key.replace(/_/g, " ")}
                    </Text>
                    <TextInput
                      style={[s.text, { borderWidth: 1, borderColor: theme.colors.border, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: theme.colors.surface0, color: theme.colors.text, fontSize: theme.fontSize.sm }]}
                      value={bankForm[key]}
                      placeholder={key === "currency" ? "OMR" : ""}
                      placeholderTextColor={theme.colors.textFaint}
                      onChangeText={(v) => setBankForm((f) => ({ ...f, [key]: v }))}
                      autoCapitalize="none"
                    />
                  </View>
                ))}
                <TouchableOpacity
                  disabled={bankSaving}
                  onPress={async () => {
                    setBankSaving(true);
                    try {
                      const result = await upsertSupplierBankAccount(bankForm);
                      setBankAccount((prev) => ({ ...prev, ...bankForm, configured: true, id: result.id, verification_status: result.verification_status as "pending" | "verified" | "rejected" }));
                      Alert.alert("Saved", "Bank account saved. Pending admin verification.");
                    } catch {
                      Alert.alert("Error", "Failed to save bank account. Please try again.");
                    } finally {
                      setBankSaving(false);
                    }
                  }}
                  style={{ backgroundColor: theme.colors.brand, borderRadius: 12, paddingVertical: 12, alignItems: "center", opacity: bankSaving ? 0.6 : 1 }}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>{bankSaving ? "Saving…" : "Save Bank Account"}</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Settlement Breakdown</Text>
            {settlements.length === 0 ? (
              <Text style={s.textMuted}>No settlement rows yet.</Text>
            ) : settlements.slice(0, 8).map((item) => <SettlementRow key={item.id} item={item} />)}
          </View>

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Payout Request History</Text>
            <View style={styles.grid}>
              <View style={[styles.metric, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.lg, fontWeight: "800" }}>{formatMoney(totalPaid)}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Completed Requests</Text>
              </View>
              <View style={[styles.metric, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                <Text style={{ color: theme.colors.warning, fontSize: theme.fontSize.lg, fontWeight: "800" }}>{formatMoney(totalPending)}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Pending Requests</Text>
              </View>
            </View>
            {payouts.length === 0 ? (
              <Text style={s.textMuted}>No payout requests yet.</Text>
            ) : payouts.map((item) => <PayoutRow key={item.id} item={item} />)}
          </View>
        </ScrollView>
      )}
    </View>
  );
}
