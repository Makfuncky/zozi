"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

interface SupplierRouteRedirectProps {
  href: string;
}

export default function SupplierRouteRedirect({ href }: SupplierRouteRedirectProps) {
  const router = useRouter();

  useEffect(() => {
    router.replace(href);
  }, [href, router]);

  return null;
}


