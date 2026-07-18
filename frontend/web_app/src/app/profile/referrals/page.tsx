"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useMemo, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Gift, Share2, Copy, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type ReferralActivity = {
  id: number;
  event_type: string;
  points: number;
  description?: string;
  referred_username?: string | null;
  created_at: string;
  channel?: string | null;
};

type ReferralDashboard = {
  referral_code: string;
  referral_link: string;
  total_points: number;
  referral_points: number;
  sharing_points: number;
  referred_count: number;
};

type ReferralHistoryResponse = {
  items: ReferralActivity[];
  total: number;
  limit: number;
  offset: number;
};

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

export default function ProfileReferralHistoryPage() {
  const router = useRouter();
  const { isLoading: authLoading, isLoggedIn } = useAuth();

  const [dashboard, setDashboard] = useState<ReferralDashboard | null>(null);
  const [referralEnabled, setReferralEnabled] = useState(true);
  const [items, setItems] = useState<ReferralActivity[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const pageSize = 20;

  const hasMore = useMemo(() => items.length < total, [items.length, total]);

  const hydrate = useCallback(async (reset: boolean) => {
    const nextOffset = reset ? 0 : items.length;
    if (reset) {
      setLoading(true);
      setError("");
    } else {
      setLoadingMore(true);
    }

    try {
      const [dashboardRes, historyRes] = await Promise.all([
        apiFetch("/auth/referrals/me"),
        apiFetch(`/auth/referrals/history?limit=${pageSize}&offset=${nextOffset}`),
      ]);

      if (!dashboardRes.ok) {
        const payload = await dashboardRes.json().catch(() => null);
        throw new Error(payload?.detail || "Unable to load referral dashboard.");
      }
      if (!historyRes.ok) {
        const payload = await historyRes.json().catch(() => null);
        throw new Error(payload?.detail || "Unable to load referral history.");
      }

      const dashboardData = (await dashboardRes.json()) as ReferralDashboard;
      const historyData = (await historyRes.json()) as ReferralHistoryResponse;

      setDashboard(dashboardData);
      setTotal(historyData.total || 0);
      setItems((prev) => (reset ? historyData.items : [...prev, ...historyData.items]));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to load referrals.");
    } finally {
      if (reset) {
        setLoading(false);
      } else {
        setLoadingMore(false);
      }
    }
  }, [items.length]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }

    apiFetch("/referrals/config")
      .then((res) => (res.ok ? res.json() : null))
      .then((cfg) => { if (cfg) setReferralEnabled(Boolean(cfg.enabled)); })
      .catch(() => {});

    void hydrate(true);
  }, [authLoading, isLoggedIn, router, hydrate]);

  async function copyLink() {
    if (!dashboard?.referral_link) return;
    try {
      await navigator.clipboard.writeText(dashboard.referral_link);
      setMsg("Referral link copied.");
      setError("");
    } catch {
      setError("Could not copy referral link.");
      setMsg("");
    }
  }

  async function claimDailyBonus() {
    setClaiming(true);
    setError("");
    setMsg("");
    try {
      const res = await apiFetch("/auth/referrals/share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: "web_referral_history" }),
      });
      const payload = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(payload?.detail || "Could not claim daily sharing bonus.");
      }
      setMsg(payload?.message || "Sharing bonus processed.");
      await hydrate(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not claim daily bonus.");
    } finally {
      setClaiming(false);
    }
  }

  return (
    <main className="min-h-screen bg-surface-base px-4 py-6 text-text">
      <div className="mx-auto w-full max-w-4xl space-y-4">
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => router.push("/profile")}
            className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-text-muted transition-colors hover:text-text"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Profile
          </button>
          <button
            type="button"
            onClick={() => void hydrate(true)}
            className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-text-muted transition-colors hover:text-text"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>

        {referralEnabled ? (
          <>
            <section className="theme-card rounded-2xl border p-4">
              <h1 className="flex items-center gap-2 text-lg font-bold text-text">
                <Gift className="h-5 w-5 text-primary" />
                Referral History
              </h1>
              <p className="mt-1 text-xs text-text-muted">
                Share your invite, earn daily points, and track all referral rewards in one place.
              </p>

              {error && <p className="mt-3 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p>}
              {msg && <p className="mt-3 rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-xs text-success">{msg}</p>}

              {loading ? (
                <div className="mt-4 h-24 animate-pulse rounded-xl bg-surface-2" />
              ) : dashboard ? (
                <>
                  <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 text-center">
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-3">
                      <p className="text-[10px] text-text-faint">Total</p>
                      <p className="mt-1 text-sm font-bold text-primary">{dashboard.total_points}</p>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-3">
                      <p className="text-[10px] text-text-faint">Referral</p>
                      <p className="mt-1 text-sm font-bold text-text">{dashboard.referral_points}</p>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-3">
                      <p className="text-[10px] text-text-faint">Sharing</p>
                      <p className="mt-1 text-sm font-bold text-text">{dashboard.sharing_points}</p>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-3">
                      <p className="text-[10px] text-text-faint">Friends</p>
                      <p className="mt-1 text-sm font-bold text-text">{dashboard.referred_count}</p>
                    </div>
                  </div>

                  <div className="mt-3 rounded-xl border border-border bg-surface-2/50 p-3">
                    <p className="text-[10px] text-text-faint">Invite link</p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <input
                        value={dashboard.referral_link}
                        readOnly
                        className="theme-input h-9 min-w-56 flex-1 rounded-lg border px-2 text-[11px]"
                      />
                      <button
                        type="button"
                        onClick={copyLink}
                        className="inline-flex h-9 items-center gap-1 rounded-lg border border-border px-3 text-xs font-semibold text-text-muted transition-colors hover:text-text"
                      >
                        <Copy className="h-3.5 w-3.5" />
                        Copy
                      </button>
                      <Button variant="primary" type="button"
                        onClick={claimDailyBonus}
                        disabled={claiming}>
                        <Share2 className="h-3.5 w-3.5" />
                        {claiming ? "Claiming..." : "Claim daily +5"}
                      </Button>
                    </div>
                  </div>
                </>
              ) : null}
            </section>

            <section className="theme-card rounded-2xl border p-4">
              <h2 className="text-sm font-semibold text-text">Activity Ledger</h2>
              <p className="mt-1 text-xs text-text-muted">{items.length} of {total} events loaded</p>

              <div className="mt-3 space-y-2">
                {items.length === 0 && !loading ? (
                  <p className="rounded-lg border border-border bg-surface-2/50 px-3 py-3 text-xs text-text-muted">
                    No referral activity yet. Share your invite link to start earning points.
                  </p>
                ) : (
                  items.map((event) => (
                    <div key={event.id} className="flex items-center justify-between gap-3 rounded-lg border border-border/70 bg-surface-2/40 px-3 py-2">
                      <div className="min-w-0">
                        <p className="truncate text-xs font-semibold text-text">{event.description || event.event_type.replaceAll("_", " ")}</p>
                        <p className="mt-0.5 text-[11px] text-text-faint">{formatDate(event.created_at)}{event.referred_username ? ` • ${event.referred_username}` : ""}</p>
                      </div>
                      <p className="shrink-0 text-sm font-bold text-success">+{event.points}</p>
                    </div>
                  ))
                )}
              </div>

              {hasMore && (
                <div className="mt-3">
                  <button
                    type="button"
                    disabled={loadingMore}
                    onClick={() => void hydrate(false)}
                    className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-muted transition-colors hover:text-text disabled:opacity-50"
                  >
                    {loadingMore ? "Loading..." : "Load more"}
                  </button>
                </div>
              )}
            </section>
          </>
        ) : (
          <section className="theme-card rounded-2xl border p-4 text-center">
            <Gift className="mx-auto h-8 w-8 text-text-faint" />
            <p className="mt-2 text-sm font-semibold text-text">Referral program is currently disabled</p>
            <p className="mt-1 text-xs text-text-muted">Check back later — the referral rewards program is paused right now.</p>
          </section>
        )}
      </div>
    </main>
  );
}


