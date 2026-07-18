"use client";

import { Button } from "@/components/ui/Button";

import { Fragment, useState, useRef, useEffect, useCallback } from "react";
import {
  ChevronRight,
  ChevronDown,
  Globe,
  Plus,
  Save,
  X,
  RefreshCw,
  Search,
  ExternalLink,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Zap,
  TrendingUp,
  Database,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

export interface CountrySummary {
  code: string;
  name: string;
  currency: string;
  currency_symbol?: string | null;
  tax_rate: number;
  tax_name: string;
  is_active: boolean;
  city_count: number;
  commission_count: number;
  flag_url?: string | null;
  region?: string | null;
  economic_tier?: string | null;
  population?: number | null;
  internet_penetration_pct?: number | null;
}

export interface AutoPopulateResult {
  code?: string;
  name?: string;
  official_name?: string;
  alpha3?: string;
  currency?: string;
  currency_symbol?: string;
  currency_name?: string;
  phone_code?: string;
  language?: string;
  timezone?: string;
  flag_url?: string;
  capital?: string;
  region?: string;
  population?: number;
  gdp_per_capita_usd?: number;
  internet_penetration_pct?: number;
  economic_tier?: string;
  default_tax_rate?: number;
  suggested_tax_rate?: number;
  suggested_tax_name?: string;
  suggested_tax_type?: string;
  tax_type?: string;
  tax_name?: string;
  suggested_gateways?: Array<{ gateway_id: string; score: number; reason: string; avg_fee?: string }>;
  suggested_commissions?: Record<string, { min: number; max: number; suggested: number }>;
  suggested_cities?: Array<{ name: string; population?: number; is_capital?: boolean }>;
  suggested_cities_list?: string[];
  supplier_kyc_tier?: string;
  supplier_requirements?: Array<{ document: string; required: boolean }>;
  logistics_model?: string;
  cod_enabled?: boolean;
  cod_max_amount?: number;
  settlement_hold_days?: number;
  consumer_protection_days?: number;
  fraud_risk_tier?: string;
  working_days?: string[];
  restricted_categories?: string[];
  data_privacy_framework?: string;
  cached?: boolean;
  degraded?: boolean;
  degraded_sources?: string[];
}

interface Props {
  countries: CountrySummary[];
  expandedCode: string | null;
  onToggleExpand: (code: string) => void;
  onRefresh: () => void;
  loading: boolean;
  children?: React.ReactNode;
  onAutoPopulateResult?: (result: AutoPopulateResult) => void;
}

const SOURCE_BADGES: Record<string, { label: string; color: string }> = {
  restcountries: { label: "RestCountries API", color: "bg-info/10 text-info border-info/20" },
  worldbank: { label: "World Bank", color: "bg-success/10 text-success border-success/20" },
  geodb: { label: "GeoDB Cities", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  algorithm: { label: "Algorithmic", color: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  curated: { label: "Curated Data", color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" },
};

function SourceBadge({ source }: { source: string }) {
  const badge = SOURCE_BADGES[source] ?? { label: source, color: "bg-surface-3 text-text-muted border-border" };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium border ${badge.color}`}>
      {badge.label}
    </span>
  );
}

function EconomicTierBadge({ tier }: { tier?: string | null }) {
  if (!tier) return null;
  const colors: Record<string, string> = {
    developed: "bg-success/10 text-success border-success/20",
    developing: "bg-info/10 text-info border-info/20",
    emerging: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${colors[tier] ?? "bg-surface-3 text-text-muted border-border"}`}>
      {tier.charAt(0).toUpperCase() + tier.slice(1)}
    </span>
  );
}

export default function CountryLedgerTable({
  countries,
  expandedCode,
  onToggleExpand,
  onRefresh,
  loading,
  children,
  onAutoPopulateResult,
}: Props) {
  const addToast = useToastStore((state) => state.addToast);

  // Ghost row state
  const [showGhostRow, setShowGhostRow] = useState(false);
  const [ghostSearch, setGhostSearch] = useState("");
  const [searchingCountry, setSearchingCountry] = useState(false);
  const [autoPopulateResult, setAutoPopulateResult] = useState<AutoPopulateResult | null>(null);
  const [creatingGhost, setCreatingGhost] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Focus ghost search when opened
  useEffect(() => {
    if (showGhostRow) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [showGhostRow]);

  // Debounced auto-populate search
  const handleGhostSearch = useCallback((val: string) => {
    setGhostSearch(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!val.trim() || val.trim().length < 2) {
      setAutoPopulateResult(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort();
      abortRef.current = new AbortController();
      setSearchingCountry(true);
      try {
        const res = await apiFetch(
          `/admin/countries/auto-populate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ search_term: val.trim() }),
            signal: abortRef.current.signal,
          }
        );
        if (res.ok) {
          const data = await res.json();
          setAutoPopulateResult(data);
          onAutoPopulateResult?.(data);
        }
      } catch (err: any) {
        if (err?.name !== "AbortError") {
          console.warn("Auto-populate error:", err);
        }
      } finally {
        setSearchingCountry(false);
      }
    }, 600);
  }, [onAutoPopulateResult]);

  const handleGhostCreate = async () => {
    if (!autoPopulateResult?.code) {
      addToast("Please search for a country first", "error");
      return;
    }
    setCreatingGhost(true);
    try {
      const payload = {
        code: autoPopulateResult.code,
        name: autoPopulateResult.name ?? ghostSearch,
        currency: autoPopulateResult.currency ?? "USD",
        timezone: autoPopulateResult.timezone ?? "UTC",
        official_name: autoPopulateResult.official_name,
        alpha3: autoPopulateResult.alpha3,
        flag_url: autoPopulateResult.flag_url,
        currency_name: autoPopulateResult.currency_name,
        currency_symbol: autoPopulateResult.currency_symbol,
        phone_code: autoPopulateResult.phone_code,
        language: autoPopulateResult.language,
        capital: autoPopulateResult.capital,
        region: autoPopulateResult.region,
        population: autoPopulateResult.population,
        gdp_per_capita_usd: autoPopulateResult.gdp_per_capita_usd,
        internet_penetration_pct: autoPopulateResult.internet_penetration_pct,
        economic_tier: autoPopulateResult.economic_tier,
        tax_type: autoPopulateResult.tax_type ?? autoPopulateResult.suggested_tax_type ?? "VAT",
        tax_rate: autoPopulateResult.default_tax_rate ?? autoPopulateResult.suggested_tax_rate,
        tax_name: autoPopulateResult.tax_name ?? autoPopulateResult.suggested_tax_name ?? "VAT",
        cities: autoPopulateResult.suggested_cities,
        suggested_gateways: autoPopulateResult.suggested_gateways,
        supplier_kyc_tier: autoPopulateResult.supplier_kyc_tier,
        logistics_model: autoPopulateResult.logistics_model,
        cod_enabled: autoPopulateResult.cod_enabled,
        cod_max_amount: autoPopulateResult.cod_max_amount,
        settlement_hold_days: autoPopulateResult.settlement_hold_days,
        consumer_protection_days: autoPopulateResult.consumer_protection_days,
        fraud_risk_tier: autoPopulateResult.fraud_risk_tier,
        data_privacy_framework: autoPopulateResult.data_privacy_framework,
        restricted_categories: autoPopulateResult.restricted_categories,
        working_days: autoPopulateResult.working_days,
        is_active: false, // draft by default
      };

      const res = await apiFetch("/admin/countries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        addToast(`🌍 ${payload.name} added to the ledger (Draft)`, "success");
        setShowGhostRow(false);
        setGhostSearch("");
        setAutoPopulateResult(null);
        onRefresh();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to add country", "error");
      }
    } catch {
      addToast("Network error creating country", "error");
    } finally {
      setCreatingGhost(false);
    }
  };

  const closeGhostRow = () => {
    setShowGhostRow(false);
    setGhostSearch("");
    setAutoPopulateResult(null);
  };

  return (
    <div className="space-y-1">
      {/* Header toolbar */}
      <div className="flex items-center justify-between px-1 pb-2">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold text-text">Country Control Plane</span>
          <span className="ml-1 rounded-full bg-surface-3 px-2 py-0.5 text-[10px] font-semibold text-text-muted">
            {countries.length} countries
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="rounded-lg border border-border bg-surface-2 p-1.5 text-text-muted hover:text-text transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-semibold shadow-sm transition-colors disabled:opacity-50" onClick={() => setShowGhostRow(true)}
            disabled={showGhostRow}
          >
            <Plus className="h-3.5 w-3.5" />
            Add Country
          </Button>
        </div>
      </div>

      {/* Ghost Row — Inline Add */}
      {showGhostRow && (
        <div className="mb-2 rounded-xl border-2 border-dashed border-primary/40 bg-primary/5 overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-primary/20">
            <Search className="h-4 w-4 text-primary shrink-0" />
            <input
              ref={searchInputRef}
              type="text"
              value={ghostSearch}
              onChange={(e) => handleGhostSearch(e.target.value)}
              placeholder="Type country name (e.g. Saudi Arabia, Pakistan)…"
              className="flex-1 bg-transparent text-sm text-text placeholder:text-text-faint outline-none"
            />
            {searchingCountry && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
            {autoPopulateResult && !searchingCountry && (
              <CheckCircle2 className="h-4 w-4 text-success" />
            )}
            <button onClick={closeGhostRow} className="text-text-muted hover:text-text">
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Auto-populated data preview */}
          {autoPopulateResult && (
            <div className="px-4 py-3 space-y-3">
              {autoPopulateResult.degraded && (
                <div className="flex items-center gap-2 rounded-lg bg-warning/10 border border-warning/20 px-3 py-2">
                  <AlertCircle className="h-3.5 w-3.5 text-warning shrink-0" />
                  <span className="text-[11px] text-warning">
                    Partial data — {autoPopulateResult.degraded_sources?.join(", ")} unavailable
                  </span>
                </div>
              )}

              {/* Country identity row */}
              <div className="flex items-center gap-3">
                {autoPopulateResult.flag_url && (
                  <img
                    src={autoPopulateResult.flag_url}
                    alt={autoPopulateResult.code}
                    className="h-6 w-9 object-cover rounded shadow-sm"
                  />
                )}
                <div>
                  <p className="font-bold text-text text-sm">{autoPopulateResult.name}</p>
                  {autoPopulateResult.official_name && (
                    <p className="text-[10px] text-text-muted">{autoPopulateResult.official_name}</p>
                  )}
                </div>
                <div className="ml-auto flex items-center gap-2">
                  <span className="rounded bg-surface-3 px-2 py-0.5 text-[11px] font-mono text-text-muted border border-border">
                    {autoPopulateResult.code}
                  </span>
                  <EconomicTierBadge tier={autoPopulateResult.economic_tier} />
                </div>
              </div>

              {/* Key data grid */}
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
                {[
                  { label: "Currency", value: `${autoPopulateResult.currency_symbol ?? ""} ${autoPopulateResult.currency}`, source: "restcountries" },
                  { label: "Tax", value: autoPopulateResult.default_tax_rate != null ? `${(autoPopulateResult.default_tax_rate * 100).toFixed(1)}% ${autoPopulateResult.tax_name ?? ""}` : autoPopulateResult.suggested_tax_rate != null ? `${(autoPopulateResult.suggested_tax_rate * 100).toFixed(1)}%` : "—", source: "curated" },
                  { label: "KYC Tier", value: autoPopulateResult.supplier_kyc_tier ?? "—", source: "algorithm" },
                  { label: "Logistics", value: autoPopulateResult.logistics_model?.replace("_", " ") ?? "—", source: "algorithm" },
                  { label: "Cities", value: String(autoPopulateResult.suggested_cities?.length ?? 0), source: "geodb" },
                  { label: "Fraud Risk", value: autoPopulateResult.fraud_risk_tier ?? "—", source: "algorithm" },
                ].map(({ label, value, source }) => (
                  <div key={label} className="rounded-lg bg-surface-2 border border-border p-2">
                    <p className="text-[9px] text-text-faint uppercase tracking-wide">{label}</p>
                    <p className="text-[11px] font-semibold text-text mt-0.5 truncate">{value}</p>
                    <SourceBadge source={source} />
                  </div>
                ))}
              </div>

              {/* Suggested gateways */}
              {(autoPopulateResult.suggested_gateways?.length ?? 0) > 0 && (
                <div>
                  <p className="text-[10px] text-text-faint uppercase tracking-wide mb-1.5 flex items-center gap-1">
                    <Zap className="h-3 w-3" /> Suggested Gateways
                    <SourceBadge source="algorithm" />
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {autoPopulateResult.suggested_gateways!.slice(0, 5).map((gw) => (
                      <div key={gw.gateway_id} className="flex items-center gap-1 rounded-lg border border-border bg-surface-2 px-2 py-1">
                        <span className="text-[10px] font-semibold text-text capitalize">{gw.gateway_id}</span>
                        <span className="text-[9px] text-success font-mono">{gw.score}/100</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cities preview */}
              {(autoPopulateResult.suggested_cities?.length ?? 0) > 0 && (
                <div>
                  <p className="text-[10px] text-text-faint uppercase tracking-wide mb-1.5 flex items-center gap-1">
                    <Database className="h-3 w-3" /> Top Cities
                    <SourceBadge source="geodb" />
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {autoPopulateResult.suggested_cities!.slice(0, 8).map((city) => (
                      <span key={typeof city === "string" ? city : city.name} className="rounded bg-surface-3 border border-border px-2 py-0.5 text-[10px] text-text-muted">
                        {typeof city === "string" ? city : city.name}
                        {typeof city === "object" && city.is_capital && " 🏛️"}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center justify-end gap-2 pt-1">
                <span className="mr-auto text-[10px] text-text-faint italic">
                  Will be saved as Draft — review before publishing
                </span>
                <button onClick={closeGhostRow} className="rounded-lg border border-border px-3 py-1.5 text-[11px] font-medium text-text-muted hover:text-text transition-colors">
                  Cancel
                </button>
                <Button variant="primary" onClick={handleGhostCreate}
                  disabled={creatingGhost || !autoPopulateResult?.code}>
                  {creatingGhost ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                  Save to Ledger
                </Button>
              </div>
            </div>
          )}

          {/* Placeholder when no result yet */}
          {!autoPopulateResult && !searchingCountry && (
            <div className="px-4 py-6 text-center text-[12px] text-text-faint">
              <Globe className="h-6 w-6 mx-auto mb-2 text-text-faint/50" />
              Type a country name above — we'll auto-fill currency, tax, cities, gateways, and more
            </div>
          )}
          {searchingCountry && (
            <div className="px-4 py-6 text-center">
              <Loader2 className="h-5 w-5 mx-auto animate-spin text-primary mb-2" />
              <p className="text-[11px] text-text-muted">Fetching country data…</p>
              <p className="text-[10px] text-text-faint mt-1">RestCountries · World Bank · GeoDB · Heuristic Engine</p>
            </div>
          )}
        </div>
      )}

      {/* Country ledger rows */}
      <div className="rounded-xl border border-border overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[2fr_1fr_1fr_auto_auto_auto] gap-2 px-4 py-2 bg-surface-2 border-b border-border text-[10px] font-semibold text-text-muted uppercase tracking-wider">
          <span>Country</span>
          <span>Currency</span>
          <span>Tax</span>
          <span className="text-center">Cities</span>
          <span className="text-center">Status</span>
          <span></span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
        ) : countries.length === 0 ? (
          <div className="py-12 text-center">
            <Globe className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
            <p className="text-sm text-text-muted">No countries configured</p>
            <p className="text-xs text-text-faint mt-1">Click "Add Country" to get started</p>
          </div>
        ) : (
          countries.map((country, idx) => (
            <Fragment key={country.code}>
              {/* Row */}
              <div
                data-testid={`country-ledger-row-${country.code}`}
                className={`grid grid-cols-[2fr_1fr_1fr_auto_auto_auto] gap-2 px-4 py-3 items-center cursor-pointer transition-colors hover:bg-surface-2 ${
                  expandedCode === country.code ? "bg-surface-2 border-b-0" : ""
                } ${idx < countries.length - 1 || expandedCode === country.code ? "border-b border-border" : ""}`}
                onClick={() => onToggleExpand(country.code)}
              >
                {/* Country identity */}
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="text-sm shrink-0">
                    {expandedCode === country.code ? (
                      <ChevronDown className="h-3.5 w-3.5 text-primary" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 text-text-muted" />
                    )}
                  </span>
                  {country.flag_url ? (
                    <img src={country.flag_url} alt={country.code} className="h-4 w-6 object-cover rounded shadow-sm shrink-0" />
                  ) : (
                    <span className="text-sm shrink-0">🌍</span>
                  )}
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-text truncate">{country.name}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[10px] font-mono text-text-faint">{country.code}</span>
                      {country.region && (
                        <span className="text-[9px] text-text-faint">· {country.region}</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Currency */}
                <div>
                  <span className="text-sm font-medium text-text">{country.currency}</span>
                  {country.currency_symbol && (
                    <span className="ml-1 text-xs text-text-muted">{country.currency_symbol}</span>
                  )}
                </div>

                {/* Tax */}
                <div>
                  <span className="text-sm text-text">
                    {country.tax_rate != null ? `${(country.tax_rate * 100).toFixed(1)}%` : "—"}
                  </span>
                  <span className="ml-1 text-[10px] text-text-muted">{country.tax_name}</span>
                </div>

                {/* Cities count */}
                <div className="text-center">
                  <span className="text-sm text-text-muted">{country.city_count}</span>
                </div>

                {/* Status */}
                <div className="flex items-center justify-center">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      country.is_active
                        ? "bg-success/10 text-success"
                        : "bg-surface-3 text-text-muted border border-border"
                    }`}
                  >
                    {country.is_active ? "Active" : "Draft"}
                  </span>
                </div>

                {/* Actions */}
                <div>
                  <ExternalLink className="h-3.5 w-3.5 text-text-faint hover:text-primary transition-colors" />
                </div>
              </div>

              {/* Expanded workspace — rendered by parent via children */}
              {expandedCode === country.code && children && (
                <div className="border-b border-border bg-surface-1/50">
                  {children}
                </div>
              )}
            </Fragment>
          ))
        )}
      </div>
    </div>
  );
}


