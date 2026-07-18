"use client";

import AdminRouteRedirect from "@/components/AdminRouteRedirect";

export default function ReturnsRedirectPage() {
  return <AdminRouteRedirect href="/admin/orders?section=returns" />;
}


