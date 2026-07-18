"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import { canAccessAdminEmailManagement } from "@shared/adminPermissions";

export default function AdminEmailDashboard() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !canAccessAdminEmailManagement(user?.role)) {
      router.push("/admin/login");
    } else {
      router.replace("/admin/communication?tab=email");
    }
  }, [authLoading, isLoggedIn, router, user?.role]);
  return null;
}
