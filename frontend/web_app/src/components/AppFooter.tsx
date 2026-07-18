"use client";

import { usePathname } from "next/navigation";
import Footer from "@/components/Footer";

// The storefront Footer is marketing chrome that doesn't belong below the
// panel shells (admin / supplier / logistics). Suppress it on those routes,
// where PanelShell already provides the full panel layout.
export default function AppFooter() {
  const pathname = usePathname();
  const isPanelRoute =
    !!pathname &&
    ["/admin", "/supplier", "/logistics-partner"].some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
    );
  if (isPanelRoute) return null;
  return <Footer />;
}
