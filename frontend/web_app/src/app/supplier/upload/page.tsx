"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function UploadRedirectPage() {
  const router = useRouter();
  useEffect(() => { router.replace("/supplier/bulk"); }, [router]);
  return null;
}


