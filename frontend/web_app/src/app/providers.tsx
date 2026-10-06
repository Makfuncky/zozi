"use client";

import { useEffect } from "react";

import { fetchRbacCatalog } from "@shared/adminPermissions";

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    void fetchRbacCatalog();
  }, []);

  return <>{children}</>;
}
