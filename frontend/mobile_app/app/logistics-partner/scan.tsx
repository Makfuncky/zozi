import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import {
  createLogisticsPartnerShipmentConfirmationRequest,
  lookupLogisticsPartnerShipment,
  updateLogisticsPartnerShipmentStatus,
  type LogisticsPartnerShipment,
} from "@/lib/api";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import SignaturePad from "@/components/SignaturePad";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";
import { formatLocalizedDateTime, isRtlLocale } from "@shared/localization";

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

type ShipmentStatus = "processing" | "prepared" | "picking_up" | "shipped" | "in_transit" | "delivered" | "failed" | "returned";
type EventType =
  | "picked_from_supplier"
  | "pickup_confirmed"
  | "pickup_cancelled"
  | "logistics_received"
  | "distribution_checkpoint"
  | "out_for_delivery"
  | "customer_received"
  | "shipment_failed"
  | "shipment_returned"
  | "shipment_delayed"
  | "shipment_rescheduled"
  | "shipment_cancelled";

type ShipmentAction = {
  status: ShipmentStatus;
  eventType: EventType;
  label: string;
};

const FAILURE_EVENT_TYPES = new Set<EventType>([
  "shipment_failed",
  "shipment_returned",
  "shipment_cancelled",
]);

function formatShipmentStatus(shipment: LogisticsPartnerShipment): string {
  return shipment.status_label || shipment.status.replace(/_/g, " ");
}

const STATUS_COLORS: Record<string, string> = {
  prepared: "#8b5cf6",
  picking_up: "#6366f1",
  shipped: "#3b82f6",
  in_transit: "#f59e0b",
  delivered: "#22c55e",
  failed: "#ef4444",
  returned: "#ef4444",
  processing: "#94a3b8",
};

function getAvailableActions(currentStatus: string): ShipmentAction[] {
  switch (currentStatus) {
    case "prepared":
      return [{ status: "picking_up", eventType: "pickup_confirmed", label: "Confirm Pickup" }];
    case "picking_up":
      return [
        { status: "shipped", eventType: "picked_from_supplier", label: "Picked From Supplier" },
        { status: "prepared", eventType: "pickup_cancelled", label: "Cancel Pickup" },
      ];
    case "shipped":
      return [
        { status: "shipped", eventType: "logistics_received", label: "Logistics Received" },
        { status: "in_transit", eventType: "distribution_checkpoint", label: "Distribution Checkpoint" },
        { status: "in_transit", eventType: "out_for_delivery", label: "Out for Delivery" },
        { status: "shipped", eventType: "shipment_delayed", label: "Shipment Delayed" },
        { status: "shipped", eventType: "shipment_rescheduled", label: "Shipment Rescheduled" },
        { status: "failed", eventType: "shipment_failed", label: "Shipment Failed" },
        { status: "returned", eventType: "shipment_cancelled", label: "Shipment Cancelled" },
        { status: "returned", eventType: "shipment_returned", label: "Shipment Returned" },
      ];
    case "in_transit":
      return [
        { status: "in_transit", eventType: "distribution_checkpoint", label: "Distribution Checkpoint" },
        { status: "in_transit", eventType: "out_for_delivery", label: "Out for Delivery" },
        { status: "delivered", eventType: "customer_received", label: "Delivered" },
        { status: "in_transit", eventType: "shipment_delayed", label: "Shipment Delayed" },
        { status: "in_transit", eventType: "shipment_rescheduled", label: "Shipment Rescheduled" },
        { status: "failed", eventType: "shipment_failed", label: "Shipment Failed" },
        { status: "returned", eventType: "shipment_cancelled", label: "Shipment Cancelled" },
        { status: "returned", eventType: "shipment_returned", label: "Shipment Returned" },
      ];
    default:
      return [];
  }
}

function actionRequiresConfirmationRequest(shipment: LogisticsPartnerShipment | null, status: string): boolean {
  if (!shipment) return false;
  return (
    (shipment.status === "picking_up" && status === "shipped")
    || ((shipment.status === "shipped" || shipment.status === "in_transit") && status === "delivered")
  );
}

function actionRequiresFailureReason(eventType: EventType | ""): boolean {
  return eventType ? FAILURE_EVENT_TYPES.has(eventType) : false;
}

export default function LogisticsPartnerScanScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const router = useRouter();
  const params = useLocalSearchParams<{ code?: string }>();
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [permissions, requestPermission] = useCameraPermissions();
  const [
    scanShipmentTitle,
    cameraLabel,
    manualLabel,
    cameraPermissionLabel,
    grantPermissionLabel,
    scanHintLabel,
    scanAgainLabel,
    lookupShipmentLabel,
    lookupHintLabel,
    shipmentCodePlaceholderLabel,
    lookupLabel,
    shipmentLabel,
    orderLabel,
    statusLabel,
    customerLabel,
    phoneLabel,
    addressLabel,
    locationLabel,
    carrierLabel,
    trackingLabel,
    scanCodeLabel,
    packagesLabel,
    weightLabel,
    dimensionsLabel,
    packagingNotesLabel,
    etaLabel,
    deliverySignatureCapturedLabel,
    updateStatusLabel,
    confirmationLabel,
    requestPendingLabel,
    waitingForLabel,
    recipientLabel,
    noActionsAvailableLabel,
    selectedMilestoneLabel,
    chooseActionLabel,
    currentHubPlaceholderLabel,
    trackingNumberPlaceholderLabel,
    notesPlaceholderLabel,
    customerSignatureLabel,
    customerFullNamePlaceholderLabel,
    signatureRequiredLabel,
    awaitingConfirmationLabel,
    sendConfirmationRequestLabel,
    updateShipmentLabel,
    openTrackerLabel,
    failureDetailsLabel,
    failureReasonRequiredLabel,
    failureNotesPlaceholderLabel,
  ] = useTranslateTexts([
    "Scan Shipment",
    "Camera",
    "Manual",
    "Camera permission is required to scan shipment QR or barcode labels.",
    "Grant Permission",
    "Scan the shipment label or enter the code manually below.",
    "Scan Again",
    "Lookup Shipment",
    "Use the printed parcel scan code or the tracking number.",
    "SHIP-123 or tracking number",
    "Lookup",
    "Shipment",
    "Order",
    "Status",
    "Customer",
    "Phone",
    "Address",
    "Location",
    "Carrier",
    "Tracking",
    "Scan code",
    "Packages",
    "Weight",
    "Dimensions",
    "Packaging notes",
    "ETA",
    "Delivery signature captured",
    "Update Status",
    "Confirmation",
    "request pending",
    "Waiting for",
    "the recipient",
    "No actions are available for this shipment in the mobile workflow.",
    "Selected Milestone",
    "Choose an action to update this shipment.",
    "Current hub (optional)",
    "Tracking number (optional)",
    "Notes (optional)",
    "Customer Signature",
    "Customer full name",
    "Delivery confirmation requires a signature from the receiving customer.",
    "Awaiting Confirmation",
    "Send Confirmation Request",
    "Update Shipment",
    "Open Tracker",
    "Failure Details",
    "Add a failure or return reason before updating this shipment.",
    "Describe the failed attempt, return reason, or cancellation cause",
  ]);

  const [mode, setMode] = useState<"camera" | "manual">(CameraView ? "camera" : "manual");
  const [manualCode, setManualCode] = useState("");
  const [shipment, setShipment] = useState<LogisticsPartnerShipment | null>(null);
  const [lookupError, setLookupError] = useState("");
  const [loading, setLoading] = useState(false);
  const [scanned, setScanned] = useState(false);

  const [newStatus, setNewStatus] = useState<ShipmentStatus>("processing");
  const [eventType, setEventType] = useState<EventType | "">("");
  const [currentHub, setCurrentHub] = useState("");
  const [trackingNumber, setTrackingNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [signatureName, setSignatureName] = useState("");
  const [signatureDataUrl, setSignatureDataUrl] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState("");

  const availableActions = useMemo(() => (shipment ? getAvailableActions(shipment.status) : []), [shipment]);
  const translatedAvailableActionLabels = useTranslateTexts(availableActions.map((action) => action.label));
  const activeConfirmation = shipment?.active_confirmation_request ?? null;
  const hasPendingConfirmation = activeConfirmation?.status === "pending";

  useEffect(() => {
    if (typeof params.code === "string" && params.code.trim()) {
      setManualCode(params.code.trim());
      setMode("manual");
    }
  }, [params.code]);

  useEffect(() => {
    if (typeof params.code !== "string") return;
    const initialCode = params.code.trim();
    if (!initialCode) return;
    setManualCode(initialCode);
    setMode("manual");
    void lookupShipment(initialCode);
  }, [params.code]);

  async function lookupShipment(rawCode: string) {
    const code = rawCode.trim();
    if (!code) return;

    setLoading(true);
    setLookupError("");
    setShipment(null);
    setUpdateMessage("");
    try {
      const payload = await lookupLogisticsPartnerShipment(code);
      setShipment(payload);
      setCurrentHub(payload.current_hub || "");
      setTrackingNumber(payload.tracking_number || "");
      setSignatureName(payload.customer_name || payload.delivery_signature_name || "");
      setSignatureDataUrl(null);
      setManualCode(code);
      const initialAction = getAvailableActions(payload.status)[0];
      setNewStatus(initialAction?.status ?? (payload.status as ShipmentStatus));
      setEventType(initialAction?.eventType ?? "");
    } catch (err: any) {
      setLookupError(err?.detail || `No shipment found for code "${code}".`);
    } finally {
      setLoading(false);
    }
  }

  async function updateShipment() {
    if (!shipment) return;
    if (!availableActions.length) {
      setLookupError("This shipment has no available mobile actions.");
      return;
    }
    if (shipment.active_confirmation_request?.status === "pending") {
      setLookupError("A confirmation request is already pending for this shipment.");
      return;
    }
    if (actionRequiresFailureReason(eventType) && !notes.trim()) {
      setLookupError(failureReasonRequiredLabel);
      return;
    }
    if (newStatus === "delivered") {
      if (!signatureName.trim() || !signatureDataUrl) {
        setLookupError("Customer name and signature are required to confirm delivery.");
        return;
      }
    }
    setUpdating(true);
    setUpdateMessage("");
    setLookupError("");
    try {
      const requiresConfirmationRequest = actionRequiresConfirmationRequest(shipment, newStatus);
      if (requiresConfirmationRequest) {
        const created = await createLogisticsPartnerShipmentConfirmationRequest(shipment.id, {
          requested_status: newStatus === "delivered" ? "delivered" : "shipped",
          delivery_signature_name: newStatus === "delivered" ? signatureName.trim() : undefined,
          delivery_signature_data_url: newStatus === "delivered" ? signatureDataUrl || undefined : undefined,
          event_type: eventType || undefined,
          current_hub: currentHub || undefined,
          tracking_number: trackingNumber || undefined,
          notes: notes || undefined,
          scan_code: manualCode || shipment.scan_code || undefined,
        });
        setShipment((prev) =>
          prev
            ? {
                ...prev,
                current_hub: created.request.current_hub ?? currentHub ?? prev.current_hub,
                tracking_number: created.request.tracking_number ?? trackingNumber ?? prev.tracking_number,
                active_confirmation_request: created.request,
              }
            : prev
        );
        setUpdateMessage("Confirmation request sent. Status will update after approval.");
      } else {
        const updated = await updateLogisticsPartnerShipmentStatus(shipment.id, {
          status: newStatus,
          release_assignment: shipment.status === "picking_up" && newStatus === "prepared",
          delivery_signature_name: newStatus === "delivered" ? signatureName.trim() : undefined,
          delivery_signature_data_url: newStatus === "delivered" ? signatureDataUrl || undefined : undefined,
          event_type: eventType || undefined,
          current_hub: currentHub || undefined,
          tracking_number: trackingNumber || undefined,
          notes: notes || undefined,
          scan_code: manualCode || shipment.scan_code || undefined,
        });
        setShipment((prev) =>
          prev
            ? {
                ...prev,
                status: updated.status,
                status_label: updated.status_label ?? prev.status_label,
                current_hub: updated.current_hub ?? currentHub,
                tracking_number: updated.tracking_number ?? trackingNumber,
                delivery_signature_name: newStatus === "delivered" ? signatureName.trim() : prev.delivery_signature_name,
                delivery_signature_data_url: newStatus === "delivered" ? signatureDataUrl : prev.delivery_signature_data_url,
                delivery_signature_captured_at: newStatus === "delivered" ? new Date().toISOString() : prev.delivery_signature_captured_at,
                active_confirmation_request: null,
              }
            : prev
        );
        const nextAction = getAvailableActions(updated.status)[0];
        setNewStatus(nextAction?.status ?? updated.status);
        setEventType(nextAction?.eventType ?? "");
        setUpdateMessage("Shipment status updated.");
      }
      setNotes("");
    } catch (err: any) {
      setLookupError(err?.detail || "Could not update shipment status.");
    } finally {
      setUpdating(false);
    }
  }

  function onScanned({ data }: { data: string }) {
    if (scanned) return;
    setScanned(true);
    lookupShipment(data);
  }

  const selectedAction = availableActions.find((action) => action.status === newStatus && action.eventType === eventType) || null;
  const selectedActionRequiresConfirmation = actionRequiresConfirmationRequest(shipment, newStatus);
  const selectedActionRequiresFailureReason = actionRequiresFailureReason(eventType);
  const actionButtonLabel = hasPendingConfirmation
    ? awaitingConfirmationLabel
    : selectedActionRequiresConfirmation
      ? sendConfirmationRequestLabel
      : (selectedAction ? translatedAvailableActionLabels[availableActions.indexOf(selectedAction)] || selectedAction.label : updateShipmentLabel);

  return (
    <View style={[s.container, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen options={{ title: scanShipmentTitle }} />

      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40, gap: 12 }} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "800", textTransform: "uppercase", letterSpacing: 0.8 }}>
            Mobile Scan Workflow
          </Text>
          <Text style={[s.text, { fontWeight: "800", fontSize: theme.fontSize.xl }]}>
            {shipment ? `Shipment #${shipment.id}` : "Lookup a shipment to continue"}
          </Text>
          <Text style={s.textMuted}>
            {shipment
              ? "Review the shipment details, choose the correct milestone, and capture only the proof required for that step."
              : "Use the camera for the fastest intake path, or switch to manual lookup when a barcode is damaged or unavailable."}
          </Text>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
            <View style={[styles.noticeBox, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, minWidth: 110 }]}> 
              <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{mode === "camera" ? cameraLabel : manualLabel}</Text>
              <Text style={s.textMuted}>Input mode</Text>
            </View>
            {shipment ? (
              <View style={[styles.noticeBox, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, minWidth: 150 }]}> 
                <Text style={{ color: STATUS_COLORS[shipment.status] || theme.colors.text, fontWeight: "700", textTransform: "capitalize" }}>
                  {formatShipmentStatus(shipment)}
                </Text>
                <Text style={s.textMuted}>{shipment.scan_code || shipment.tracking_number || "No code assigned yet"}</Text>
              </View>
            ) : null}
          </View>
        </View>

        <View style={{ flexDirection: "row", gap: 8 }}>
          <TouchableOpacity
            onPress={() => setMode("camera")}
            style={[styles.modeBtn, { backgroundColor: mode === "camera" ? theme.colors.brand : theme.colors.surface1, borderColor: theme.colors.border }]}
          >
            <Text style={{ color: mode === "camera" ? "#fff" : theme.colors.text, fontWeight: "700" }}>{cameraLabel}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => setMode("manual")}
            style={[styles.modeBtn, { backgroundColor: mode === "manual" ? theme.colors.brand : theme.colors.surface1, borderColor: theme.colors.border }]}
          >
            <Text style={{ color: mode === "manual" ? "#fff" : theme.colors.text, fontWeight: "700" }}>{manualLabel}</Text>
          </TouchableOpacity>
        </View>

        {mode === "camera" && CameraView ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            {!permissions?.granted ? (
              <View style={{ gap: 12, alignItems: "center" }}>
                <Text style={[s.textMuted, { textAlign: "center" }]}>{cameraPermissionLabel}</Text>
                <TouchableOpacity onPress={requestPermission} style={[styles.primaryBtn, { backgroundColor: theme.colors.brand }]}>
                  <Text style={styles.primaryBtnText}>{grantPermissionLabel}</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                <View style={{ height: 280, overflow: "hidden", borderRadius: 16 }}>
                  <CameraView
                    style={StyleSheet.absoluteFill}
                    facing="back"
                    barcodeScannerSettings={{ barcodeTypes: ["qr", "ean13", "ean8", "code128", "code39", "upc_a", "upc_e"] }}
                    onBarcodeScanned={scanned ? undefined : onScanned}
                  />
                </View>
                <Text style={[s.textMuted, { textAlign: "center" }]}>{scanHintLabel}</Text>
                {scanned ? (
                  <TouchableOpacity onPress={() => setScanned(false)} style={[styles.primaryBtn, { backgroundColor: theme.colors.brand }]}> 
                    <Text style={styles.primaryBtnText}>{scanAgainLabel}</Text>
                  </TouchableOpacity>
                ) : null}
              </>
            )}
          </View>
        ) : null}

        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>{lookupShipmentLabel}</Text>
          <Text style={s.textMuted}>{lookupHintLabel}</Text>
          <View style={{ flexDirection: "row", gap: 8 }}>
            <TextInput
              value={manualCode}
              onChangeText={setManualCode}
              placeholder={shipmentCodePlaceholderLabel}
              placeholderTextColor={theme.colors.textMuted}
              style={[s.input, { flex: 1 }]}
              autoCapitalize="characters"
              onSubmitEditing={() => lookupShipment(manualCode)}
            />
            <TouchableOpacity
              onPress={() => lookupShipment(manualCode)}
              disabled={loading || !manualCode.trim()}
              style={[styles.primaryBtn, { backgroundColor: theme.colors.brand, opacity: loading || !manualCode.trim() ? 0.6 : 1 }]}
            >
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>{lookupLabel}</Text>}
            </TouchableOpacity>
          </View>
          {lookupError ? <Text testID="logistics-scan-error" style={{ color: theme.colors.danger, fontWeight: "600" }}>{lookupError}</Text> : null}
          {updateMessage ? <Text style={{ color: theme.colors.success, fontWeight: "600" }}>{updateMessage}</Text> : null}
        </View>

        {shipment ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
              <View style={{ flex: 1, gap: 4 }}>
                <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>{`${shipmentLabel} #${shipment.id}`}</Text>
                <Text style={s.textMuted}>{`${orderLabel} #${shipment.order_id}`}</Text>
              </View>
              <View style={[styles.chip, { backgroundColor: (STATUS_COLORS[shipment.status] || theme.colors.textMuted) + "22", borderColor: STATUS_COLORS[shipment.status] || theme.colors.border }]}> 
                <Text style={{ color: STATUS_COLORS[shipment.status] || theme.colors.text, fontWeight: "700", fontSize: 12, textTransform: "capitalize" }}>
                  {formatShipmentStatus(shipment)}
                </Text>
              </View>
            </View>

            <View style={{ gap: 4 }}>
              <Text style={s.textMuted}>{statusLabel}: {formatShipmentStatus(shipment)}</Text>
              {shipment.customer_name ? <Text style={s.textMuted}>{customerLabel}: {shipment.customer_name}</Text> : null}
              {shipment.customer_phone ? <Text style={s.textMuted}>{phoneLabel}: {shipment.customer_phone}</Text> : null}
              {shipment.shipping_address ? <Text style={s.textMuted}>{addressLabel}: {shipment.shipping_address}</Text> : null}
              {shipment.delivery_location ? <Text style={s.textMuted}>{locationLabel}: {shipment.delivery_location}</Text> : null}
              {shipment.carrier_name ? <Text style={s.textMuted}>{carrierLabel}: {shipment.carrier_name}</Text> : null}
              {shipment.tracking_number ? <Text style={s.textMuted}>{trackingLabel}: {shipment.tracking_number}</Text> : null}
              {shipment.scan_code ? <Text style={s.textMuted}>{scanCodeLabel}: {shipment.scan_code}</Text> : null}
              {shipment.package_count != null ? <Text style={s.textMuted}>{packagesLabel}: {shipment.package_count}</Text> : null}
              {shipment.package_weight_kg != null ? <Text style={s.textMuted}>{weightLabel}: {shipment.package_weight_kg} kg</Text> : null}
              {shipment.package_dimensions ? <Text style={s.textMuted}>{dimensionsLabel}: {shipment.package_dimensions}</Text> : null}
              {shipment.packaging_notes ? <Text style={s.textMuted}>{packagingNotesLabel}: {shipment.packaging_notes}</Text> : null}
              {shipment.estimated_delivery ? <Text style={s.textMuted}>{etaLabel}: {formatLocalizedDateTime(shipment.estimated_delivery, locale, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</Text> : null}
              {shipment.delivery_signature_captured_at ? (
                <Text style={s.textMuted}>{deliverySignatureCapturedLabel}: {formatLocalizedDateTime(shipment.delivery_signature_captured_at, locale, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</Text>
              ) : null}
            </View>

            <Text style={[s.text, { fontWeight: "700" }]}>{updateStatusLabel}</Text>
            {hasPendingConfirmation ? (
              <View style={[styles.noticeBox, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}> 
                <Text style={{ color: theme.colors.text, fontWeight: "700" }}>
                  {activeConfirmation?.confirmation_type_label || confirmationLabel} {requestPendingLabel}
                </Text>
                <Text style={s.textMuted}>
                  {waitingForLabel} {activeConfirmation?.target_role || recipientLabel} to approve before the shipment moves to {activeConfirmation?.requested_status?.replace(/_/g, " ")}.
                </Text>
                {activeConfirmation?.current_hub ? <Text style={s.textMuted}>{currentHubPlaceholderLabel.replace(" (optional)", "")}: {activeConfirmation.current_hub}</Text> : null}
                {activeConfirmation?.tracking_number ? <Text style={s.textMuted}>{trackingLabel}: {activeConfirmation.tracking_number}</Text> : null}
              </View>
            ) : null}
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={{ flexDirection: "row", gap: 6 }}>
                {availableActions.map((action) => (
                  <TouchableOpacity
                    testID={`logistics-scan-action-${action.status}-${action.eventType}`}
                    key={`${action.status}:${action.eventType}`}
                    onPress={() => {
                      setNewStatus(action.status);
                      setEventType(action.eventType);
                    }}
                    style={[
                      styles.chip,
                      {
                        backgroundColor: newStatus === action.status && eventType === action.eventType ? theme.colors.brand : theme.colors.surface2,
                        borderColor: newStatus === action.status && eventType === action.eventType ? theme.colors.brand : theme.colors.border,
                      },
                    ]}
                    disabled={hasPendingConfirmation}
                  >
                    <Text style={{ color: newStatus === action.status && eventType === action.eventType ? "#fff" : theme.colors.text, fontWeight: "700", fontSize: 12 }}>
                      {translatedAvailableActionLabels[availableActions.indexOf(action)] || action.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
            {!availableActions.length ? (
              <Text style={s.textMuted}>{noActionsAvailableLabel}</Text>
            ) : null}

            <View style={[styles.noticeBox, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}> 
              <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{selectedMilestoneLabel}</Text>
              <Text style={s.textMuted}>{selectedAction ? translatedAvailableActionLabels[availableActions.indexOf(selectedAction)] || selectedAction.label : eventType ? eventType.replace(/_/g, " ") : chooseActionLabel}</Text>
            </View>

            {selectedActionRequiresFailureReason ? (
              <View testID="logistics-scan-failure-helper" style={[styles.noticeBox, { backgroundColor: theme.colors.danger + "12", borderColor: theme.colors.danger }]}> 
                <Text style={{ color: theme.colors.danger, fontWeight: "700" }}>{failureDetailsLabel}</Text>
                <Text style={s.textMuted}>{failureReasonRequiredLabel}</Text>
              </View>
            ) : null}

            <TextInput
              value={currentHub}
              onChangeText={setCurrentHub}
              placeholder={currentHubPlaceholderLabel}
              placeholderTextColor={theme.colors.textMuted}
              style={s.input}
              editable={!hasPendingConfirmation}
            />
            <TextInput
              value={trackingNumber}
              onChangeText={setTrackingNumber}
              placeholder={trackingNumberPlaceholderLabel}
              placeholderTextColor={theme.colors.textMuted}
              style={s.input}
              editable={!hasPendingConfirmation}
            />
            <TextInput
              testID="logistics-scan-notes"
              value={notes}
              onChangeText={setNotes}
              placeholder={selectedActionRequiresFailureReason ? failureNotesPlaceholderLabel : notesPlaceholderLabel}
              placeholderTextColor={theme.colors.textMuted}
              style={s.input}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
              editable={!hasPendingConfirmation}
            />

            {newStatus === "delivered" ? (
              <View style={{ gap: 10 }}>
                <Text style={[s.text, { fontWeight: "700" }]}>{customerSignatureLabel}</Text>
                <TextInput
                  value={signatureName}
                  onChangeText={setSignatureName}
                  placeholder={customerFullNamePlaceholderLabel}
                  placeholderTextColor={theme.colors.textMuted}
                  style={s.input}
                  editable={!hasPendingConfirmation}
                />
                <SignaturePad
                  onChange={setSignatureDataUrl}
                  strokeColor={theme.colors.text}
                  backgroundColor={theme.colors.surface1}
                  borderColor={theme.colors.border}
                />
                <Text style={s.textMuted}>{signatureRequiredLabel}</Text>
              </View>
            ) : null}

            <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
              <TouchableOpacity
                testID="logistics-scan-update"
                onPress={updateShipment}
                disabled={updating || !availableActions.length || hasPendingConfirmation}
                style={[styles.primaryBtn, { backgroundColor: theme.colors.brand, opacity: updating || !availableActions.length || hasPendingConfirmation ? 0.6 : 1, flexGrow: 1 }]}
              >
                {updating ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>{actionButtonLabel}</Text>}
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => router.push(`/tracking/${shipment.order_id}` as never)}
                style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2, flexGrow: 1 }]}
              >
                <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{openTrackerLabel}</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    gap: 10,
  },
  modeBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
  },
  chip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  noticeBox: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 4,
  },
  primaryBtn: {
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryBtn: {
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryBtnText: {
    color: "#fff",
    fontWeight: "700",
  },
});