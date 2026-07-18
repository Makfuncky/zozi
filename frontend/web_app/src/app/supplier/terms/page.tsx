"use client";

import { useCallback, useEffect, useState } from "react";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { BookOpen, CheckCircle2, Loader2, ShieldCheck } from "@/lib/icons";

type OnboardingStatus = {
  terms_accepted?: boolean;
};

const HIGHLIGHTS = [
  "You are responsible for accurate product listings, pricing, and stock availability.",
  "Payouts are released after successful delivery and any applicable hold period.",
  "Commission rates are applied per the badge tier active on your account.",
  "You must comply with local laws, tax obligations, and platform policies.",
];

export default function SupplierTermsPage() {
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const addToast = useToastStore((state) => state.addToast);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await apiFetch("/supplier/onboarding/status");
      const json = (await parseJsonResponse(res)) as OnboardingStatus;
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      setStatus(json);
      setAccepted(Boolean(json.terms_accepted));
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load terms status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const accept = async () => {
    setSubmitting(true);
    try {
      const res = await apiFetch("/supplier/terms/accept", { method: "POST" });
      const json = (await parseJsonResponse(res)) as { detail?: string };
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      setAccepted(true);
      addToast("Terms accepted. Thank you!", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to accept terms", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SupplierLayout title="Terms">
      <PanelContent width="wide">
        <PanelHero
          eyebrow="Account"
          title="Supplier Agreement & Policies"
          description="Review the ZOZI supplier terms of service. Accepting confirms your commitment to our marketplace policies."
          icon={<BookOpen className="h-5 w-5" />}
        />

        {loading ? (
          <div className="theme-card rounded-xl border p-8 text-center text-xs text-text-muted">
            <Loader2 className="mx-auto h-5 w-5 animate-spin text-primary" />
            <p className="mt-2">Loading terms status…</p>
          </div>
        ) : loadError ? (
          <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
            <p className="text-sm font-semibold text-text">{loadError}</p>
            <button
              onClick={() => void load()}
              className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="theme-card rounded-xl border p-5">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-primary/12 p-3 text-primary">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-text">Agreement Status</p>
                  <p className="mt-1 flex items-center gap-2 text-xs text-text-muted">
                    {accepted ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-success" />
                        You have accepted the current supplier terms.
                      </>
                    ) : (
                      "You have not yet accepted the supplier terms."
                    )}
                  </p>
                </div>
              </div>
            </div>

            <div className="theme-card rounded-xl border p-5">
              <p className="text-sm font-semibold text-text">Key Terms Summary</p>
              <ul className="mt-3 space-y-2">
                {HIGHLIGHTS.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-xs text-text-muted">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-[11px] leading-5 text-text-faint">
                This summary is provided for convenience. The full legally binding agreement is available
                from your onboarding packet and the ZOZI supplier policy center.
              </p>
            </div>

            {!accepted ? (
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => void accept()}
                  disabled={submitting}
                  className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-semibold disabled:opacity-50"
                >
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                  {submitting ? "Accepting…" : "Accept Terms"}
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-end gap-2 rounded-xl border border-success/30 bg-success/10 px-4 py-3 text-xs font-semibold text-success">
                <CheckCircle2 className="h-4 w-4" />
                Terms accepted — no further action required.
              </div>
            )}
          </div>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
