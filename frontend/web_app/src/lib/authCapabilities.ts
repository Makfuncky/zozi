"use client";

import { useEffect, useState } from "react";

export type AuthCapabilities = {
  google: boolean;
  google_mode?: "gsi" | "redirect" | "disabled";
  google_client_id?: string | null;
  facebook: boolean;
  facebook_mode?: "redirect" | "disabled";
  customer_email_verification_required: boolean;
  email_delivery?: {
    available: boolean;
    live: boolean;
    preview_only: boolean;
    provider: string;
    from_address?: string | null;
  };
};

const OAUTH_PROVIDERS_PROXY_URL = "/api/auth/oauth/providers";

export function useAuthCapabilities() {
  const [capabilities, setCapabilities] = useState<AuthCapabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        const res = await fetch(OAUTH_PROVIDERS_PROXY_URL, { cache: "no-store" });
        const data = await res.json().catch(() => null);
        if (!res.ok || !data) {
          throw new Error(data?.detail || "Unable to load sign-in options");
        }
        if (!cancelled) {
          setCapabilities(data as AuthCapabilities);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setCapabilities(null);
          setError(err instanceof Error ? err.message : "Unable to load sign-in options");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, []);

  return { capabilities, loading, error };
}
