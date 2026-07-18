"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowLeft, Globe, MapPin, Phone, RefreshCw, ShieldCheck, Truck } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { resolveImage } from "@/lib/utils";
import { useAuth } from "@/lib/useAuth";

type ServiceArea = {
  id: number;
  country_code: string;
  country_name: string;
  city_name?: string | null;
  origin_city?: string | null;
  zone_label?: string | null;
  charge_amount: number;
  pickup_charge?: number | null;
  dropoff_charge?: number | null;
  currency: string;
  delivery_days_min?: number | null;
  delivery_days_max?: number | null;
};

type LogisticsPartnerDetail = {
  id: number;
  name: string;
  code: string;
  bio?: string | null;
  about_us?: string | null;
  city?: string | null;
  country?: string | null;
  address?: string | null;
  website?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  verification_status: string;
  service_types?: string[];
  coverage_regions?: string[];
  service_areas?: ServiceArea[];
};

export default function LogisticsPartnerDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const [reloadKey, setReloadKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [partner, setPartner] = useState<LogisticsPartnerDetail | null>(null);

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
        const response = await apiFetch(`/logistics-partners/public/${params?.id}`);
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(payload?.detail || "Could not load this logistics partner.");
        }
        if (!active) return;
        setPartner(payload);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load this logistics partner.");
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
  }, [isLoggedIn, params?.id, reloadKey]);

  const serviceAreaSummary = useMemo(() => {
    const areas = partner?.service_areas || [];
    const countries = new Set(areas.map((area) => area.country_name).filter(Boolean));
    const cities = new Set(areas.map((area) => area.city_name).filter(Boolean));
    return {
      totalAreas: areas.length,
      countryCount: countries.size,
      cityCount: cities.size,
    };
  }, [partner?.service_areas]);

  if (authLoading || !isLoggedIn) {
    return <main className="min-h-screen flex items-center justify-center text-sm text-text-muted">Loading logistics partner...</main>;
  }

  if (loading) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="mx-auto max-w-5xl space-y-4">
          <div className="h-64 animate-pulse rounded-3xl border border-border bg-surface-2" />
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="h-72 animate-pulse rounded-3xl border border-border bg-surface-2" />
            <div className="h-72 animate-pulse rounded-3xl border border-border bg-surface-2" />
          </div>
        </div>
      </main>
    );
  }

  if (error || !partner) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="mx-auto max-w-3xl rounded-3xl border border-danger/30 bg-danger/10 p-6 text-sm text-danger">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-semibold">Logistics partner unavailable</p>
              <p className="mt-1">{error || "This approved logistics partner could not be loaded."}</p>
              <button onClick={() => router.push("/logistics-partners")} className="mt-4 text-xs font-semibold text-danger underline">
                Back to logistics partners
              </button>
            </div>
          </div>
        </div>
      </main>
    );
  }

  const banner = resolveImage(partner.banner_url || partner.logo_url || undefined);
  const logo = resolveImage(partner.logo_url || partner.banner_url || undefined);
  const location = [partner.city, partner.country].filter(Boolean).join(", ");

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,var(--color-surface-0),var(--color-surface-1))] px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-center justify-between gap-3">
          <button onClick={() => router.push("/logistics-partners")} className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-xs font-semibold text-text-muted hover:text-text">
            <ArrowLeft className="h-3.5 w-3.5" />Back to logistics partners
          </button>
          <button onClick={() => setReloadKey((current) => current + 1)} className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-xs font-semibold text-text-muted hover:text-text">
            <RefreshCw className="h-3.5 w-3.5" />Refresh
          </button>
        </div>

        <section className="overflow-hidden rounded-3xl border border-border bg-surface">
          <div className="relative h-52 overflow-hidden bg-surface-2">
            <img src={banner} alt={partner.name} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-linear-to-t from-black/55 via-black/10 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-6">
              <div className="flex flex-wrap items-end gap-4">
                <img src={logo} alt={partner.name} className="h-20 w-20 rounded-3xl border border-white/60 bg-white object-cover shadow-xl" />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h1 className="text-3xl font-black tracking-tight text-white">{partner.name}</h1>
                    <span className="rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-white backdrop-blur">
                      <ShieldCheck className="mr-1 inline h-3 w-3" />Approved
                    </span>
                  </div>
                  <p className="mt-2 text-sm font-mono text-white/80">{partner.code}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="grid gap-4 border-t border-border p-6 md:grid-cols-3">
            <div className="rounded-2xl border border-border bg-surface-2/50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Coverage</p>
              <p className="mt-2 text-2xl font-black text-text">{serviceAreaSummary.totalAreas}</p>
              <p className="text-xs text-text-muted">Approved charge rows</p>
            </div>
            <div className="rounded-2xl border border-border bg-surface-2/50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Countries</p>
              <p className="mt-2 text-2xl font-black text-text">{serviceAreaSummary.countryCount}</p>
              <p className="text-xs text-text-muted">Distinct approved destinations</p>
            </div>
            <div className="rounded-2xl border border-border bg-surface-2/50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Cities</p>
              <p className="mt-2 text-2xl font-black text-text">{serviceAreaSummary.cityCount}</p>
              <p className="text-xs text-text-muted">City-specific approved rows</p>
            </div>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="theme-card rounded-3xl border p-6">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">
              <Truck className="h-4 w-4" />About this partner
            </div>
            {partner.bio ? <p className="mt-4 text-sm leading-7 text-text-muted">{partner.bio}</p> : null}
            {partner.about_us ? <p className="mt-4 text-sm leading-7 text-text-muted">{partner.about_us}</p> : null}

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {location ? <div className="rounded-2xl border border-border bg-surface-2/50 p-4 text-sm text-text-muted"><MapPin className="mb-2 h-4 w-4 text-primary" />{location}</div> : null}
              {partner.address ? <div className="rounded-2xl border border-border bg-surface-2/50 p-4 text-sm text-text-muted"><MapPin className="mb-2 h-4 w-4 text-primary" />{partner.address}</div> : null}
              {partner.contact_phone ? <div className="rounded-2xl border border-border bg-surface-2/50 p-4 text-sm text-text-muted"><Phone className="mb-2 h-4 w-4 text-primary" />{partner.contact_phone}</div> : null}
              {partner.website ? <a href={partner.website} target="_blank" rel="noreferrer" className="rounded-2xl border border-border bg-surface-2/50 p-4 text-sm text-text-muted hover:border-primary/30 hover:text-text"><Globe className="mb-2 h-4 w-4 text-primary" />{partner.website.replace(/^https?:\/\//, "")}</a> : null}
            </div>

            {(partner.service_types || []).length > 0 ? (
              <div className="mt-6">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Service types</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(partner.service_types || []).map((service) => (
                    <span key={service} className="rounded-full border border-border bg-surface-2 px-3 py-1 text-xs font-semibold text-text-muted">
                      {service.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </section>

          <section className="theme-card rounded-3xl border p-6">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">
              <ShieldCheck className="h-4 w-4" />Approved service areas
            </div>
            <p className="mt-3 text-sm text-text-muted">
              These are the destination rows currently approved for this partner. Customer quotes still depend on matching country and city.
            </p>
            <div className="mt-5 space-y-3">
              {(partner.service_areas || []).length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border px-4 py-10 text-center text-sm text-text-muted">
                  No approved service areas are public yet.
                </div>
              ) : (
                (partner.service_areas || []).map((area) => (
                  <div key={area.id} className="rounded-2xl border border-border bg-surface-2/50 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-semibold text-text">{area.zone_label || area.city_name || area.country_name}</p>
                      <span className="theme-chip-success rounded-full px-2 py-0.5 text-[10px] font-bold">Approved</span>
                    </div>
                    <p className="mt-2 text-xs text-text-muted">{[area.origin_city ? `Pickup ${area.origin_city}` : null, area.city_name, area.country_name, area.country_code].filter(Boolean).join(" · ")}</p>
                    <p className="mt-2 text-sm font-semibold text-text">{area.currency} {area.charge_amount.toFixed(2)}</p>
                    {(area.pickup_charge != null || area.dropoff_charge != null) ? (
                      <p className="mt-1 text-xs text-text-muted">Pickup {area.pickup_charge != null ? `${area.currency} ${area.pickup_charge.toFixed(2)}` : "—"} · Drop-off {area.dropoff_charge != null ? `${area.currency} ${area.dropoff_charge.toFixed(2)}` : "—"}</p>
                    ) : null}
                    {(area.delivery_days_min != null || area.delivery_days_max != null) ? (
                      <p className="mt-1 text-xs text-text-muted">ETA {area.delivery_days_min ?? "?"}-{area.delivery_days_max ?? "?"} day(s)</p>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </section>
        </div>

        <section className="rounded-3xl border border-border bg-surface p-6 text-sm text-text-muted">
          <p>
            Looking for shipping charges during checkout? Quotes are still calculated automatically from approved destination matches in the cart and checkout flow.
            Continue shopping in <Link href="/products" className="font-semibold text-primary hover:underline">products</Link> or go back to <Link href="/logistics-partners" className="font-semibold text-primary hover:underline">the logistics directory</Link>.
          </p>
        </section>
      </div>
    </main>
  );
}