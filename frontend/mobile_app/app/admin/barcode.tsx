/**
 * Admin Barcode Scanner — shipment barcode lookup & status update.
 * Uses expo-camera for native scanning with manual entry fallback.
 */
import React, { useCallback, useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { Ionicons, Feather } from "@expo/vector-icons";
import { Stack, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useAuthStore } from "@/lib/authStore";
import { makeStyles, AppTheme } from "@/theme";
import { toast } from "@/lib/toastStore";

let CameraView: any = null;
let useCameraPermissions: () => [any, () => void] = () => [null, () => {}];
try {
  const cam = require("expo-camera");
  CameraView = cam.CameraView;
  if (typeof cam.useCameraPermissions === "function") {
    useCameraPermissions = cam.useCameraPermissions;
  }
} catch {
  CameraView = null;
}

interface ShipmentInfo {
  id: number;
  order_id: number;
  status: string;
  carrier_name?: string | null;
  tracking_number?: string | null;
  distribution_channel?: string | null;
  current_hub?: string | null;
  shipping_address?: string | null;
  created_at?: string;
  updated_at?: string;
}

const STATUS_OPTIONS = [
  { value: "picked", label: "Picked Up", icon: "cube-outline" as const },
  { value: "in_transit", label: "In Transit", icon: "car-outline" as const },
  { value: "delivered", label: "Delivered", icon: "checkmark-circle-outline" as const },
  { value: "returned", label: "Returned", icon: "return-down-back-outline" as const },
  { value: "failed", label: "Failed", icon: "close-circle-outline" as const },
];

const STATUS_COLORS: Record<string, string> = {
  pending: "#F59E0B",
  picked: "#3B82F6",
  in_transit: "#8B5CF6",
  delivered: "#10B981",
  returned: "#EF4444",
  failed: "#EF4444",
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    container: {
      flex: 1,
    },
    scroll: {
      padding: theme.spacing.md,
      gap: theme.spacing.md,
      paddingBottom: 60,
    },
    modeToggle: {
      flexDirection: "row",
      borderRadius: theme.radius.lg,
      overflow: "hidden",
      borderWidth: 1,
    },
    modeBtn: {
      flex: 1,
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 6,
      paddingVertical: 12,
    },
    cameraBox: {
      height: 260,
      borderRadius: theme.radius.lg,
      overflow: "hidden",
      position: "relative",
    },
    scanOverlay: {
      ...StyleSheet.absoluteFillObject,
      alignItems: "center",
      justifyContent: "center",
    },
    scanFrame: {
      width: 220,
      height: 220,
      borderWidth: 2,
      borderRadius: 12,
      borderColor: "rgba(255,255,255,0.7)",
    },
    manualInput: {
      flexDirection: "row",
      gap: theme.spacing.sm,
    },
    input: {
      flex: 1,
      borderWidth: 1.5,
      borderRadius: theme.radius.md,
      paddingHorizontal: 14,
      paddingVertical: 12,
      fontSize: theme.fontSize.md,
    },
    lookupBtn: {
      paddingHorizontal: 18,
      borderRadius: theme.radius.md,
      alignItems: "center",
      justifyContent: "center",
    },
    shipmentCard: {
      borderRadius: theme.radius.lg,
      borderWidth: 1.5,
      padding: theme.spacing.md,
      gap: theme.spacing.sm,
    },
    shipmentHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    statusChip: {
      paddingHorizontal: 12,
      paddingVertical: 4,
      borderRadius: 20,
    },
    infoRow: {
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
    },
    updateSection: {
      borderRadius: theme.radius.lg,
      borderWidth: 1.5,
      padding: theme.spacing.md,
      gap: theme.spacing.sm,
    },
    statusGrid: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
    },
    statusOption: {
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      paddingHorizontal: 14,
      paddingVertical: 10,
      borderRadius: theme.radius.md,
      borderWidth: 1.5,
    },
    noteInput: {
      borderWidth: 1.5,
      borderRadius: theme.radius.md,
      paddingHorizontal: 14,
      paddingVertical: 12,
      fontSize: theme.fontSize.sm,
      minHeight: 80,
      textAlignVertical: "top",
    },
    updateBtn: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
      paddingVertical: 14,
      borderRadius: theme.radius.md,
    },
  });

export default function AdminBarcodeScanPage() {
  const { theme } = useThemeStore();
  const { isLoggedIn, user } = useAuthStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [permission, requestPermission] = useCameraPermissions();
  const [mode, setMode] = useState<"camera" | "manual">("manual");
  const [manualCode, setManualCode] = useState("");
  const [scanning, setScanning] = useState(false);
  const [shipment, setShipment] = useState<ShipmentInfo | null>(null);
  const [lookupError, setLookupError] = useState("");
  const [newStatus, setNewStatus] = useState("");
  const [eventNote, setEventNote] = useState("");
  const [updating, setUpdating] = useState(false);

  const lookupShipment = useCallback(
    async (code: string) => {
      const trimmed = code.trim();
      if (!trimmed) return;
      setScanning(true);
      setLookupError("");
      setShipment(null);
      setNewStatus("");
      try {
        const data = await apiFetch<ShipmentInfo>(
          `/logistics/shipments/tracking/${encodeURIComponent(trimmed)}`
        );
        setShipment(data);
      } catch {
        setLookupError("No shipment found for this code.");
      } finally {
        setScanning(false);
      }
    },
    []
  );

  const handleBarcodeScan = useCallback(
    ({ data }: { data: string }) => {
      if (!scanning && data) {
        setManualCode(data);
        lookupShipment(data);
      }
    },
    [scanning, lookupShipment]
  );

  const updateStatus = useCallback(async () => {
    if (!shipment || !newStatus) return;
    setUpdating(true);
    try {
      await apiFetch(`/logistics/shipments/${shipment.id}/events`, {
        method: "POST",
        body: JSON.stringify({
          event_type: "status_change",
          status_after: newStatus,
          notes: eventNote || undefined,
        }),
      });
      toast.success("Status updated successfully");
      // Refresh shipment
      const updated = await apiFetch<ShipmentInfo>(
        `/logistics/shipments/${shipment.id}`
      );
      setShipment(updated);
      setNewStatus("");
      setEventNote("");
    } catch {
      toast.error("Failed to update status");
    } finally {
      setUpdating(false);
    }
  }, [shipment, newStatus, eventNote]);

  if (!isLoggedIn || user?.role !== "admin") {
    return (
      <View style={[s.container, { alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: "Admin Barcode" }} />
        <Ionicons name="lock-closed" size={40} color={theme.colors.textMuted} />
        <Text style={[s.text, { marginTop: 12 }]}>Admin access required</Text>
        <TouchableOpacity
          onPress={() => router.push("/admin/login")}
          style={{ marginTop: 16, paddingHorizontal: 24, paddingVertical: 10, backgroundColor: theme.colors.brand, borderRadius: theme.radius.md }}
        >
          <Text style={{ color: "#fff", fontWeight: "700" }}>Login</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surface0 }]}>
      <Stack.Screen options={{ title: "Barcode Scanner", headerStyle: { backgroundColor: theme.colors.surface1 }, headerTintColor: theme.colors.text }} />
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Mode Toggle */}
        <View style={[styles.modeToggle, { borderColor: theme.colors.border }]}>
          <TouchableOpacity
            style={[styles.modeBtn, mode === "camera" && { backgroundColor: theme.colors.brand }]}
            onPress={() => {
              setMode("camera");
              if (!permission?.granted) requestPermission();
            }}
          >
            <Ionicons name="camera" size={18} color={mode === "camera" ? "#fff" : theme.colors.text} />
            <Text style={{ color: mode === "camera" ? "#fff" : theme.colors.text, fontWeight: "600" }}>Camera</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeBtn, mode === "manual" && { backgroundColor: theme.colors.brand }]}
            onPress={() => setMode("manual")}
          >
            <Feather name="edit-3" size={18} color={mode === "manual" ? "#fff" : theme.colors.text} />
            <Text style={{ color: mode === "manual" ? "#fff" : theme.colors.text, fontWeight: "600" }}>Manual</Text>
          </TouchableOpacity>
        </View>

        {/* Camera View */}
        {mode === "camera" && CameraView && permission?.granted && (
          <View style={styles.cameraBox}>
            <CameraView
              style={StyleSheet.absoluteFill}
              onBarcodeScanned={handleBarcodeScan}
              barcodeScannerSettings={{ barcodeTypes: ["qr", "code128", "ean13", "ean8", "code39"] }}
            />
            <View style={styles.scanOverlay}>
              <View style={styles.scanFrame} />
            </View>
          </View>
        )}

        {mode === "camera" && !CameraView && (
          <View style={[styles.cameraBox, { backgroundColor: theme.colors.surface1, alignItems: "center", justifyContent: "center" }]}>
            <Ionicons name="camera-outline" size={40} color={theme.colors.textMuted} />
            <Text style={[s.text, { marginTop: 8 }]}>Camera not available</Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>Use manual entry instead</Text>
          </View>
        )}

        {/* Manual Entry */}
        <View style={styles.manualInput}>
          <TextInput
            style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 }]}
            value={manualCode}
            onChangeText={setManualCode}
            placeholder="Enter tracking code..."
            placeholderTextColor={theme.colors.textMuted}
            returnKeyType="search"
            onSubmitEditing={() => lookupShipment(manualCode)}
          />
          <TouchableOpacity
            style={[styles.lookupBtn, { backgroundColor: theme.colors.brand }]}
            onPress={() => lookupShipment(manualCode)}
            disabled={scanning}
          >
            {scanning ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Ionicons name="search" size={22} color="#fff" />
            )}
          </TouchableOpacity>
        </View>

        {/* Error */}
        {lookupError ? (
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8, padding: 12, backgroundColor: theme.colors.danger + "18", borderRadius: theme.radius.md }}>
            <Ionicons name="close-circle" size={20} color={theme.colors.danger} />
            <Text style={{ color: theme.colors.danger, flex: 1 }}>{lookupError}</Text>
          </View>
        ) : null}

        {/* Shipment Result */}
        {shipment && (
          <View style={[styles.shipmentCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
            <View style={styles.shipmentHeader}>
              <Text style={{ fontSize: 18, fontWeight: "800", color: theme.colors.text }}>
                Shipment #{shipment.id}
              </Text>
              <View style={[styles.statusChip, { backgroundColor: (STATUS_COLORS[shipment.status] || theme.colors.textMuted) + "22" }]}>
                <Text style={{ color: STATUS_COLORS[shipment.status] || theme.colors.textMuted, fontWeight: "700", fontSize: 12 }}>
                  {shipment.status.replace(/_/g, " ").toUpperCase()}
                </Text>
              </View>
            </View>

            <View style={styles.infoRow}>
              <Ionicons name="receipt-outline" size={16} color={theme.colors.textMuted} />
              <Text style={{ color: theme.colors.textMuted }}>Order #{shipment.order_id}</Text>
            </View>
            {shipment.tracking_number && (
              <View style={styles.infoRow}>
                <Ionicons name="barcode-outline" size={16} color={theme.colors.textMuted} />
                <Text style={{ color: theme.colors.textMuted }}>{shipment.tracking_number}</Text>
              </View>
            )}
            {shipment.carrier_name && (
              <View style={styles.infoRow}>
                <Ionicons name="car-outline" size={16} color={theme.colors.textMuted} />
                <Text style={{ color: theme.colors.textMuted }}>{shipment.carrier_name}</Text>
              </View>
            )}
            {shipment.current_hub && (
              <View style={styles.infoRow}>
                <Ionicons name="location-outline" size={16} color={theme.colors.textMuted} />
                <Text style={{ color: theme.colors.textMuted }}>{shipment.current_hub}</Text>
              </View>
            )}
            {shipment.shipping_address && (
              <View style={styles.infoRow}>
                <Ionicons name="home-outline" size={16} color={theme.colors.textMuted} />
                <Text style={{ color: theme.colors.textMuted, flex: 1 }}>{shipment.shipping_address}</Text>
              </View>
            )}
          </View>
        )}

        {/* Update Status Section */}
        {shipment && (
          <View style={[styles.updateSection, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
            <Text style={{ fontSize: 16, fontWeight: "700", color: theme.colors.text }}>Update Status</Text>

            <View style={styles.statusGrid}>
              {STATUS_OPTIONS.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={[
                    styles.statusOption,
                    {
                      borderColor: newStatus === opt.value ? theme.colors.brand : theme.colors.border,
                      backgroundColor: newStatus === opt.value ? theme.colors.brand + "18" : "transparent",
                    },
                  ]}
                  onPress={() => setNewStatus(opt.value)}
                >
                  <Ionicons
                    name={opt.icon}
                    size={16}
                    color={newStatus === opt.value ? theme.colors.brand : theme.colors.textMuted}
                  />
                  <Text
                    style={{
                      color: newStatus === opt.value ? theme.colors.brand : theme.colors.text,
                      fontWeight: "600",
                      fontSize: 13,
                    }}
                  >
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TextInput
              style={[styles.noteInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface0 }]}
              value={eventNote}
              onChangeText={setEventNote}
              placeholder="Add a note (optional)..."
              placeholderTextColor={theme.colors.textMuted}
              multiline
            />

            <TouchableOpacity
              style={[styles.updateBtn, { backgroundColor: newStatus ? theme.colors.brand : theme.colors.border }]}
              onPress={updateStatus}
              disabled={!newStatus || updating}
            >
              {updating ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <>
                  <Ionicons name="checkmark-circle" size={20} color="#fff" />
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: 16 }}>Update Status</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
}
