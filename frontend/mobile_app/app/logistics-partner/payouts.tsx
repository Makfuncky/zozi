import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Stack } from "expo-router";
import {
  getLogisticsFinanceSettlements,
  getLogisticsFinanceSummary,
  getLogisticsPartnerDashboard,
  getLogisticsPartnerPayouts,
  requestLogisticsPartnerPayout,
  getPartnerBankAccount,
  upsertPartnerBankAccount,
  type LogisticsFinanceSettlement,
  type LogisticsFinanceSummary,
  type LogisticsPartnerDashboardData,
  type LogisticsPartnerPayout,
  type RecipientBankAccount,
} from "@/lib/api";
import { getLogisticsPayoutReadiness } from "@/lib/logisticsPayoutInsights";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme, makeStyles } from "@/theme";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: { padding: theme.spacing.md, gap: 14 },
  card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 12 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  metric: { borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, minWidth: "46%", flex: 1, gap: 4 },
  input: { borderWidth: 1, borderRadius: theme.radius.lg, paddingHorizontal: 12, paddingVertical: 10, color: theme.colors.text },
  button: { borderRadius: theme.radius.lg, paddingVertical: 12, alignItems: "center", borderWidth: 1.5 },
  payoutRow: { borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 14 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
});

const STATUS_COLORS = (theme: AppTheme): Record<string, string> => ({
  pending: theme.colors.warning,
  processing: theme.colors.statusProcessing,
  completed: theme.colors.success,
  settled: theme.colors.success,
  eligible: theme.colors.statusProcessing,
  partial: theme.colors.warning,
  rejected: theme.colors.danger,
  reversed: theme.colors.danger,
});

function formatCurrency(amount: number): string {
  return `AED ${amount.toFixed(2)}`;
}

function paymentMethodLabel(value?: string | null): string {
  if (value === "cod") return "Cash on Delivery";
  if (value === "tap") return "Tap";
  if (value === "card") return "Card";
  return "Unspecified";
}

function routeLabel(item: LogisticsFinanceSettlement): string {
  const route = [item.partner_name, item.service_area_label].filter(Boolean).join(" • ");
  const destination = [item.destination_city, item.destination_country].filter(Boolean).join(", ");
  return route || destination || "Allocation snapshot pending";
}

export default function LogisticsPartnerPayoutsScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const statusColors = STATUS_COLORS(theme);

  const [dashboard, setDashboard] = useState<LogisticsPartnerDashboardData | null>(null);
  const [financeSummary, setFinanceSummary] = useState<LogisticsFinanceSummary | null>(null);
  const [financeSettlements, setFinanceSettlements] = useState<LogisticsFinanceSettlement[]>([]);
  const [payouts, setPayouts] = useState<LogisticsPartnerPayout[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("bank");
  const [notes, setNotes] = useState("");

  // Bank account state
  const [bankAccount, setBankAccount] = useState<RecipientBankAccount | null>(null);
  const [bankExpanded, setBankExpanded] = useState(false);
  const [bankForm, setBankForm] = useState({
    beneficiary_name: "", bank_name: "", branch_name: "", account_number: "",
    iban: "", swift_code: "", routing_number: "", currency: "AED", bank_country: "",
  });
  const [bankSaving, setBankSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [dashboardData, payoutData, summaryData, settlementData, bankData] = await Promise.all([
        getLogisticsPartnerDashboard(),
        getLogisticsPartnerPayouts(),
        getLogisticsFinanceSummary(),
        getLogisticsFinanceSettlements(),
        getPartnerBankAccount().catch(() => null),
      ]);
      setDashboard(dashboardData);
      setPayouts(payoutData);
      setFinanceSummary(summaryData);
      setFinanceSettlements(settlementData);
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
          currency: bankData.currency || "AED",
          bank_country: bankData.bank_country || "",
        });
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const canSubmit = useMemo(() => {
    const parsed = Number(amount);
    return parsed > 0 && parsed <= Number(dashboard?.payout_summary?.available_balance || 0);
  }, [amount, dashboard]);

  const payoutReadiness = useMemo(
    () => getLogisticsPayoutReadiness({
      availableBalance: Number(dashboard?.payout_summary?.available_balance || 0),
      pendingCodRemittance: Number(financeSummary?.pending_cod_remittance || 0),
      hasBankAccount: Boolean(bankAccount?.id),
      bankVerificationStatus: bankAccount?.verification_status,
    }),
    [bankAccount?.id, bankAccount?.verification_status, dashboard?.payout_summary?.available_balance, financeSummary?.pending_cod_remittance],
  );

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      await requestLogisticsPartnerPayout({ amount: Number(amount), method, notes });
      setAmount("");
      setNotes("");
      Alert.alert("Submitted", "Your payout request has been sent.");
      await load();
    } catch (error: unknown) {
      Alert.alert("Request failed", error instanceof Error ? error.message : "Unable to submit payout request.");
    } finally {
      setSubmitting(false);
    }
  }, [amount, canSubmit, load, method, notes]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Payouts" }} />
      {loading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator size="large" color={theme.colors.brand} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
          showsVerticalScrollIndicator={false}
        >
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={styles.row}>
              <View style={{ flex: 1, gap: 4 }}>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", letterSpacing: 1 }]}>Payout Readiness</Text>
                <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{payoutReadiness.title}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{payoutReadiness.detail}</Text>
              </View>
              <View style={[styles.badge, {
                backgroundColor: payoutReadiness.tone === "good" ? theme.colors.successBg : payoutReadiness.tone === "critical" ? theme.colors.dangerBg : theme.colors.warningBg,
              }]}>
                <Text style={{ color: payoutReadiness.tone === "good" ? theme.colors.success : payoutReadiness.tone === "critical" ? theme.colors.danger : theme.colors.warning, fontWeight: "700", fontSize: theme.fontSize.xs }}>
                  {payoutReadiness.tone.toUpperCase()}
                </Text>
              </View>
            </View>
            <View style={styles.grid}>
              {[
                { label: "Bank", value: bankAccount?.verification_status || "not configured" },
                { label: "Available", value: formatCurrency(Number(dashboard?.payout_summary?.available_balance || 0)) },
                { label: "Pending COD", value: formatCurrency(Number(financeSummary?.pending_cod_remittance || 0)) },
                { label: "Recent Requests", value: String(payouts.length) },
              ].map((item) => (
                <View key={item.label} style={[styles.metric, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                  <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.md, fontWeight: "800" }}>{item.value}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{item.label}</Text>
                </View>
              ))}
            </View>
          </View>

          {financeSummary && (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Delivery Finance</Text>
              <View style={styles.grid}>
                {[
                  { label: "Delivery Fees", value: formatCurrency(financeSummary.total_delivery_fees), tone: theme.colors.brand },
                  { label: "Pickup Fees", value: formatCurrency(financeSummary.total_pickup_fees || 0), tone: theme.colors.statusProcessing },
                  { label: "Dropoff Fees", value: formatCurrency(financeSummary.total_dropoff_fees || 0), tone: theme.colors.text },
                  { label: "COD Collected", value: formatCurrency(financeSummary.total_cod_collected), tone: theme.colors.success },
                  { label: "Pending COD", value: formatCurrency(financeSummary.pending_cod_remittance), tone: theme.colors.warning },
                  { label: "Refund Reversals", value: formatCurrency(financeSummary.total_refund_reversals || 0), tone: theme.colors.danger },
                ].map(({ label, value, tone }) => (
                  <View key={label} style={[styles.metric, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                    <Text style={{ color: tone, fontSize: theme.fontSize.lg, fontWeight: "800" }}>{value}</Text>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                  </View>
                ))}
              </View>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Delivered settlement rows: {financeSummary.total_deliveries}</Text>
            </View>
          )}

          {financeSummary?.bank_instruction || (financeSummary?.pending_cod_remittance || 0) > 0 ? (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{financeSummary?.bank_instruction?.title || "COD Remittance Instructions"}</Text>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Outstanding COD due {formatCurrency(financeSummary?.pending_cod_remittance || 0)}</Text>
              <Text style={[s.text, { fontWeight: "800", color: theme.colors.brand }]}>Reference {financeSummary?.bank_instruction?.reference_value || "Pending"}</Text>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Bank {financeSummary?.bank_instruction?.bank_name || "Not configured"}</Text>
              {financeSummary?.bank_instruction?.beneficiary_name ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{financeSummary.bank_instruction.beneficiary_name}</Text>
              ) : null}
              {financeSummary?.bank_instruction?.account_number || financeSummary?.bank_instruction?.iban ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Account {financeSummary.bank_instruction?.account_number || financeSummary.bank_instruction?.iban}</Text>
              ) : null}
              {financeSummary?.bank_instruction?.swift_code ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>SWIFT {financeSummary.bank_instruction.swift_code}</Text>
              ) : null}
              {(financeSummary?.bank_instruction?.support_email || financeSummary?.bank_instruction?.support_phone) && (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Support {[financeSummary.bank_instruction?.support_email, financeSummary.bank_instruction?.support_phone].filter(Boolean).join(" • ")}</Text>
              )}
              {financeSummary?.bank_instruction?.instructions ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{financeSummary.bank_instruction.instructions}</Text>
              ) : null}
            </View>
          ) : null}

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Revenue Summary</Text>
            <View style={styles.grid}>
              {[
                { label: "Total Earned", value: formatCurrency(dashboard?.payout_summary.total_earned ?? 0), tone: theme.colors.brand },
                { label: "Available", value: formatCurrency(dashboard?.payout_summary.available_balance ?? 0), tone: theme.colors.success },
                { label: "Pending", value: formatCurrency(dashboard?.payout_summary.pending_amount ?? 0), tone: theme.colors.warning },
                { label: "Completed", value: formatCurrency(dashboard?.payout_summary.completed_amount ?? 0), tone: theme.colors.statusProcessing },
              ].map(({ label, value, tone }) => (
                <View key={label} style={[styles.metric, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                  <Text style={{ color: tone, fontSize: theme.fontSize.lg, fontWeight: "800" }}>{value}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* ─── Payout Bank Account ──────────────────────────── */}
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <TouchableOpacity onPress={() => setBankExpanded((p) => !p)} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Payout Bank Account</Text>
              <View style={[styles.badge, {
                backgroundColor: bankAccount?.verification_status === "verified" ? theme.colors.successBg : bankAccount?.verification_status === "rejected" ? theme.colors.dangerBg : theme.colors.warningBg,
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
                      placeholder={key === "currency" ? "AED" : ""}
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
                      const result = await upsertPartnerBankAccount(bankForm);
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
                  <Text style={{ color: theme.colors.onBrand, fontWeight: "700", fontSize: theme.fontSize.sm }}>{bankSaving ? "Saving…" : "Save Bank Account"}</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Settlement Breakdown</Text>
            {financeSettlements.length === 0 ? (
              <Text style={s.textMuted}>No settlement rows yet.</Text>
            ) : financeSettlements.slice(0, 8).map((settlement) => {
              const statusColor = statusColors[settlement.status] ?? theme.colors.textMuted;
              const codColor = statusColors[settlement.cod_remittance_status || ""] ?? theme.colors.textMuted;
              const refundColor = statusColors[settlement.refund_status || ""] ?? theme.colors.textMuted;

              return (
                <View key={settlement.id} style={[styles.payoutRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                  <View style={styles.row}>
                    <View style={{ gap: 2, flex: 1 }}>
                      <Text style={[s.text, { fontWeight: "700", color: theme.colors.text }]}>Order #{settlement.order_id}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{routeLabel(settlement)}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{paymentMethodLabel(settlement.payment_method)}</Text>
                    </View>
                    <View style={[styles.badge, { backgroundColor: `${statusColor}22` }]}>
                      <Text style={{ color: statusColor, fontWeight: "700", textTransform: "capitalize", fontSize: theme.fontSize.xs }}>{settlement.status}</Text>
                    </View>
                  </View>
                  <Text style={[s.text, { fontWeight: "700", color: theme.colors.brand }]}>Total {formatCurrency(settlement.total_delivery_fee)}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Pickup {formatCurrency(settlement.pickup_charge)} · Dropoff {formatCurrency(settlement.dropoff_charge)}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>COD {formatCurrency(settlement.cod_collected || 0)} collected · {formatCurrency(settlement.cod_remitted || 0)} remitted · {formatCurrency(settlement.cod_retained || 0)} retained</Text>
                  {settlement.cod_collected ? (
                    <View style={[styles.badge, { alignSelf: "flex-start", backgroundColor: `${codColor}22` }]}>
                      <Text style={{ color: codColor, fontWeight: "700", fontSize: theme.fontSize.xs }}>
                        COD {settlement.cod_remittance_status || "pending"}
                      </Text>
                    </View>
                  ) : null}
                  {settlement.refund_status ? (
                    <View style={[styles.badge, { alignSelf: "flex-start", backgroundColor: `${refundColor}22` }]}>
                      <Text style={{ color: refundColor, fontWeight: "700", fontSize: theme.fontSize.xs }}>
                        Refund {settlement.refund_status} · {formatCurrency(settlement.logistics_reversal_amount || 0)}
                      </Text>
                    </View>
                  ) : null}
                  {!!settlement.allocations?.length && (
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                      Supplier split: {settlement.allocations.map((row) => `${row.supplier_name || `#${row.supplier_id}`} ${formatCurrency(row.shipping_amount)}`).join(" · ")}
                    </Text>
                  )}
                </View>
              );
            })}
          </View>

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Request Payout</Text>
            <View style={{ gap: 10 }}>
              <View>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginBottom: 6 }]}>Amount (AED)</Text>
                <TextInput
                  value={amount}
                  onChangeText={setAmount}
                  keyboardType="decimal-pad"
                  placeholder="150.00"
                  placeholderTextColor={theme.colors.textMuted}
                  style={[styles.input, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}
                />
              </View>
              <View>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginBottom: 6 }]}>Method</Text>
                <TextInput
                  value={method}
                  onChangeText={setMethod}
                  placeholder="bank"
                  placeholderTextColor={theme.colors.textMuted}
                  style={[styles.input, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}
                />
              </View>
              <View>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginBottom: 6 }]}>Notes</Text>
                <TextInput
                  value={notes}
                  onChangeText={setNotes}
                  placeholder="Settlement instructions"
                  placeholderTextColor={theme.colors.textMuted}
                  multiline
                  numberOfLines={3}
                  style={[styles.input, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border, minHeight: 90, textAlignVertical: "top" }]}
                />
              </View>
              <TouchableOpacity
                style={[styles.button, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand }]}
                disabled={!canSubmit || submitting}
                onPress={handleSubmit}
              >
                <Text style={{ color: theme.colors.onBrand, fontWeight: "700", fontSize: theme.fontSize.md }}>
                  {submitting ? "Submitting..." : "Submit Request"}
                </Text>
              </TouchableOpacity>
              {!canSubmit ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Request amount must be positive and within your available balance.</Text> : null}
            </View>
          </View>

          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Payout History</Text>
            {payouts.length === 0 ? (
              <Text style={s.textMuted}>No payout requests yet.</Text>
            ) : payouts.map((payout) => {
              const statusColor = statusColors[payout.status] ?? theme.colors.textMuted;
              return (
                <View key={payout.id} style={[styles.payoutRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                  <View style={styles.row}>
                    <View style={{ gap: 2, flex: 1 }}>
                      <Text style={[s.text, { fontWeight: "700", color: theme.colors.brand }]}>{formatCurrency(payout.amount)}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Requested {payout.created_at ? new Date(payout.created_at).toLocaleString() : "recently"}</Text>
                    </View>
                    <View style={[styles.badge, { backgroundColor: statusColor + "22" }]}>
                      <Text style={{ color: statusColor, fontWeight: "700", textTransform: "capitalize", fontSize: theme.fontSize.xs }}>{payout.status}</Text>
                    </View>
                  </View>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Method: {payout.method || "bank"}</Text>
                  {payout.reference ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Reference: {payout.reference}</Text> : null}
                  {payout.notes ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{payout.notes}</Text> : null}
                </View>
              );
            })}
          </View>
        </ScrollView>
      )}
    </View>
  );
}