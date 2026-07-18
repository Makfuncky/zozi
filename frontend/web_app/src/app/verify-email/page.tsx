"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle, XCircle } from "lucide-react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import BrandLoading from "@/components/BrandLoading";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams?.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided.");
      return;
    }

    apiFetch(`/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setStatus("success");
          setMessage(data.detail || "Your email has been verified!");
        } else {
          setStatus("error");
          setMessage(data.detail || "Verification failed.");
        }
      })
      .catch(() => {
        setStatus("error");
        setMessage("Network error. Please try again.");
      });
  }, [token]);

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-sm w-full theme-card border rounded-2xl p-8 text-center">
        {status === "loading" && (
          <BrandLoading label="Verifying your email..." size={72} className="py-4" />
        )}
        {status === "success" && (
          <>
            <CheckCircle className="theme-status-success mx-auto mb-4 h-12 w-12" />
            <h1 className="text-text font-bold text-lg mb-2">Email Verified!</h1>
            <p className="text-text-muted text-sm mb-6">{message}</p>
            <Link
              href="/login"
              className="theme-btn-primary inline-block rounded-xl px-6 py-2.5 text-sm font-bold"
            >
              Sign In
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <XCircle className="theme-status-danger mx-auto mb-4 h-12 w-12" />
            <h1 className="text-text font-bold text-lg mb-2">Verification Failed</h1>
            <p className="text-text-muted text-sm mb-6">{message}</p>
            <div className="flex flex-col gap-2">
              <Link
                href="/login"
                className="theme-btn-primary inline-block rounded-xl px-6 py-2.5 text-sm font-bold"
              >
                Back to Login
              </Link>
              <p className="text-text-faint text-xs">
                Already logged in?{" "}
                <Link href="/profile" className="theme-link-brand hover:underline">
                  Resend from Profile
                </Link>
              </p>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <BrandLoading fullscreen label="Verifying your email..." />
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}


