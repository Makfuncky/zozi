import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, getStatusColor } from "@/theme";
import { getReturn, ReturnRequest } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Button } from "@/components/ui/Button";
import ScreenHeader from "@/components/ui/ScreenHeader";

export default function ReturnDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const formatPrice = useCurrencyStore((st) => st.format);

  const [returnData, setReturnData] = useState<ReturnRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = React.useCallback(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getReturn(Number(id))
      .then((data) => {
        setReturnData(data);
        setError(null);
      })
      .catch(() => {
        setError("We couldn't load this return. Please check your connection and try again.");
      })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <>
        <ScreenHeader title={`Return #${id ?? ""}`} />
        <LoadingSpinner fullscreen />
      </>
    );
  }

  if (error || !returnData) {
    return (
      <>
        <ScreenHeader title="Return" />
        <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center", padding: theme.spacing.xl }]}>
          <Ionicons name="cloud-offline-outline" size={48} color={theme.colors.textMuted} style={{ marginBottom: 12 }} />
          <Text style={[s.title, { color: theme.colors.text, textAlign: "center", marginBottom: 6 }]}>
            {error ?? "Return not found."}
          </Text>
          <Button label="Retry" onPress={load} style={{ marginTop: theme.spacing.md }} />
          <Button
            label="Go Back"
            variant="ghost"
            onPress={() => router.back()}
            style={{ marginTop: theme.spacing.sm }}
          />
        </View>
      </>
    );
  }

  const status = getStatusColor(returnData.status, theme);

  return (
    <>
      <ScreenHeader title={`Return #${returnData.id}`} />
      <ScrollView
        style={s.container}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
      >
        {/* Status header */}
        <View style={[styles.statusCard, { backgroundColor: status.bg, borderColor: status.border }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <View style={[styles.statusDot, { backgroundColor: status.color }]} />
            <Text style={{ color: status.color, fontWeight: "700", fontSize: 13, letterSpacing: 0.5 }}>
              {returnData.status.toUpperCase()}
            </Text>
            <StatusBadge status={returnData.status} />
          </View>
          {returnData.refund_amount != null && (
            <Text style={{ color: theme.colors.success, fontWeight: "600", fontSize: 15, marginTop: 8 }}>
              Refund: {formatPrice(Number(returnData.refund_amount))}
            </Text>
          )}
        </View>

        {/* Details */}
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Row label="Return ID" value={`#${returnData.id}`} theme={theme} />
          <Row label="Order ID" value={`#${returnData.order_id}`} theme={theme} />
          <Row label="Submitted" value={new Date(returnData.created_at).toLocaleDateString()} theme={theme} />
          {returnData.updated_at && (
            <Row label="Updated" value={new Date(returnData.updated_at).toLocaleDateString()} theme={theme} />
          )}
        </View>

        {/* Reason */}
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginTop: 12 }]}>
          <Text style={{ color: theme.colors.textMuted, fontSize: 12, fontWeight: "600", marginBottom: 6 }}>REASON</Text>
          <Text style={{ color: theme.colors.text, fontSize: 14, lineHeight: 20 }}>{returnData.reason}</Text>
        </View>

        {/* Notes */}
        {returnData.notes && (
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginTop: 12 }]}>
            <Text style={{ color: theme.colors.textMuted, fontSize: 12, fontWeight: "600", marginBottom: 6 }}>NOTES FROM ADMIN</Text>
            <Text style={{ color: theme.colors.text, fontSize: 14, lineHeight: 20 }}>{returnData.notes}</Text>
          </View>
        )}

        {/* Items */}
        {returnData.items && returnData.items.length > 0 && (
          <View style={{ marginTop: 12 }}>
            <Text style={{ color: theme.colors.textMuted, fontSize: 12, fontWeight: "600", marginBottom: 8 }}>ITEMS</Text>
            {returnData.items.map((item, i) => (
              <View
                key={i}
                style={[styles.itemRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
              >
                <Text style={{ color: theme.colors.text, fontSize: 14, flex: 1 }}>
                  {item.product_name ?? `Product #${item.product_id}`}
                </Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>×{item.quantity}</Text>
                {item.price != null && (
                  <Text style={{ color: theme.colors.textMuted, fontSize: 13, marginLeft: 10 }}>
                    {formatPrice(Number(item.price))}
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </>
  );
}

function Row({ label, value, theme }: { label: string; value: string; theme: any }) {
  return (
    <View style={styles.row}>
      <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>{label}</Text>
      <Text style={{ color: theme.colors.text, fontSize: 13, fontWeight: "600" }}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  centerCol: { flex: 1, alignItems: "center", justifyContent: "center" },
  statusCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginBottom: 12,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    gap: 8,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  itemRow: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 10,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
});
