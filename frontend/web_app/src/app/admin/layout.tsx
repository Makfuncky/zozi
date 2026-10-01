import type { Metadata } from "next";
import { Suspense } from "react";
import BrandLoading from "@/components/BrandLoading";
import { DensityProvider } from "@/lib/densityContext";
import { AdminCountryProvider } from "@/lib/useAdminCountry";
import ErrorBoundary from "@/components/ErrorBoundary";

export const metadata: Metadata = {
  title: "Admin Panel | ZOZI",
  description: "ZOZI platform management",
};

export default function AdminRootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <DensityProvider>
        <AdminCountryProvider>
          <Suspense fallback={<BrandLoading fullscreen label="Loading admin..." className="p-8" />}>
            {children}
          </Suspense>
        </AdminCountryProvider>
      </DensityProvider>
    </ErrorBoundary>
  );
}
