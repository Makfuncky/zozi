"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/useAuth";

export default function LogisticsPartnerIndexPage() {
  const router = useRouter();
  const { user, isLoading, isLoggedIn } = useAuth();

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (isLoggedIn && user?.role === "logistics_partner") {
      router.replace("/logistics-partner/dashboard");
      return;
    }
    router.replace("/logistics-partner/login");
  }, [isLoading, isLoggedIn, user?.role, router]);

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="theme-card p-6 text-center text-sm theme-text-muted">
        <span className="loading loading-spinner loading-md align-middle mr-2" aria-hidden />
        Routing to the logistics partner portal&hellip;
      </div>
    </main>
  );
}
