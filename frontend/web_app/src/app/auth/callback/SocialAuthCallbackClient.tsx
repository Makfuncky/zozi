"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import { useLocaleStore } from "@/lib/localeStore";

function mapSocialError(error: string, tr: (key: string) => string): string {
  if (error === "google_email_required" || error === "facebook_email_required") {
    return tr("socialEmailRequired");
  }
  if (error === "access_denied") {
    return tr("socialLoginCancelled");
  }
  return tr("socialLoginFailed");
}

export default function SocialAuthCallbackClient() {
  const router = useRouter();
  const params = useSearchParams();
  const { refresh } = useAuth();
  const tr = useLocaleStore((s) => s.t);
  const [message, setMessage] = useState(tr("loading"));

  useEffect(() => {
    const run = async () => {
      const token = params?.get("token");
      const error = params?.get("error");

      if (error) {
        router.replace(`/login?error=${encodeURIComponent(mapSocialError(error, tr as any))}`);
        return;
      }

      if (!token) {
        router.replace(`/login?error=${encodeURIComponent(tr("socialLoginFailed"))}`);
        return;
      }

      try {
        // Exchange the URL token for httpOnly cookies via server endpoint.
        // This avoids storing the token in localStorage or keeping it in the URL.
        const res = await fetch("/api/auth/social-callback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Token exchange failed");
        }

        // Clean the URL immediately so the token is not visible in browser history
        window.history.replaceState({}, "", window.location.pathname);

        // Refresh user state — the httpOnly cookie will be sent automatically
        const user = await refresh();
        if (!user) {
          throw new Error("refresh failed");
        }

        if (user.role === "supplier") {
          router.replace("/supplier/dashboard");
        } else if (
          (user.role as string) === "admin" ||
          (user.role as string) === "sub_admin" ||
          (user.role as string) === "moderator" ||
          (user.role as string) === "support"
        ) {
          router.replace("/admin/dashboard");
        } else {
          router.replace("/");
        }
      } catch {
        setMessage(tr("socialLoginFailed"));
        router.replace(`/login?error=${encodeURIComponent(tr("socialLoginFailed"))}`);
      }
    };

    run();
  }, [params, refresh, router, tr]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-base px-4 text-text">
      <div className="theme-card rounded-2xl border px-6 py-8 text-center text-sm">
        {message}
      </div>
    </main>
  );
}
