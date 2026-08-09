"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Globe,
  Users,
  Banknote,
  Percent,
  ShoppingBag,
  Package,
  Calendar,
  Wifi,
  CreditCard,
  Truck,
  Scale,
  Megaphone,
  TrendingUp,
  Headphones,
  Cpu,
  Newspaper,
  ShieldAlert,
  Sparkles,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Globe2,
  MapPin,
  Clock,
  Star,
  Gauge,
  Info,
  MessageSquare,
} from "@/lib/icons";
import type { LucideIcon } from "@/lib/icons";
import { apiFetch } from "@/lib/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

interface ModuleMeta {
  confidence?: string;
  verification_notes?: string;
  sources?: string[];
  [key: string]: unknown;
}

interface ResearchData {
  meta: {
    generated_at_utc: string;
    country_code: string;
    country_name: string;
    overall_confidence: string;
    modules_available: number;
    modules_total: number;
    data_sources: string[];
  };
  [moduleKey: string]: ModuleMeta | unknown;
}

interface ModuleDef {
  key: string;
  label: string;
  icon: LucideIcon;
  color: string;
}

// ── Module Definitions ─────────────────────────────────────────────────────

const RESEARCH_MODULES: ModuleDef[] = [
  { key: "module_01_country_identity", label: "Country Identity", icon: Globe, color: "text-blue-500" },
  { key: "module_02_demographics", label: "Demographics", icon: Users, color: "text-green-500" },
  { key: "module_03_economy_wealth", label: "Economy & Wealth", icon: Banknote, color: "text-yellow-500" },
  { key: "module_04_tax_duties", label: "Tax & Duties", icon: Percent, color: "text-red-500" },
  { key: "module_05_consumer_psychology", label: "Consumer Psychology", icon: ShoppingBag, color: "text-purple-500" },
  { key: "module_06_consumption_preferences", label: "Consumption Preferences", icon: Package, color: "text-pink-500" },
  { key: "module_07_shopping_seasonality", label: "Shopping Seasonality", icon: Calendar, color: "text-orange-500" },
  { key: "module_08_digital_landscape", label: "Digital Landscape", icon: Wifi, color: "text-cyan-500" },
  { key: "module_09_payment_infrastructure", label: "Payment Infrastructure", icon: CreditCard, color: "text-emerald-500" },
  { key: "module_10_logistics_shipping", label: "Logistics & Shipping", icon: Truck, color: "text-amber-500" },
  { key: "module_11_legal_regulations", label: "Legal & Regulations", icon: Scale, color: "text-slate-500" },
  { key: "module_12_language_communication", label: "Language & Communication", icon: MessageSquare, color: "text-indigo-500" },
  { key: "module_13_community_social", label: "Community & Social", icon: Users, color: "text-rose-500" },
  { key: "module_14_marketing_advertising", label: "Marketing & Advertising", icon: Megaphone, color: "text-violet-500" },
  { key: "module_15_competition", label: "Competition & Market", icon: TrendingUp, color: "text-lime-500" },
  { key: "module_16_customer_service", label: "Customer Service", icon: Headphones, color: "text-teal-500" },
  { key: "module_17_technology_infrastructure", label: "Technology & Infrastructure", icon: Cpu, color: "text-gray-500" },
  { key: "module_18_news_current_context", label: "News & Current Context", icon: Newspaper, color: "text-sky-500" },
  { key: "module_19_risk_compliance", label: "Risk & Compliance", icon: ShieldAlert, color: "text-red-600" },
  { key: "module_20_strategic_recommendations", label: "Strategic Recommendations", icon: Sparkles, color: "text-yellow-600" },
];

// ── Helpers ─────────────────────────────────────────────────────────────────

function confidenceBadge(confidence?: string) {
  if (!confidence) return null;
  const colors: Record<string, string> = {
    high: "bg-green-100 text-green-800 border-green-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    low: "bg-red-100 text-red-800 border-red-200",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors[confidence] || "bg-gray-100 text-gray-800"}`}>
      {confidence.toUpperCase()}
    </span>
  );
}

function isNonEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value as object).length > 0;
  return true;
}

function renderValue(key: string, value: unknown): React.ReactNode {
  if (!isNonEmpty(value)) return null;

  if (typeof value === "boolean") {
    return (
      <span className={`inline-flex items-center gap-1 ${value ? "text-green-600" : "text-red-500"}`}>
        <span className={`w-2 h-2 rounded-full ${value ? "bg-green-500" : "bg-red-500"}`} />
        {value ? "Yes" : "No"}
      </span>
    );
  }

  if (typeof value === "number") {
    return <span className="font-mono text-sm tabular-nums">{value.toLocaleString()}</span>;
  }

  if (typeof value === "string") {
    if (value.startsWith("http")) {
      return (
        <a href={value} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-600 hover:underline text-sm">
          {value.length > 50 ? value.slice(0, 50) + "..." : value}
          <ExternalLink className="w-3 h-3" />
        </a>
      );
    }
    if (value.length > 120) {
      return <span className="text-sm">{value.slice(0, 120)}...</span>;
    }
    return <span className="text-sm">{value}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    return (
      <div className="flex flex-wrap gap-1.5">
        {value.map((item, i) => {
          if (typeof item === "object" && item !== null) {
            return (
              <span key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-50 rounded text-xs border">
                {Object.entries(item as Record<string, unknown>).slice(0, 2).map(([k, v]) => (
                  <span key={k} className="text-gray-600">{String(v)}</span>
                ))}
              </span>
            );
          }
          return (
            <span key={i} className="inline-flex items-center px-2 py-1 bg-gray-50 rounded text-xs border text-gray-700">
              {String(item)}
            </span>
          );
        })}
      </div>
    );
  }

  if (typeof value === "object" && value !== null) {
    const entries = Object.entries(value as Record<string, unknown>).filter(([, v]) => isNonEmpty(v));
    if (entries.length === 0) return null;
    return (
      <div className="grid grid-cols-2 gap-2 text-sm">
        {entries.map(([k, v]) => (
          <div key={k} className="flex items-center gap-1">
            <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}:</span>
            <span className="font-medium">{String(v)}</span>
          </div>
        ))}
      </div>
    );
  }

  return <span className="text-sm">{String(value)}</span>;
}

// ── Stat Card ───────────────────────────────────────────────────────────────

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon?: LucideIcon; color?: string }) {
  return (
    <div className="bg-white rounded-lg border p-4 flex items-center gap-3">
      {Icon && (
        <div className={`w-10 h-10 rounded-lg ${color || "bg-gray-100"} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${color?.replace("bg-", "text-") || "text-gray-600"}`} />
        </div>
      )}
      <div>
        <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
        <div className="text-xl font-bold tabular-nums">{value}</div>
      </div>
    </div>
  );
}

// ── Module Section ──────────────────────────────────────────────────────────

function ModuleSection({
  def,
  data,
  defaultOpen,
}: {
  def: ModuleDef;
  data?: ModuleMeta;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  if (!data) return null;

  const { confidence, verification_notes, sources, ...fields } = data;
  const entries = Object.entries(fields).filter(([, v]) => isNonEmpty(v));

  if (entries.length === 0) return null;

  return (
    <div className="border rounded-lg bg-white overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg ${def.color.replace("text-", "bg-").replace("500", "100")} flex items-center justify-center`}>
            <def.icon className={`w-4 h-4 ${def.color}`} />
          </div>
          <div>
            <span className="font-medium text-sm">{def.label}</span>
            <div className="flex items-center gap-2 mt-0.5">
              {confidenceBadge(confidence)}
            </div>
          </div>
        </div>
        {open ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>

      {open && (
        <div className="border-t px-4 py-3 space-y-3">
          {entries.map(([key, value]) => {
            const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            const rendered = renderValue(key, value);
            if (!rendered) return null;
            return (
              <div key={key} className="flex flex-col gap-0.5">
                <span className="text-xs text-gray-500 uppercase tracking-wide">{label}</span>
                <div>{rendered}</div>
              </div>
            );
          })}

          {verification_notes && (
            <div className="flex items-start gap-2 p-2 bg-yellow-50 rounded text-xs text-yellow-800 border border-yellow-200">
              <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>{verification_notes}</span>
            </div>
          )}

          {sources && sources.length > 0 && (
            <div className="text-xs text-gray-400">
              Sources: {sources.join(", ")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

interface CountryResearchPanelProps {
  countryCode: string;
}

export default function CountryResearchPanel({ countryCode }: CountryResearchPanelProps) {
  const [research, setResearch] = useState<ResearchData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchResearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/country-research/${countryCode}/research`, {
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed with status ${res.status}`);
      }
      const json = await res.json();
      setResearch(json.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [countryCode]);

  useEffect(() => {
    fetchResearch();
  }, [fetchResearch]);

  // ── Loading state ──
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-sm text-gray-500">Loading research data for {countryCode}...</p>
      </div>
    );
  }

  // ── Error state ──
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <AlertCircle className="w-8 h-8 text-red-500" />
        <p className="text-sm text-red-600">{error}</p>
        <button onClick={fetchResearch} className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90">
          Retry
        </button>
      </div>
    );
  }

  if (!research) return null;

  const meta = research.meta;

  // ── Filter modules by search ──
  const filteredDefs = searchQuery
    ? RESEARCH_MODULES.filter((def) => {
        const data = research[def.key] as ModuleMeta | undefined;
        const entries = data ? Object.entries(data).filter(([, v]) => isNonEmpty(v)) : [];
        return (
          def.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          entries.some(([k, v]) => String(k).toLowerCase().includes(searchQuery.toLowerCase()) || String(v).toLowerCase().includes(searchQuery.toLowerCase()))
        );
      })
    : RESEARCH_MODULES;

  return (
    <div className="space-y-4">
      {/* ── Header Stats ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Country" value={meta.country_name} icon={Globe2} color="bg-blue-100" />
        <StatCard label="Code" value={meta.country_code} icon={MapPin} color="bg-green-100" />
        <StatCard label="Confidence" value={meta.overall_confidence.toUpperCase()} icon={Gauge} color={meta.overall_confidence === "high" ? "bg-green-100" : meta.overall_confidence === "medium" ? "bg-yellow-100" : "bg-red-100"} />
        <StatCard label="Modules" value={`${meta.modules_available}/${meta.modules_total}`} icon={Star} color="bg-purple-100" />
      </div>

      {/* ── Data Sources ── */}
      <div className="text-xs text-gray-400 flex flex-wrap gap-2">
        <span className="font-medium text-gray-500">Data sources:</span>
        {meta.data_sources?.map((s: string) => (
          <span key={s} className="px-2 py-0.5 bg-gray-50 border rounded-full">{s}</span>
        ))}
      </div>

      {/* ── Search ── */}
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search modules and data points..."
        className="w-full px-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
      />

      {/* ── Module Sections ── */}
      <div className="space-y-2">
        {filteredDefs.map((def, idx) => (
          <ModuleSection
            key={def.key}
            def={def}
            data={research[def.key] as ModuleMeta | undefined}
            defaultOpen={idx < 3 || searchQuery.length > 0}
          />
        ))}
        {filteredDefs.length === 0 && (
          <p className="text-center text-gray-400 py-8 text-sm">No modules match your search.</p>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="text-xs text-gray-400 text-center pt-4 border-t">
        Generated at {new Date(meta.generated_at_utc).toLocaleString()}
      </div>
    </div>
  );
}