"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

interface AdminRouteRedirectProps {
  href: string;
}

export default function AdminRouteRedirect({ href }: AdminRouteRedirectProps) {
  const router = useRouter();

  useEffect(() => {
    router.replace(href);
  }, [href, router]);

  return null;
}


