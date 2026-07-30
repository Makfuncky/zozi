"use client";

import { Fragment } from "react";
import { formatNumber, PieChartComponent, BarChartComponent } from "@/components/ChartComponents";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function AnalyticsTab({
  ...p
}: CountriesTabProps) {
  const { categoryCommissions, cities, commissionTiers, country, name, promotionRules, regions, staffAssignments } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-analytics-panel">
      <h3 className="text-sm font-bold text-text">Analytics & Performance Metrics</h3>
      <p className="text-xs text-text-muted">View country configuration analytics and performance indicators.</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="text-2xl font-bold text-primary">{country?.regions?.reduce((acc, r) => acc + (r.cities?.length || 0), 0) || 0}</div>
          <div className="text-[10px] text-text-muted uppercase">Cities Covered</div>
        </div>
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="text-2xl font-bold text-primary">{country?.payment_gateways?.filter(g => g.enabled).length || 0}</div>
          <div className="text-[10px] text-text-muted uppercase">Active Gateways</div>
        </div>
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="text-2xl font-bold text-primary">{country?.logistics_providers?.filter(p => p.enabled).length || 0}</div>
          <div className="text-[10px] text-text-muted uppercase">Delivery Partners</div>
        </div>
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="text-2xl font-bold text-primary">{promotionRules.length}</div>
          <div className="text-[10px] text-text-muted uppercase">Active Promotions</div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">

        <div className="rounded-lg border border-border bg-surface p-4">
          <h4 className="text-xs font-bold text-text mb-3">Tax Configuration</h4>
          <div className="h-56">
            <PieChartComponent
              data={[
                { label: "Standard Rate", value: country?.tax_rate ? (country.tax_rate * 100) : 0 },
                { label: "Exempt Categories", value: country?.tax_exempt_categories?.length || 0 },
                { label: "Reduced Rates", value: country?.tax_reduced_rates ? Object.keys(country.tax_reduced_rates).length : 0 },
              ]}
              title={`Tax Rate: ${country?.tax_rate ? (country.tax_rate * 100).toFixed(1) : 0}%`}
              colors={["#22c55e", "#6366f1", "#f59e0b"]}
            />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <h4 className="text-xs font-bold text-text mb-3">Payment Gateway Distribution</h4>
          <div className="h-56">
            <BarChartComponent
              data={country?.payment_gateways?.map(g => ({
                label: g.name.length > 10 ? g.name.substring(0, 10) + "..." : g.name,
                value: g.fee_percentage,
                enabled: g.enabled
              })) || []}
              title="Fees %"
              yKeys={["value"]}
              color="#3b82f6"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-text">Commission Structure</h4>
          <div className="text-[10px] space-y-1">
            <div className="flex justify-between">
              <span className="text-text-faint">Value-based Tiers:</span>
              <span className="text-text font-medium">{commissionTiers.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-faint">Category Overrides:</span>
              <span className="text-text font-medium">{categoryCommissions.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-faint">Avg. Commission Rate:</span>
              <span className="text-text font-medium">
                {categoryCommissions.length > 0 
                  ? (categoryCommissions.reduce((sum, c) => sum + c.commission_rate, 0) / categoryCommissions.length * 100).toFixed(1) + "%"
                  : "N/A"}
              </span>
            </div>
          </div>
        </div>
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-text">Regional Coverage</h4>
          <div className="text-[10px] space-y-1">
            <div className="flex justify-between">
              <span className="text-text-faint">Regions/Hubs:</span>
              <span className="text-text font-medium">{regions.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-faint">Staff Assignments:</span>
              <span className="text-text font-medium">{staffAssignments.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-faint">Active Status:</span>
              <span className={`font-medium ${country?.is_active ? "text-success" : "text-danger"}`}>
                {country?.is_active ? "Active" : "Inactive"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="text-[10px] text-text-muted italic border-t border-border pt-2">
        Advanced analytics dashboard with sales trends, conversion rates, and performance KPIs coming soon.
      </div>
    </section>
  );
}
