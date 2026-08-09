import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { apiFetch, scanShipmentEvent, verifyProductBarcode, ProductVerificationResult } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles } from "@/theme";
import ScreenHeader from "@/components/ui/ScreenHeader";

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
  useCameraPermissions = () => [null, () => {}];
}

interface ScannedProduct {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
}

interface ShipmentScanResult {
  shipment: {
    id: number;
    order_id: number;
    status: string;
    distribution_channel?: string;
    current_hub?: string;
  };
  event: {
    id: number;
    event_type: string;
    status_after?: string;
    location?: string;
    created_at: string;
  };
}

type ScanTarget = "product" | "transaction" | "verification";
type ShipmentEventType =
  | "picked_from_supplier"
  | "logistics_received"
  | "distribution_checkpoint"
  | "out_for_delivery"
  | "customer_received"
  | "shipment_failed"
  | "shipment_returned";

const EVENT_TYPE_OPTIONS: { value: ShipmentEventType; label: string }[] = [
  { value: "picked_from_supplier", label: "Picked" },
  { value: "logistics_received", label: "Logistics In" },
  { value: "distribution_checkpoint", label: "Checkpoint" },
  { value: "out_for_delivery", label: "Out For Delivery" },
  { value: "customer_received", label: "Customer Received" },
  { value: "shipment_failed", label: "Failed" },
  { value: "shipment_returned", label: "Returned" },
];

export default function BarcodeScanScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const formatPrice = useCurrencyStore((state) => state.format);
  const router = useRouter();
  const params = useLocalSearchParams<{
    code?: string;
    target?: ScanTarget;
    event_type?: ShipmentEventType;
    location?: string;
    distribution_channel?: string;
  }>();

  const [permissions, requestPermission] = useCameraPermissions();
  const [mode, setMode] = useState<"camera" | "manual">(CameraView ? "camera" : "manual");
  const [target, setTarget] = useState<ScanTarget>("product");
  const [manualCode, setManualCode] = useState("");
  const [eventType, setEventType] = useState<ShipmentEventType>("distribution_checkpoint");
  const [location, setLocation] = useState("");
  const [distributionChannel, setDistributionChannel] = useState("");
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [product, setProduct] = useState<ScannedProduct | null>(null);
  const [shipmentResult, setShipmentResult] = useState<ShipmentScanResult | null>(null);
  const [verificationResult, setVerificationResult] = useState<ProductVerificationResult | null>(null);

  useEffect(() => {
    const incomingTarget = params.target;
    if (incomingTarget === "transaction" || incomingTarget === "product") {
      setTarget(incomingTarget);
    }
    if (typeof params.code === "string" && params.code.trim()) {
      setManualCode(params.code.trim());
    }
    if (
      typeof params.event_type === "string" &&
      EVENT_TYPE_OPTIONS.some((option) => option.value === params.event_type)
    ) {
      setEventType(params.event_type);
    }
    if (typeof params.location === "string" && params.location.trim()) {
      setLocation(params.location.trim());
    }
    if (
      typeof params.distribution_channel === "string" &&
      params.distribution_channel.trim()
    ) {
      setDistributionChannel(params.distribution_channel.trim());
    }
  }, [params]);

  const lookup = async (rawCode: string) => {
    const code = rawCode.trim();
    if (!code) return;

    setLoading(true);
    setError(null);
    setProduct(null);
    setShipmentResult(null);
    setVerificationResult(null);
    try {
      if (target === "verification") {
        const result = await verifyProductBarcode({ barcode: code });
        setVerificationResult(result);
      } else if (target === "transaction") {
        const match = code.toUpperCase().match(/^SHIP-(\d+)$/);
        if (!match) {
          setError("Transaction scan format must be SHIP-<id>.");
        } else {
          const shipmentId = Number(match[1]);
          const result = await scanShipmentEvent(shipmentId, {
            scan_code: code,
            event_type: eventType,
            location: location.trim() || undefined,
            distribution_channel: distributionChannel.trim() || undefined,
          });
          setShipmentResult(result as ShipmentScanResult);
        }
      } else {
        const result = await apiFetch<ScannedProduct>(`/products/barcode/${encodeURIComponent(code)}`);
        if ((result as any)?.id) {
          setProduct(result as ScannedProduct);
        } else {
          setError("No product found for this code.");
        }
      }
    } catch {
      const msgs: Record<ScanTarget, string> = {
        transaction: "Failed to register shipment scan.",
        product: "Failed to lookup product.",
        verification: "Failed to verify barcode.",
      };
      setError(msgs[target]);
    } finally {
      setLoading(false);
    }
  };

  const onScanned = ({ data }: { type: string; data: string }) => {
    if (scanned) return;
    setScanned(true);
    lookup(data);
  };

  return (
    <View style={[s.container, { paddingTop: 0 }]}>
      <ScreenHeader
        title="Barcode / QR Scanner"
        rightIcon={mode === "camera" ? "keypad-outline" : "camera-outline"}
        onRightPress={() => setMode(mode === "camera" ? "manual" : "camera")}
      />

      {mode === "camera" && CameraView && (
        <View style={{ flex: 1 }}>
          {!permissions?.granted ? (
            <View style={styles.centered}>
              <Text style={[s.textMuted, { textAlign: "center", marginBottom: 16 }]}>
                Camera permission is required to scan.
              </Text>
              <TouchableOpacity onPress={requestPermission} style={[styles.btn, { backgroundColor: theme.colors.brand }]}>
                <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Grant Permission</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <CameraView
                style={StyleSheet.absoluteFill}
                facing="back"
                barcodeScannerSettings={{ barcodeTypes: ["qr", "ean13", "ean8", "code128", "code39", "upc_a", "upc_e"] }}
                onBarcodeScanned={scanned ? undefined : onScanned}
              />
              <View style={styles.overlay}>
                <View style={styles.frame} />
                <Text style={styles.overlayText}>
                  {target === "transaction" ? "Scan shipment code (SHIP-...)" : target === "verification" ? "Scan barcode to verify" : "Scan product barcode or QR"}
                </Text>
                <View style={styles.targetRow}>
                  <TouchableOpacity
                    onPress={() => setTarget("product")}
                    style={[styles.targetBtn, { backgroundColor: target === "product" ? theme.colors.brand : "rgba(0,0,0,0.45)" }]}
                  >
                    <Text style={styles.targetText}>Product</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => setTarget("transaction")}
                    style={[styles.targetBtn, { backgroundColor: target === "transaction" ? theme.colors.brand : "rgba(0,0,0,0.45)" }]}
                  >
                    <Text style={styles.targetText}>Transaction</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => setTarget("verification")}
                    style={[styles.targetBtn, { backgroundColor: target === "verification" ? theme.colors.brand : "rgba(0,0,0,0.45)" }]}
                  >
                    <Text style={styles.targetText}>Verify</Text>
                  </TouchableOpacity>
                </View>
              </View>
              {scanned && (
                <TouchableOpacity
                  style={[styles.btn, { position: "absolute", bottom: 28, alignSelf: "center", backgroundColor: theme.colors.brand, paddingHorizontal: 20 }]}
                  onPress={() => {
                    setScanned(false);
                    setProduct(null);
                    setShipmentResult(null);
                    setError(null);
                  }}
                >
                  <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Scan Again</Text>
                </TouchableOpacity>
              )}
            </>
          )}
        </View>
      )}

      {(mode === "manual" || !CameraView) && (
        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
          <View style={{ flexDirection: "row", gap: 8, marginBottom: 12 }}>
            <TouchableOpacity
              onPress={() => setTarget("product")}
              style={[styles.targetSwitch, { backgroundColor: target === "product" ? theme.colors.brand : theme.colors.surface1, borderColor: theme.colors.border }]}
            >
              <Text style={{ color: target === "product" ? theme.colors.onBrand : theme.colors.text, fontWeight: "700", fontSize: 12 }}>Product</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setTarget("transaction")}
              style={[styles.targetSwitch, { backgroundColor: target === "transaction" ? theme.colors.brand : theme.colors.surface1, borderColor: theme.colors.border }]}
            >
              <Text style={{ color: target === "transaction" ? theme.colors.onBrand : theme.colors.text, fontWeight: "700", fontSize: 12 }}>Transaction</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setTarget("verification")}
              style={[styles.targetSwitch, { backgroundColor: target === "verification" ? theme.colors.brand : theme.colors.surface1, borderColor: theme.colors.border }]}
            >
              <Text style={{ color: target === "verification" ? theme.colors.onBrand : theme.colors.text, fontWeight: "700", fontSize: 12 }}>Verify</Text>
            </TouchableOpacity>
          </View>

          <Text style={[s.text, { fontWeight: "800", fontSize: 18, marginBottom: 4 }]}>
            {target === "product" ? "Manual Product Lookup" : target === "verification" ? "Verify Product Barcode" : "Manual Shipment Scan"}
          </Text>
          <Text style={[s.textMuted, { marginBottom: 14, fontSize: 13 }]}>
            {target === "product"
              ? "Enter product barcode format: P-<id> or numeric id."
              : target === "verification"
              ? "Enter the barcode / QR code to submit for product verification."
              : "Enter shipment scan code format: SHIP-<id>."}
          </Text>

          {target === "transaction" && (
            <View style={{ gap: 8, marginBottom: 12 }}>
              <Text style={[s.textMuted, { fontSize: 12, marginBottom: -2 }]}>Event Type</Text>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                {EVENT_TYPE_OPTIONS.map((option) => {
                  const active = eventType === option.value;
                  return (
                    <TouchableOpacity
                      key={option.value}
                      onPress={() => setEventType(option.value)}
                      style={[
                        styles.eventTypePill,
                        {
                          backgroundColor: active ? theme.colors.brand : theme.colors.surface1,
                          borderColor: active ? theme.colors.brand : theme.colors.border,
                        },
                      ]}
                    >
                      <Text style={{ color: active ? theme.colors.onBrand : theme.colors.text, fontSize: 11, fontWeight: "700" }}>
                        {option.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
              <TextInput
                value={location}
                onChangeText={setLocation}
                placeholder="Location / hub (optional)"
                placeholderTextColor={theme.colors.textMuted}
                style={s.input}
              />
              <TextInput
                value={distributionChannel}
                onChangeText={setDistributionChannel}
                placeholder="Distribution channel (optional)"
                placeholderTextColor={theme.colors.textMuted}
                style={s.input}
              />
            </View>
          )}

          <View style={{ flexDirection: "row", gap: 8, marginBottom: 16 }}>
            <TextInput
              value={manualCode}
              onChangeText={setManualCode}
              placeholder={target === "product" ? "Barcode / QR code" : "Shipment code (SHIP-...)"}
              placeholderTextColor={theme.colors.textMuted}
              style={[s.input, { flex: 1 }]}
              returnKeyType="search"
              onSubmitEditing={() => lookup(manualCode)}
            />
            <TouchableOpacity
              onPress={() => lookup(manualCode)}
              disabled={loading || !manualCode.trim()}
              style={[styles.btn, { backgroundColor: loading ? theme.colors.surface2 : theme.colors.brand, paddingHorizontal: 14 }]}
            >
              {loading ? <ActivityIndicator size="small" color={theme.colors.onBrand} /> : <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Lookup</Text>}
            </TouchableOpacity>
          </View>

          {error && (
            <View style={[styles.card, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}>
              <Text style={{ color: theme.colors.danger, fontWeight: "700", marginBottom: 4 }}>Error</Text>
              <Text style={{ color: theme.colors.danger, fontSize: 13 }}>{error}</Text>
            </View>
          )}

          {product && (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.brand + "55" }]}>
              <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 4 }]}>{product.name}</Text>
              <Text style={[s.textMuted, { fontSize: 13 }]}>{product.category}</Text>
              <View style={{ flexDirection: "row", gap: 16, marginTop: 10 }}>
                <Text style={{ color: theme.colors.brand, fontWeight: "800" }}>{formatPrice(Number(product.price))}</Text>
                <Text style={{ color: product.stock > 0 ? theme.colors.success : theme.colors.danger, fontWeight: "700" }}>
                  Stock: {product.stock}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => router.push(`/(tabs)/products/${product.id}` as never)}
                style={[styles.btn, { marginTop: 10, backgroundColor: theme.colors.brand }]}
              >
                <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Open Product</Text>
              </TouchableOpacity>
            </View>
          )}

          {verificationResult && (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.brand + "55" }]}>
              <Text style={[s.text, { fontWeight: "800", fontSize: 16 }]}>
                Verification #{verificationResult.id}
              </Text>
              {verificationResult.product_name && (
                <Text style={[s.textMuted, { marginTop: 4, fontSize: 13 }]}>{verificationResult.product_name}</Text>
              )}
              <Text style={[
                { marginTop: 6, fontSize: 13, fontWeight: "700" },
                { color: verificationResult.status === "verified" ? theme.colors.success : verificationResult.status === "failed" ? theme.colors.danger : theme.colors.warning },
              ]}>
                Status: {verificationResult.status.toUpperCase()}
              </Text>
              {verificationResult.notes && (
                <Text style={[s.textMuted, { fontSize: 12, marginTop: 4 }]}>{verificationResult.notes}</Text>
              )}
            </View>
          )}

          {shipmentResult && (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.brand + "55" }]}>
              <Text style={[s.text, { fontWeight: "800", fontSize: 16 }]}>
                Shipment #{shipmentResult.shipment.id} · Order #{shipmentResult.shipment.order_id}
              </Text>
              <Text style={[s.textMuted, { marginTop: 6, fontSize: 12 }]}>
                Event: {shipmentResult.event.event_type}
              </Text>
              <Text style={[s.textMuted, { fontSize: 12 }]}>
                Status: {shipmentResult.shipment.status}
              </Text>
              {shipmentResult.event.location && (
                <Text style={[s.textMuted, { fontSize: 12 }]}>
                  Location: {shipmentResult.event.location}
                </Text>
              )}
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

export function ErrorBoundary({
  error,
  retry,
}: {
  error: Error;
  retry: () => void;
}) {
  const { theme } = useThemeStore();
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", padding: 24, gap: 10 }}>
      <Text style={{ fontSize: 16, fontWeight: "700", textAlign: "center" }}>Scanner Error</Text>
      <Text style={{ fontSize: 12, color: theme.colors.textMuted, textAlign: "center" }}>{error.message}</Text>
      <TouchableOpacity
        onPress={retry}
        style={{ backgroundColor: theme.colors.brand, borderRadius: 10, paddingHorizontal: 16, paddingVertical: 10 }}
      >
        <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Retry</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  btn: {
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
  },
  frame: {
    width: 240,
    height: 240,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: "#ffffff",
    marginBottom: 12,
  },
  overlayText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700",
    backgroundColor: "rgba(0,0,0,0.45)",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  targetRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 12,
  },
  targetBtn: {
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  targetText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700",
  },
  targetSwitch: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginTop: 8,
  },
  eventTypePill: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
});
