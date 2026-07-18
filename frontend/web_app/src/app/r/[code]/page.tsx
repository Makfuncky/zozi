"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const APP_SCHEME = process.env.NEXT_PUBLIC_APP_DEEP_LINK_SCHEME || "zozi";

function isProbablyMobile(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
}

export default function ReferralEntryPage() {
  const params = useParams<{ code?: string }>();
  const [redirecting, setRedirecting] = useState(true);

  const referralCode = useMemo(
    () => String(params?.code || "").trim().toUpperCase(),
    [params?.code]
  );

  const fallbackRegisterUrl = useMemo(() => {
    if (!referralCode) return "/register";
    return `/register?ref=${encodeURIComponent(referralCode)}`;
  }, [referralCode]);

  const appRegisterUrl = useMemo(() => {
    if (!referralCode) return `${APP_SCHEME}://register`;
    return `${APP_SCHEME}://register?ref=${encodeURIComponent(referralCode)}`;
  }, [referralCode]);

  useEffect(() => {
    if (!referralCode || typeof window === "undefined") {
      setRedirecting(false);
      return;
    }

    if (!isProbablyMobile()) {
      window.location.replace(fallbackRegisterUrl);
      return;
    }

    let openedApp = false;
    const onVisibilityChange = () => {
      if (document.visibilityState === "hidden") openedApp = true;
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    const fallbackTimer = window.setTimeout(() => {
      if (!openedApp) {
        window.location.replace(fallbackRegisterUrl);
      }
      setRedirecting(false);
    }, 1400);

    window.location.href = appRegisterUrl;

    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.clearTimeout(fallbackTimer);
    };
  }, [appRegisterUrl, fallbackRegisterUrl, referralCode]);

  return (
    <main className="min-h-screen bg-surface-base px-4 py-10 text-text">
      <div className="mx-auto w-full max-w-lg rounded-2xl border border-border bg-surface-1 p-6 shadow-sm">
        <h1 className="text-xl font-bold">Referral Invite</h1>
        <p className="mt-2 text-sm text-text-muted">
          {referralCode
            ? `Invite code detected: ${referralCode}`
            : "No referral code found in this link."}
        </p>
        <p className="mt-3 text-sm text-text-muted">
          {redirecting
            ? "Opening the app registration screen..."
            : "Continue in app or register on web."}
        </p>

        <div className="mt-6 flex flex-wrap gap-2">
          <a
            href={appRegisterUrl}
            className="theme-btn-primary rounded-xl px-4 py-2 text-sm font-semibold"
          >
            Open App
          </a>
          <Link
            href={fallbackRegisterUrl}
            className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-text-muted transition-colors hover:text-text"
          >
            Continue on Web
          </Link>
        </div>
      </div>
    </main>
  );
}
