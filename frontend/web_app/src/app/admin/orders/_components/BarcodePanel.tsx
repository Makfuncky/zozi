"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, ScanLine } from "@/lib/icons";
import { PanelContent } from "@/components/PanelPage";

export default function BarcodePanel() {
  const router = useRouter();
  return (
    <div className="rounded-xl border border-border bg-surface-1 p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <ScanLine className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-text">Shipment Barcode & QR Scanner</h2>
          <p className="text-xs text-text-muted">
            Scan a parcel QR or tracking number to look up a shipment and correct its status, request
            confirmations, or record hub checkpoints.
          </p>
        </div>
      </div>
      <button
        onClick={() => router.push("/admin/barcode")}
        className="theme-btn-primary mt-4 inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
      >
        Open Scanner <ArrowRight className="h-4 w-4" />
      </button>
    </div>
  );
}
