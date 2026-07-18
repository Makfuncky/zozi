"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminModerationPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/admin/resolution?section=moderation");
  }, [router]);
  return null;
}
