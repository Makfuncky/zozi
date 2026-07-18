"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";

export default function AdminChatPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
      router.replace("/admin/login");
    } else {
      router.replace("/admin/communication?tab=chat");
    }
  }, [authLoading, isLoggedIn, router, user?.role]);
  return null;
}
