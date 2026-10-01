"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function PaymentGatewaysTab({
  ...p
}: CountriesTabProps) {
  const { busyAction, canSubmit, gateways, name, newGatewayCredRef, newGatewayFeeFixed, newGatewayFeePct, newGatewayId, newGatewayName, newGatewaySupportsCod, newGatewaySupportsInstall, newGatewayType, submitPaymentGatewaysDraft, setGateways, setNewGatewayCredRef, setNewGatewayFeeFixed, setNewGatewayFeePct, setNewGatewayId, setNewGatewayName, setNewGatewaySupportsCod, setNewGatewaySupportsInstall, setNewGatewayType } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Payment Gateways & Transaction Rules</h3>
      <p className="text-xs text-text-muted">Dynamic payment options configured in the checkout pipeline. Note that credential variables must match backend environment naming.</p>

      <div className="grid gap-2 grid-cols-2 md:grid-cols-3 lg:grid-cols-4 p-3 rounded-lg border border-border bg-surface">
        <label className="space-y-1 text-[10px] text-text-muted">
          Gateway ID
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayId} onChange={(e) => setNewGatewayId(e.target.value)} placeholder="mada" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Display Name
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayName} onChange={(e) => setNewGatewayName(e.target.value)} placeholder="Mada Credit/Debit" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Integration Type
          <select className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayType} onChange={(e) => setNewGatewayType(e.target.value)}>
            <option value="card">Card Payment</option>
            <option value="wallet">Digital Wallet</option>
            <option value="cod">Cash on Delivery (COD)</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Credential Env Reference Key
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayCredRef} onChange={(e) => setNewGatewayCredRef(e.target.value)} placeholder="MADA_API_KEY" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Fee Percentage
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayFeePct} onChange={(e) => setNewGatewayFeePct(e.target.value)} />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Fee Fixed Amount
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayFeeFixed} onChange={(e) => setNewGatewayFeeFixed(e.target.value)} />
        </label>
        <div className="flex items-center gap-4 col-span-2 pt-2">
          <label className="inline-flex items-center gap-1 text-[10px] font-semibold text-text cursor-pointer">
            <input type="checkbox" checked={newGatewaySupportsCod} onChange={(e) => setNewGatewaySupportsCod(e.target.checked)} />
            Supports Cash On Delivery (COD)
          </label>
          <label className="inline-flex items-center gap-1 text-[10px] font-semibold text-text cursor-pointer">
            <input type="checkbox" checked={newGatewaySupportsInstall} onChange={(e) => setNewGatewaySupportsInstall(e.target.checked)} />
            Supports Installments / BNPL
          </label>
        </div>
        <div className="flex items-end justify-end col-span-2 md:col-span-3 lg:col-span-4 mt-2">
          <button
            type="button"
            onClick={() => {
              const gid = newGatewayId.trim().toLowerCase();
              const gname = newGatewayName.trim();
              if (!gid || !gname) return;
              setGateways([
                ...gateways,
                {
                  gateway_id: gid,
                  name: gname,
                  type: newGatewayType,
                  enabled: true,
                  credential_ref: newGatewayCredRef.trim() || null,
                  supports_cod: newGatewaySupportsCod,
                  supports_installments: newGatewaySupportsInstall,
                  fee_percentage: Number(newGatewayFeePct) || 0,
                  fee_fixed: Number(newGatewayFeeFixed) || 0
                }
              ]);
              setNewGatewayId("");
              setNewGatewayName("");
              setNewGatewayCredRef("");
              setNewGatewaySupportsCod(false);
              setNewGatewaySupportsInstall(false);
            }}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-4 text-xs font-semibold text-text hover:bg-surface-3 transition"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Gateway Option
          </button>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 mt-2">
        {gateways.map((gw, index) => (
          <div key={index} className="rounded-xl border border-border bg-surface p-3 space-y-2 relative shadow-sm hover:shadow transition">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold text-text block text-sm">{gw.name}</span>
                <span className="text-[10px] font-mono text-text-faint uppercase">{gw.gateway_id} | {gw.type}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-muted cursor-pointer">
                  <input
                    type="checkbox"
                    checked={gw.enabled}
                    onChange={(e) => {
                      const updated = [...gateways];
                      updated[index].enabled = e.target.checked;
                      setGateways(updated);
                    }}
                  />
                  Active
                </label>
                <Button variant="danger" className="p-1.5 rounded transition" type="button"
                  onClick={() => setGateways(gateways.filter((_, i) => i !== index))}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs border-t border-border/60 pt-2">
              <div><span className="text-text-muted font-semibold">Cred Variable:</span> <span className="font-mono text-[10px] bg-surface-2 px-1 rounded">{gw.credential_ref || "None Required"}</span></div>
              <div><span className="text-text-muted font-semibold">Tx Cost:</span> {gw.fee_percentage}% + {gw.fee_fixed}</div>
              <div><span className="text-text-muted font-semibold">Allow COD:</span> {gw.supports_cod ? "Yes" : "No"}</div>
              <div><span className="text-text-muted font-semibold">Allow Installment:</span> {gw.supports_installments ? "Yes" : "No"}</div>
            </div>
          </div>
        ))}
        {gateways.length === 0 && (
          <div className="col-span-2 text-center py-6 text-text-faint italic border rounded-xl bg-surface">No gateways configured. Customers will only be able to use standard Cash on Delivery if active.</div>
        )}
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitPaymentGatewaysDraft}
          disabled={!canSubmit || busyAction === "payment_gateways"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "payment_gateways" ? "Creating draft..." : "Save Payment Gateways Draft"}
        </Button>
      </div>
    </section>
  );
}
