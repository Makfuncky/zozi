/**
 * Admin Bank Account Verification — React Native
 * Mirrors web_app/src/app/admin/bank-accounts/page.tsx
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  TextInput,
  RefreshControl,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { useAuthStore } from "@/lib/authStore";

interface BankAccountRecord {
  id: number;
  supplier_id?: number | null;
  partner_id?: number | null;
  entity_name?: string | null;
  beneficiary_name?: string | null;
  bank_name?: string | null;
  branch_name?: string | null;
  account_number?: string | null;
  iban?: string | null;
  swift_code?: string | null;
  routing_number?: string | null;
  currency?: string;
  bank_country?: string | null;
  verification_status: "pending" | "verified" | "rejected";
  verification_note?: string | null;
  verified_at?: string | null;
  created_at?: string | null;
}

type Kind = "supplier" | "logistics_partner";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    tabRail: {
      flexDirection: "row",
      marginHorizontal: theme.spacing.md,
      marginBottom: theme.spacing.sm,
      borderRadius: 12,
      overflow: "hidden",
      borderWidth: 1,
    },
    tabBtn: {
      flex: 1,
      paddingVertical: 12,
      alignItems: "center",
    },
    card: {
      marginHorizontal: theme.spacing.md,
      marginBottom: theme.spacing.sm,
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      overflow: "hidden",
    },
    cardHeader: {
      flexDirection: "row",
      alignItems: "center",
      padding: theme.spacing.md,
      gap: 12,
    },
    cardBody: {
      paddingHorizontal: theme.spacing.md,
      paddingBottom: theme.spacing.md,
      gap: 10,
    },
    detailRow: {
      flexDirection: "row",
      gap: 8,
    },
    detailLabel: {
      fontSize: 12,
      fontWeight: "600",
      width: 110,
    },
    detailValue: {
      flex: 1,
      fontSize: 12,
    },
    noteInput: {
      borderWidth: 1,
      borderRadius: 10,
      padding: 10,
      minHeight: 72,
      textAlignVertical: "top",
      fontSize: 13,
    },
    actionRow: {
      flexDirection: "row",
      gap: 10,
    },
    actionBtn: {
      flex: 1,
      paddingVertical: 10,
      borderRadius: 10,
      alignItems: "center",
      borderWidth: 1,
    },
    statusPill: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 999,
    },
    emptyBox: {
      alignItems: "center",
      padding: 40,
      gap: 8,
    },
    msgBox: {
      marginHorizontal: theme.spacing.md,
      marginBottom: theme.spacing.sm,
      padding: 12,
      borderRadius: theme.radius.md,
      borderWidth: 1,
    },
  });

function statusPillColor(
  status: BankAccountRecord["verification_status"],
  theme: AppTheme
): string {
  if (status === "verified") return theme.colors.success;
  if (status === "rejected") return theme.colors.danger;
  return theme.colors.warning;
}

function DetailRow({
  label,
  value,
  theme,
}: {
  label: string;
  value?: string | null;
  theme: AppTheme;
}) {
  const styles = createStyles(theme);
  if (!value) return null;
  return (
    <View style={styles.detailRow}>
      <Text style={[styles.detailLabel, { color: theme.colors.textMuted }]}>
        {label}
      </Text>
      <Text style={[styles.detailValue, { color: theme.colors.text }]}>
        {value}
      </Text>
    </View>
  );
}

function BankCard({
  record,
  onAction,
}: {
  record: BankAccountRecord;
  onAction: () => void;
}) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const [expanded, setExpanded] = useState(false);
  const [note, setNote] = useState(record.verification_note ?? "");
  const [actioning, setActioning] = useState(false);
  const pillColor = statusPillColor(record.verification_status, theme);

  async function handleVerify(approve: boolean) {
    setActioning(true);
    try {
      await apiFetch(
        `/admin/bank-accounts/${record.id}/verify`,
        {
          method: "POST",
          body: JSON.stringify({ approved: approve, note: note.trim() || null }),
        } as never
      );
      onAction();
    } catch (e: any) {
      const detail: string = e?.body?.detail ?? e?.message ?? "Action failed";
      Alert.alert("Error", detail);
    } finally {
      setActioning(false);
    }
  }

  return (
    <View
      style={[
        styles.card,
        { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
      ]}
    >
      {/* Header */}
      <TouchableOpacity
        testID={`admin-bank-accounts-card-toggle-${record.id}`}
        style={styles.cardHeader}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.8}
      >
        <View style={{ flex: 1, gap: 4 }}>
          <Text style={[s.text, { fontWeight: "700" }]}>
            {record.entity_name ?? `Account #${record.id}`}
          </Text>
          <Text style={[s.textMuted, { fontSize: 12 }]}>
            {record.bank_name ?? "—"} · {record.currency ?? "N/A"}
          </Text>
        </View>
        <View
          style={[
            styles.statusPill,
            { backgroundColor: pillColor + "22", borderWidth: 1, borderColor: pillColor },
          ]}
        >
          <Text
            style={{
              color: pillColor,
              fontSize: 11,
              fontWeight: "700",
              textTransform: "capitalize",
            }}
          >
            {record.verification_status}
          </Text>
        </View>
        <Ionicons
          name={expanded ? "chevron-up" : "chevron-down"}
          size={16}
          color={theme.colors.textMuted}
        />
      </TouchableOpacity>

      {/* Expanded details */}
      {expanded && (
        <View style={styles.cardBody}>
          <DetailRow label="Beneficiary" value={record.beneficiary_name} theme={theme} />
          <DetailRow label="Bank" value={record.bank_name} theme={theme} />
          <DetailRow label="Branch" value={record.branch_name} theme={theme} />
          <DetailRow label="Account No." value={record.account_number} theme={theme} />
          <DetailRow label="IBAN" value={record.iban} theme={theme} />
          <DetailRow label="SWIFT" value={record.swift_code} theme={theme} />
          <DetailRow label="Routing No." value={record.routing_number} theme={theme} />
          <DetailRow label="Country" value={record.bank_country} theme={theme} />
          <DetailRow label="Currency" value={record.currency} theme={theme} />
          {record.created_at && (
            <DetailRow
              label="Submitted"
              value={new Date(record.created_at).toLocaleDateString()}
              theme={theme}
            />
          )}

          {record.verification_status === "pending" && (
            <>
              <TextInput
                testID={`admin-bank-accounts-note-${record.id}`}
                style={[
                  styles.noteInput,
                  {
                    color: theme.colors.text,
                    backgroundColor: theme.colors.surface0,
                    borderColor: theme.colors.border,
                  },
                ]}
                placeholder="Optional note (visible to supplier/partner)"
                placeholderTextColor={theme.colors.textMuted}
                value={note}
                onChangeText={setNote}
                multiline
              />

              {actioning ? (
                <ActivityIndicator color={theme.colors.brand} />
              ) : (
                <View style={styles.actionRow}>
                  <TouchableOpacity
                    testID={`admin-bank-accounts-approve-${record.id}`}
                    style={[
                      styles.actionBtn,
                      { backgroundColor: theme.colors.success, borderColor: theme.colors.success },
                    ]}
                    onPress={() => handleVerify(true)}
                    activeOpacity={0.8}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700" }}>Approve</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    testID={`admin-bank-accounts-reject-${record.id}`}
                    style={[
                      styles.actionBtn,
                      { backgroundColor: theme.colors.danger, borderColor: theme.colors.danger },
                    ]}
                    onPress={() => handleVerify(false)}
                    activeOpacity={0.8}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700" }}>Reject</Text>
                  </TouchableOpacity>
                </View>
              )}
            </>
          )}

          {record.verification_status !== "pending" && record.verification_note && (
            <View
              style={{
                padding: 10,
                borderRadius: 8,
                backgroundColor: theme.colors.surface2,
              }}
            >
              <Text style={[s.textMuted, { fontSize: 12 }]}>
                Note: {record.verification_note}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

export default function AdminBankAccountsScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const [kind, setKind] = useState<Kind>("supplier");
  const [records, setRecords] = useState<BankAccountRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const isAdmin =
    user?.role === "admin" || user?.role === "sub_admin";

  const load = useCallback(
    async (k: Kind, silent = false) => {
      if (!silent) setLoading(true);
      setMsg(null);
      try {
        const res = await apiFetch<BankAccountRecord[]>(
          `/admin/bank-accounts/pending?kind=${k}`
        );
        if (Array.isArray(res)) {
          setRecords(res);
        } else {
          setRecords([]);
        }
      } catch {
        setRecords([]);
      } finally {
        if (!silent) setLoading(false);
        setRefreshing(false);
      }
    },
    []
  );

  useEffect(() => {
    void load(kind);
  }, [kind, load]);

  if (!isAdmin) {
    return (
      <View testID="admin-bank-accounts-guard" style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: "Bank Account Verification" }} />
        <Ionicons name="lock-closed-outline" size={40} color={theme.colors.textMuted} />
        <Text style={[s.textMuted, { marginTop: 12, textAlign: "center" }]}>
          Admin access required
        </Text>
      </View>
    );
  }

  return (
    <View testID="admin-bank-accounts-screen" style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Bank Account Verification" }} />

      {/* Kind tabs */}
      <View
        style={[
          styles.tabRail,
          { borderColor: theme.colors.border, marginTop: theme.spacing.sm },
        ]}
      >
        {(["supplier", "logistics_partner"] as Kind[]).map((k) => (
          <TouchableOpacity
            testID={`admin-bank-accounts-tab-${k}`}
            key={k}
            style={[
              styles.tabBtn,
              {
                backgroundColor:
                  kind === k ? theme.colors.brand : theme.colors.surface1,
              },
            ]}
            onPress={() => setKind(k)}
            activeOpacity={0.85}
          >
            <Text
              style={{
                color: kind === k ? "#fff" : theme.colors.text,
                fontWeight: "700",
                fontSize: 13,
                textTransform: "capitalize",
              }}
            >
              {k === "supplier" ? "Suppliers" : "Logistics Partners"}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {msg && (
        <View
          style={[
            styles.msgBox,
            {
              backgroundColor:
                msg.type === "success"
                  ? theme.colors.success + "22"
                  : theme.colors.danger + "22",
              borderColor:
                msg.type === "success" ? theme.colors.success : theme.colors.danger,
            },
          ]}
        >
          <Text
            style={{
              color: msg.type === "success" ? theme.colors.success : theme.colors.danger,
              fontSize: 13,
            }}
          >
            {msg.text}
          </Text>
        </View>
      )}

      {loading ? (
        <ActivityIndicator
          color={theme.colors.brand}
          style={{ marginTop: 40 }}
          size="large"
        />
      ) : (
        <ScrollView
          contentContainerStyle={{ paddingTop: theme.spacing.sm, paddingBottom: 40 }}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                void load(kind, true);
              }}
              colors={[theme.colors.brand]}
            />
          }
        >
          {records.length === 0 ? (
            <View testID="admin-bank-accounts-empty" style={styles.emptyBox}>
              <Ionicons name="checkmark-circle-outline" size={40} color={theme.colors.success} />
              <Text style={[s.text, { fontWeight: "700" }]}>All clear!</Text>
              <Text style={[s.textMuted, { textAlign: "center" }]}>
                No pending bank accounts for{" "}
                {kind === "supplier" ? "suppliers" : "logistics partners"}.
              </Text>
            </View>
          ) : (
            records.map((record) => (
              <BankCard
                key={record.id}
                record={record}
                onAction={() => void load(kind, true)}
              />
            ))
          )}
        </ScrollView>
      )}
    </View>
  );
}
