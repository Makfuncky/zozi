"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Camera, ScanLine, Keyboard, RefreshCw, CheckCircle,
  XCircle, Package, Truck, MapPin, AlertCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import BrandLoading from "@/components/BrandLoading";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";

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

const STATUS_CHIP: Record<string, string> = {
  pending: "theme-chip-warning",
  picked: "theme-chip-info",
  in_transit: "theme-chip-brand",
  delivered: "theme-chip-success",
  returned: "theme-chip-danger",
  failed: "theme-chip-danger",
};

export default function BarcodeScannerPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const scanIntervalRef = useRef<number | null>(null);
  // Holds ZXing reader instance when loaded dynamically
  const zxingReaderRef = useRef<any>(null);

  const [mode, setMode] = useState<"camera" | "manual">("manual");
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [scanning, setScanning] = useState(false);

  const [shipment, setShipment] = useState<ShipmentInfo | null>(null);
  const [lookupError, setLookupError] = useState("");
  const [scannedCode, setScannedCode] = useState("");
  const [newStatus, setNewStatus] = useState("");
  const [eventNote, setEventNote] = useState("");
  const [updating, setUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  const stopCamera = useCallback(() => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    // Stop ZXing continuous decode if active
    if (zxingReaderRef.current) {
      try { zxingReaderRef.current.reset(); } catch {}
      zxingReaderRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  }, []);

  // Cleanup camera on unmount
  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const startCamera = async () => {
    setCameraError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);

      if ("BarcodeDetector" in window) {
        // -- Native BarcodeDetector (Chrome/Edge/Android) ------------------
        const detector = new (window as any).BarcodeDetector({
          formats: ["qr_code", "code_128", "ean_13", "ean_8", "code_39", "upc_a", "upc_e"],
        });
        scanIntervalRef.current = window.setInterval(async () => {
          if (!videoRef.current || videoRef.current.readyState < 2) return;
          try {
            const barcodes = await detector.detect(videoRef.current);
            if (barcodes.length > 0) {
              const code = barcodes[0].rawValue as string;
              stopCamera();
              await lookupShipment(code);
            }
          } catch {}
        }, 500);
      } else {
        // -- ZXing fallback (Firefox, Safari, desktop Chrome without flag) --
        try {
          const { BrowserMultiFormatReader } = await import("@zxing/library");
          const reader = new BrowserMultiFormatReader();
          zxingReaderRef.current = reader;

          // ZXing decodes frames directly from the video element continuously
          (reader as any).decodeFromVideoElement(videoRef.current!, (result: any, _err: unknown) => {
            if (result) {
              const code = result.getText();
              stopCamera();
              lookupShipment(code);
            }
            // err is a NotFoundException on every frame without a barcode ? safe to ignore
          });
        } catch {
          setCameraError(
            "Barcode detection is not supported in this browser. Please enter the code manually."
          );
        }
      }
    } catch (err: any) {
      setCameraError(err?.message || "Camera access denied or not available");
    }
  };

  const lookupShipment = async (code: string) => {
    if (!code.trim()) return;
    setScanning(true);
    setLookupError("");
    setShipment(null);
    setUpdateSuccess(false);
    const trimmed = code.trim();
    setScannedCode(trimmed);

    try {
      // Try tracking number match first, then shipment ID
      let res = await apiFetch(`/logistics/shipments/scan?code=${encodeURIComponent(trimmed)}`);
      if (!res.ok && !isNaN(Number(trimmed))) {
        res = await apiFetch(`/logistics/shipments/${trimmed}`);
      }
      if (res.ok) {
        const data = await res.json();
        setShipment(data);
        setNewStatus(data.status);
      } else {
        setLookupError(`No shipment found for code "${trimmed}"`);
      }
    } catch { setLookupError("Network error looking up shipment"); }
    setScanning(false);
  };

  const handleManualLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    await lookupShipment(manualCode);
  };

  const handleUpdateStatus = async () => {
    if (!shipment) return;
    setUpdating(true);
    setUpdateSuccess(false);
    try {
      const res = await apiFetch(`/logistics/shipments/${shipment.id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: newStatus,
          note: eventNote || `Scanned: ${scannedCode}`,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setShipment((prev) => prev ? { ...prev, ...updated } : updated);
        setUpdateSuccess(true);
        setEventNote("");
      }
    } catch {}
    setUpdating(false);
  };

  if (isLoading) {
    return (
      <AdminLayout title="Barcode / QR" headerMode="compact">
        <PanelLoadingState />
      </AdminLayout>
    );
  }

  if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
    router.push("/admin/login");
    return null;
  }

  return (
    <Suspense fallback={<BrandLoading fullscreen label="Loading barcode scanner..." className="p-8" />}>
      <AdminLayout title="Barcode / QR">
        <PanelContent width="medium" className="py-3 sm:py-4">


        {/* Mode toggle */}
        <div className="theme-card flex w-full gap-1 overflow-x-auto rounded-xl border p-1 sm:w-fit">
          <button onClick={() => { setMode("camera"); stopCamera(); }}
            className={`flex flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition-colors sm:flex-none ${mode === "camera" ? "theme-btn-primary" : "text-text-muted hover:text-text"}`}>
            <Camera className="w-4 h-4" /> Camera
          </button>
          <button onClick={() => { setMode("manual"); stopCamera(); }}
            className={`flex flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition-colors sm:flex-none ${mode === "manual" ? "theme-btn-primary" : "text-text-muted hover:text-text"}`}>
            <Keyboard className="w-4 h-4" /> Manual
          </button>
        </div>

        {/* Camera mode */}
        {mode === "camera" && (
          <div className="theme-card rounded-xl border p-4 space-y-4">
            <div className="relative rounded-xl overflow-hidden bg-black aspect-video max-h-72">
              <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
              {!cameraActive && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Camera className="w-12 h-12 text-white/30" />
                </div>
              )}
              {cameraActive && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-48 h-28 border-2 border-primary rounded-xl opacity-80 animate-pulse" />
                </div>
              )}
            </div>
            <canvas ref={canvasRef} className="hidden" />

            {cameraError && (
              <div className="flex items-center gap-2 text-xs text-warning">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {cameraError}
              </div>
            )}

            <div className="flex flex-col gap-3 sm:flex-row">
              {!cameraActive ? (
                <button onClick={startCamera}
                  className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-xs font-semibold sm:w-auto">
                  <Camera className="w-4 h-4" /> Start Camera
                </button>
              ) : (
                <button onClick={stopCamera}
                  className="theme-btn-secondary w-full rounded-xl px-5 py-2.5 text-xs font-semibold sm:w-auto">
                  Stop Camera
                </button>
              )}
            </div>

            {/* Manual code entry as fallback even in camera mode */}
            <form onSubmit={handleManualLookup} className="mt-2 flex flex-col gap-2 sm:flex-row">
              <input
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                placeholder="Or type / paste code here"
                className="theme-input flex-1 rounded-xl border px-3 py-2 text-xs"
              />
              <button type="submit" disabled={scanning || !manualCode}
                className="theme-btn-accent flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold disabled:opacity-50 sm:w-auto">
                {scanning ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Lookup"}
              </button>
            </form>
          </div>
        )}

        {/* Manual mode */}
        {mode === "manual" && (
          <div className="theme-card rounded-xl border p-4">
            <h2 className="text-xs font-bold text-text mb-3">Enter Barcode / Tracking Number</h2>
            <form onSubmit={handleManualLookup} className="flex flex-col gap-3 sm:flex-row">
              <input
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                placeholder="e.g. TRK-0000123 or scan code"
                className="theme-input flex-1 rounded-xl border px-3 py-2.5 text-xs"
                autoFocus
              />
              <button type="submit" disabled={scanning || !manualCode}
                className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-xs font-semibold disabled:opacity-50 sm:w-auto">
                {scanning ? <><RefreshCw className="w-4 h-4 animate-spin" />Scanning?</> : <><ScanLine className="w-4 h-4" />Lookup</>}
              </button>
            </form>
          </div>
        )}

        {/* Lookup error */}
        {lookupError && (
          <div className="theme-alert-danger flex items-center gap-2 rounded-xl p-4 text-xs">
            <XCircle className="w-4 h-4 shrink-0" />
            {lookupError}
          </div>
        )}

        {/* Shipment result */}
        {shipment && (
          <div className="theme-card rounded-xl border p-4 space-y-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Package className="w-5 h-5 theme-status-info" />
                  <h2 className="text-base font-bold text-text">Shipment #{shipment.id}</h2>
                  <span className={`px-2 py-0.5 rounded-lg text-xs font-semibold ${STATUS_CHIP[shipment.status] ?? "theme-chip-muted"}`}>
                    {shipment.status.replace(/_/g, " ")}
                  </span>
                </div>
                <p className="text-xs text-text-muted">Order #{shipment.order_id}</p>
              </div>
              {updateSuccess && (
                <div className="flex items-center gap-1.5 text-success text-xs font-semibold">
                  <CheckCircle className="w-4 h-4" />Updated
                </div>
              )}
            </div>

            {/* Shipment details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {[
                { label: "Carrier", value: shipment.carrier_name },
                { label: "Tracking #", value: shipment.tracking_number },
                { label: "Channel", value: shipment.distribution_channel?.replace(/_/g, " ") },
                { label: "Current Hub", value: shipment.current_hub },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-xl bg-surface-2 px-4 py-3">
                  <p className="text-xs text-text-muted">{label}</p>
                  <p className="text-xs font-semibold text-text mt-0.5">{value || "?"}</p>
                </div>
              ))}
            </div>

            {shipment.shipping_address && (
              <div className="flex items-start gap-2 rounded-xl bg-surface-2 px-4 py-3 text-xs">
                <MapPin className="w-4 h-4 text-text-muted shrink-0 mt-0.5" />
                <p className="text-text">{shipment.shipping_address}</p>
              </div>
            )}

            {/* Update status */}
            <div className="border-t border-border pt-4 space-y-3">
              <h3 className="text-xs font-bold text-text flex items-center gap-2">
                <Truck className="w-4 h-4" />Update Status
              </h3>
              <div className="flex flex-wrap gap-2">
                {["pending", "picked", "in_transit", "delivered", "returned", "failed"].map((s) => (
                  <button key={s} onClick={() => setNewStatus(s)}
                    className={`rounded-xl px-3 py-1.5 text-xs font-semibold border transition-colors ${
                      newStatus === s ? STATUS_CHIP[s] ?? "theme-chip-info" : "border-border text-text-muted hover:text-text"
                    }`}>
                    {s.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
              <input
                value={eventNote}
                onChange={(e) => setEventNote(e.target.value)}
                placeholder="Event note (optional, e.g. Scanned at Dubai Hub)"
                className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
              />
              <button
                onClick={handleUpdateStatus}
                disabled={updating || newStatus === shipment.status}
                className="theme-btn-primary rounded-xl px-5 py-2.5 text-xs font-semibold disabled:opacity-50 flex items-center gap-2"
              >
                {updating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                Confirm Update
              </button>
            </div>
          </div>
        )}
        </PanelContent>
    </AdminLayout>
  </Suspense>
  );
}


