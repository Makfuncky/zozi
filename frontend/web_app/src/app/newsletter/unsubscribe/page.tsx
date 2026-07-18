"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle, XCircle, Mail, AlertCircle } from "lucide-react";
import { apiFetch } from "@/lib/api";
import BrandLoading from "@/components/BrandLoading";

const MotionDiv: any = motion.div;

function UnsubscribeContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error" | "invalid">("loading");
  const [message, setMessage] = useState("");

  const router = useRouter();
  const token = searchParams?.get("token");
  const email = searchParams?.get("email");

  const handleUnsubscribe = useCallback(async () => {
    try {
      const response = await apiFetch("/email/unsubscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          token,
          email
        })
      });

      if (response.ok) {
        setStatus("success");
        setMessage("You have been successfully unsubscribed from our newsletter. We're sorry to see you go!");
      } else {
        const error = await response.json();
        setStatus("error");
        setMessage(error.detail || "Failed to unsubscribe. Please try again.");
      }
    } catch (error) {
      console.error("Unsubscribe error:", error);
      setStatus("error");
      setMessage("An error occurred while processing your request. Please try again later.");
    }
  }, [email, token]);

  useEffect(() => {
    if (!token || !email) {
      setStatus("invalid");
      setMessage("Invalid unsubscribe link. Please check your email for the correct link.");
      return;
    }

    handleUnsubscribe();
  }, [token, email, handleUnsubscribe]);

  const getStatusIcon = () => {
    switch (status) {
      case "success":
        return <CheckCircle className="theme-status-success mx-auto mb-4 h-16 w-16" />;
      case "error":
        return <XCircle className="theme-status-danger mx-auto mb-4 h-16 w-16" />;
      case "invalid":
        return <AlertCircle className="theme-status-warning mx-auto mb-4 h-16 w-16" />;
      default:
        return <BrandLoading size={72} className="pb-2" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "success":
        return "theme-status-success";
      case "error":
        return "theme-status-danger";
      case "invalid":
        return "theme-status-warning";
      default:
        return "text-text";
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-base px-4 text-text">
      <MotionDiv
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="theme-card w-full max-w-md rounded-lg border p-8 text-center"
      >
        {getStatusIcon()}

        <h1 className={`text-2xl font-bold mb-4 ${getStatusColor()}`}>
          {status === "loading" && "Processing..."}
          {status === "success" && "Unsubscribed Successfully"}
          {status === "error" && "Unsubscribe Failed"}
          {status === "invalid" && "Invalid Link"}
        </h1>

        <p className="mb-6 text-text-muted">
          {message}
        </p>

        {status === "success" && (
          <div className="theme-alert-success mb-6 rounded-lg p-4">
            <p className="text-sm">
              You will no longer receive promotional emails from ZOZI.
              You can always resubscribe from our website if you change your mind.
            </p>
          </div>
        )}

        {status === "error" && (
          <div className="theme-alert-danger mb-6 rounded-lg p-4">
            <p className="text-sm">
              If you're having trouble unsubscribing, please contact our support team at{" "}
              <a href="mailto:support@zozi.com" className="underline">
                support@zozi.com
              </a>
            </p>
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={() => router.push("/")}
            className="theme-btn-primary w-full rounded-lg px-4 py-2"
          >
            Continue Shopping
          </button>

          {status === "success" && (
            <button
              onClick={() => router.push("/newsletter")}
              className="theme-btn-secondary w-full rounded-lg border px-4 py-2"
            >
              Manage Email Preferences
            </button>
          )}
        </div>

        <div className="mt-8 border-t border-border pt-6">
          <div className="flex items-center justify-center text-sm text-text-faint">
            <Mail className="w-4 h-4 mr-2" />
            ZOZI Newsletter
          </div>
        </div>
      </MotionDiv>
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <Suspense
      fallback={
        <BrandLoading fullscreen label="Loading preferences..." className="p-4" />
      }
    >
      <UnsubscribeContent />
    </Suspense>
  );
}


