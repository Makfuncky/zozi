"use client";

import { Fragment } from "react";
import { toErrorMessage, toNumberOrNull, formatIso } from "../constants";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function VersionsTab({
  ...p
}: CountriesTabProps) {
  const { actOnVersion, activeVersionType, busyAction, filteredVersions, versions, setActiveVersionType } = p;

  return (
  <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-versions-panel">
    <h3 className="text-sm font-bold text-text">Version History & Draft Pipelines</h3>
    <p className="text-xs text-text-muted">GCC configs follow a draft-approve-publish workflow. Approved versions can be published instantly or rolled back to previous states.</p>

    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-semibold text-text-muted">Filter By Config:</span>
      {[
        { key: "all", label: "All Configs" },
        { key: "tax", label: "Tax" },
        { key: "logistics", label: "Internal Logistics" },
        { key: "logistics_providers", label: "Delivery Partners" },
        { key: "payment_gateways", label: "Payment Gateways" },
        { key: "legal_rules", label: "Legal Rules" },
        { key: "regions", label: "Regions" },
        { key: "supplier_requirements", label: "Supplier KYC" },
        { key: "payout_settings", label: "Payouts" },
        { key: "commission_tiers", label: "Value Commissions" },
        { key: "commission", label: "Category Commissions" },
      ].map((filter) => (
        <button
          key={filter.key}
          type="button"
          onClick={() => setActiveVersionType(filter.key)}
          className={`rounded-full border px-3 py-1 text-[11px] font-semibold transition ${
            activeVersionType === filter.key
              ? "border-primary bg-primary/10 text-primary"
              : "border-border bg-surface text-text-muted hover:text-text"
          }`}
        >
          {filter.label}
        </button>
      ))}
    </div>

    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="w-full min-w-[860px] border-collapse text-xs">
        <thead className="bg-surface-2 text-left text-text-muted">
          <tr>
            <th className="px-3 py-2 font-semibold">Config Type</th>
            <th className="px-3 py-2 font-semibold">Version Number</th>
            <th className="px-3 py-2 font-semibold">Current State</th>
            <th className="px-3 py-2 font-semibold">Created Date</th>
            <th className="px-3 py-2 font-semibold">Published Date</th>
            <th className="px-3 py-2 font-semibold w-[220px]">Workflow Action</th>
          </tr>
        </thead>
        <tbody>
          {filteredVersions.map((version) => (
            <tr key={version.id} className="border-t border-border/80 hover:bg-surface-2/40 transition" data-version-id={version.id}>
              <td className="px-3 py-2.5 font-bold uppercase tracking-wide text-text font-mono text-[10px]">
                {version.config_type.replace("_", " ")}
              </td>
              <td className="px-3 py-2.5 text-text font-semibold">v{version.version}</td>
              <td className="px-3 py-2.5">
                <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  version.status === "published"
                    ? "bg-success/15 text-success border border-success/30"
                    : version.status === "approved"
                    ? "bg-primary/15 text-primary border border-primary/30"
                    : version.status === "draft"
                    ? "bg-warning/15 text-warning border border-warning/30"
                    : "bg-text-faint/15 text-text-muted border"
                }`}>
                  {version.status.toUpperCase()}
                </span>
              </td>
              <td className="px-3 py-2.5 text-text-muted">{formatIso(version.created_at)}</td>
              <td className="px-3 py-2.5 text-text-muted">{formatIso(version.published_at)}</td>
              <td className="px-3 py-2.5">
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => actOnVersion(version, "approve")}
                    disabled={busyAction === `approve-${version.id}` || version.status !== "draft"}
                    className="inline-flex items-center gap-1 rounded bg-surface border border-border px-2 py-1 text-[10px] font-bold text-text hover:bg-surface-3 transition disabled:opacity-40"
                    data-testid={`approve-version-${version.id}`}
                  >
                    <Check className="h-3 w-3 text-success" />
                    Approve
                  </button>
                  <Button variant="primary" className="inline-flex items-center gap-1 rounded px-2 py-1 text-[10px] font-bold transition disabled:opacity-40" type="button"
                    onClick={() => actOnVersion(version, "publish")}
                    disabled={busyAction === `publish-${version.id}` || !["draft", "approved"].includes(version.status)}
                    data-testid={`publish-version-${version.id}`}
                  >
                    <UploadCloud className="h-3 w-3" />
                    Publish
                  </Button>
                  <Button variant="danger" className="inline-flex items-center gap-1 rounded bg-surface border border-border px-2 py-1 text-[10px] font-bold hover:bg-danger/10 hover:border-danger/20 transition disabled:opacity-40" type="button"
                    onClick={() => actOnVersion(version, "rollback")}
                    disabled={busyAction === `rollback-${version.id}` || version.status !== "published"}
                    data-testid={`rollback-version-${version.id}`}
                  >
                    <RefreshCw className="h-3 w-3" />
                    Rollback
                  </Button>
                </div>
              </td>
            </tr>
          ))}
          {filteredVersions.length === 0 ? (
            <tr>
              <td className="px-3 py-4 text-center text-text-muted" colSpan={6}>
                No version control ledgers recorded for this configuration filter.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  </section>
  );
}
