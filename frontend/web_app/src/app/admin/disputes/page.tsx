"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminDisputesPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/admin/resolution?section=disputes");
  }, [router]);
  return null;
}
