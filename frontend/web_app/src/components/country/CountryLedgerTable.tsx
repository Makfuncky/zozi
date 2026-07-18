"use client";

import { Fragment, useState, useCallback } from "react";
import { ChevronRight, ChevronDown, Globe, Plus, Save, X, RefreshCw } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import GhostRowForm from "./GhostRowForm";

export interface CountrySummary {
  code: string;
  name: string;
  currency: string;
  tax_rate: number;
  tax_name: string;
  is_active: boolean;
  city_count: number;
  commission_count: number;
}

interface CountryLedgerTableProps {
  countries: CountrySummary[];
  expandedCode: string | null;
  onToggleExpand: (code: string) => void;
  onRefresh: () => void;
  loading: boolean;
  children?: React.ReactNode;
}

export default function CountryLedgerTable({
  countries,
  expandedCode,
  onToggleExpand,
  onRefresh,
  loading,
  children,
}: CountryLedgerTableProps) {
  if (loading) {
    return <div className="text-center py-8 text-sm text-text-muted">Loading countries...</div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-bold text-text">Countries Ledger</h2>
          <span className="text-xs text-text-muted bg-surface-2 px-2 py-0.5 rounded-full">
            {countries.length} countries
          </span>
        </div>
      </div>

      {/* Ghost Row Form */}
      <GhostRowForm onCountryCreated={onRefresh} />

      {/* Column Headers */}
      <div className="hidden md:grid md:grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_1fr_40px] gap-3 px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-muted bg-surface-2 rounded-t-lg border border-border">
        <span>Country</span>
        <span>Code</span>
        <span>Currency</span>
        <span>Tax Rate</span>
        <span>Cities</span>
        <span>Commissions</span>
        <span>Status</span>
        <span></span>
      </div>

      {/* Rows */}
      <div className="border border-t-0 border-border rounded-b-lg divide-y divide-border/60">
        {countries.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-text-muted">
            No countries configured yet.
          </div>
        )}
        {countries.map((country) => {
          const isExpanded = expandedCode === country.code;
          return (
            <Fragment key={country.code}>
              {/* Main Row */}
              <div
                data-testid={`country-ledger-row-${country.code}`}
                className="grid grid-cols-1 md:grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_1fr_40px] gap-3 px-4 py-3 items-center text-xs hover:bg-surface-1/60 cursor-pointer transition"
                onClick={() => onToggleExpand(country.code)}
              >
                <div className="flex items-center gap-2 font-medium text-text">
                  {isExpanded ? (
                    <ChevronDown className="h-3.5 w-3.5 text-text-muted shrink-0" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 text-text-muted shrink-0" />
                  )}
                  <span className="truncate">{country.name}</span>
                </div>
                <span className="hidden md:inline text-text-muted font-mono">{country.code}</span>
                <span className="hidden md:inline text-text-muted">{country.currency}</span>
                <span className="hidden md:inline text-text-muted">{country.tax_rate}%</span>
                <span className="hidden md:inline text-text-muted">{country.city_count}</span>
                <span className="hidden md:inline text-text-muted">{country.commission_count}</span>
                <span className="hidden md:inline">
                  <span
                    className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                      country.is_active
                        ? "bg-success/10 text-success"
                        : "bg-danger/10 text-danger"
                    }`}
                  >
                    {country.is_active ? "Active" : "Inactive"}
                  </span>
                </span>
                <span className="hidden md:inline text-text-faint">
                  {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                </span>

                {/* Mobile summary */}
                <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-text-faint md:hidden">
                  <span>{country.code}</span>
                  <span>{country.currency}</span>
                  <span>{country.tax_rate}% tax</span>
                  <span>{country.city_count} cities</span>
                  <span
                    className={`font-semibold ${country.is_active ? "text-success" : "text-danger"}`}
                  >
                    {country.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
              </div>

              {/* Expanded Detail Panel */}
              {isExpanded && (
                <div className="border-t border-border/40 bg-surface-1/30">
                  <div className="p-4">{children}</div>
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}


