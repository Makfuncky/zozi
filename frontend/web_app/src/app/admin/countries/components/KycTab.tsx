"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function KycTab({
  ...p
}: CountriesTabProps) {
  const { approvalRequired, busyAction, canSubmit, country, kycLevel, requiredDocuments, submitSupplierRequirementsDraft, setApprovalRequired, setKycLevel, setRequiredDocuments } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Supplier Onboarding & Compliance</h3>
      <p className="text-xs text-text-muted">Define the level of validation and documentary evidence required from suppliers requesting to sell in this country.</p>

      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
        <label className="space-y-1 text-xs text-text-muted">
          KYC Clearance Level
          <select className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={kycLevel} onChange={(e) => setKycLevel(e.target.value)}>
            <option value="basic">Basic (Self-verification)</option>
            <option value="standard">Standard (Business ID & Bank verification)</option>
            <option value="enhanced">Enhanced (Fully-audited KYC and corporate verification)</option>
          </select>
        </label>
        <div className="flex items-end pb-2">
          <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
            <input type="checkbox" checked={approvalRequired} onChange={(e) => setApprovalRequired(e.target.checked)} />
            Require manual ops approval before listing products
          </label>
        </div>
      </div>

      <div className="space-y-2 border-t border-border pt-4">
        <span className="block text-xs font-bold text-text-muted">Required Documents Checklist</span>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { id: "commercial_license", label: "Commercial Registration (CR)" },
            { id: "vat_certificate", label: "VAT Certificate" },
            { id: "owner_id", label: "Authorized Signatory ID" },
            { id: "bank_statement", label: "Bank Account Ownership (IBAN)" },
            { id: "brand_auth", label: "Brand Authorization / Dealer Certificate" },
            { id: "import_permit", label: "Import Permit / Customs Registration" },
            { id: "saudi_fda", label: "SFDA / Local FDA License Certificate" }
          ].map((doc) => {
            const isChecked = requiredDocuments.includes(doc.id);
            return (
              <label key={doc.id} className="flex items-center gap-2 border border-border/80 bg-surface rounded-lg p-2.5 text-xs text-text cursor-pointer hover:bg-surface-2 transition select-none">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setRequiredDocuments([...requiredDocuments, doc.id]);
                    } else {
                      setRequiredDocuments(requiredDocuments.filter((d) => d !== doc.id));
                    }
                  }}
                />
                <span>{doc.label}</span>
              </label>
            );
          })}
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitSupplierRequirementsDraft}
          disabled={!canSubmit || busyAction === "supplier_requirements"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "supplier_requirements" ? "Creating draft..." : "Save Supplier Rules Draft"}
        </Button>
      </div>
    </section>
  );
}
