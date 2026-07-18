"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, Globe, MapPin, RefreshCw, Search, ShieldCheck, Truck } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { resolveImage } from "@/lib/utils";
import { useAuth } from "@/lib/useAuth";

type LogisticsPartnerSummary = {
  id: number;
  name: string;
  code: string;
  bio?: string | null;
  city?: string | null;
  country?: string | null;
  website?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  verification_status: string;
  service_types?: string[];
  coverage_regions?: string[];
};

type PublicPartnersResponse = {
  total: number;
  items: LogisticsPartnerSummary[];
};

export default function LogisticsPartnersDiscoveryPage() {
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [data, setData] = useState<PublicPartnersResponse>({ total: 0, items: [] });

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
    }
  }, [authLoading, isLoggedIn, router]);

  useEffect(() => {
    if (!isLoggedIn) return;
    let active = true;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams();
        if (submittedQuery.trim()) {
          params.set("q", submittedQuery.trim());
        }
        params.set("limit", "24");
        const path = `/logistics-partners/public${params.toString() ? `?${params.toString()}` : ""}`;
        const response = await apiFetch(path);
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(payload?.detail || "Could not load logistics partners right now.");
        }
        if (!active) return;
        setData({
          total: Number(payload?.total ?? 0),
          items: Array.isArray(payload?.items) ? payload.items : [],
        });
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load logistics partners right now.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      active = false;
    };
  }, [isLoggedIn, reloadKey, submittedQuery]);

  const activeFilters = useMemo(() => submittedQuery.trim(), [submittedQuery]);

  if (authLoading || !isLoggedIn) {
    return <main className="min-h-screen flex items-center justify-center text-sm text-text-muted">Loading logistics partners...</main>;
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.10),_transparent_40%),linear-gradient(180deg,_var(--color-surface-0),_var(--color-surface-1))] px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="theme-card overflow-hidden rounded-3xl border p-6 sm:p-8">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-primary">Approved Delivery Network</p>
              <h1 className="mt-3 text-3xl font-black tracking-tight text-text sm:text-4xl">Discover logistics partners approved for the marketplace.</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-muted">
                These partners passed profile approval. Their approved service areas and charge rows are what drive customer quotes and shipment pickup eligibility.
              </p>
              <div className="mt-5 flex flex-wrap gap-2 text-xs">
                <span className="theme-chip-success rounded-full px-3 py-1 font-semibold">Profile approved</span>
                <span className="theme-chip-info rounded-full px-3 py-1 font-semibold">Coverage visible</span>
                <span className="theme-chip-warning rounded-full px-3 py-1 font-semibold">Charges still depend on destination</span>
              </div>
            </div>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                setSubmittedQuery(query);
              }}
              className="rounded-2xl border border-border bg-surface-2/60 p-4"
            >
              <label className="text-xs font-semibold text-text-muted">Search partner, city, country, or code</label>
              <div className="mt-2 flex gap-2">
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search approved logistics partners"
                    className="theme-input w-full rounded-2xl border px-10 py-3 text-sm"
                  />
                </div>
                <button type="submit" className="theme-btn-primary rounded-2xl px-4 py-3 text-sm font-semibold">Search</button>
              </div>
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                  setSubmittedQuery("");
                }}
                className="mt-3 text-xs font-semibold text-primary hover:underline"
              >
                Clear filter
              </button>
            </form>
          </div>
        </section>

        <section className="flex flex-wrap items-center justify-between gap-3 text-sm">
          <div>
            <p className="font-semibold text-text">{loading ? "Loading..." : `${data.total.toLocaleString()} approved partner${data.total === 1 ? "" : "s"}`}</p>
            <p className="text-xs text-text-muted">{activeFilters ? `Filtered by \"${activeFilters}\"` : "Showing all currently approved partner profiles."}</p>
          </div>
          <button
            onClick={() => setReloadKey((current) => current + 1)}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </section>

        {error ? (
          <div className="rounded-2xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          </div>
        ) : null}

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-72 animate-pulse rounded-3xl border border-border bg-surface-2" />
            ))}
          </div>
        ) : data.items.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-border bg-surface/60 px-6 py-16 text-center">
            <Truck className="mx-auto h-8 w-8 text-text-faint" />
            <h2 className="mt-4 text-lg font-bold text-text">No approved logistics partners matched</h2>
            <p className="mt-2 text-sm text-text-muted">Try a broader city, country, or partner name. Only approved partner profiles appear here.</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.items.map((partner) => {
              const location = [partner.city, partner.country].filter(Boolean).join(", ");
              const logo = resolveImage(partner.logo_url || partner.banner_url || undefined);
              return (
                <Link
                  key={partner.id}
                  href={`/logistics-partners/${partner.id}`}
                  className="group overflow-hidden rounded-3xl border border-border bg-surface transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5"
                >
                  <div className="relative h-28 overflow-hidden bg-linear-to-r from-primary/10 via-accent/10 to-brand/10">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.20),_transparent_45%)]" />
                    <img src={logo} alt={partner.name} className="absolute bottom-4 left-4 h-16 w-16 rounded-2xl border border-white/60 bg-white object-cover shadow-lg" />
                  </div>
                  <div className="space-y-4 p-5">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-lg font-bold text-text group-hover:text-primary">{partner.name}</h2>
                        <span className="theme-chip-success rounded-full px-2 py-0.5 text-[10px] font-bold">
                          <ShieldCheck className="mr-1 inline h-3 w-3" />Approved
                        </span>
                      </div>
                      <p className="mt-1 text-xs font-mono text-text-faint">{partner.code}</p>
                    </div>

                    <div className="space-y-2 text-xs text-text-muted">
                      {location ? (
                        <p className="flex items-center gap-2"><MapPin className="h-3.5 w-3.5" />{location}</p>
                      ) : null}
                      {partner.website ? (
                        <p className="flex items-center gap-2"><Globe className="h-3.5 w-3.5" />{partner.website.replace(/^https?:\/\//, "")}</p>
                      ) : null}
                    </div>

                    {partner.bio ? <p className="line-clamp-3 text-sm leading-6 text-text-muted">{partner.bio}</p> : null}

                    <div className="flex flex-wrap gap-2 text-[11px]">
                      {(partner.service_types || []).slice(0, 3).map((service) => (
                        <span key={service} className="rounded-full border border-border bg-surface-2 px-2.5 py-1 font-semibold text-text-muted">
                          {service.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}


