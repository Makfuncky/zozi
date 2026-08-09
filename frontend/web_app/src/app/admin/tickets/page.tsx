"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminTicketsPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/admin/resolution?section=tickets");
  }, [router]);
  return null;
}
