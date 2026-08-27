import { DensityProvider } from "@/lib/densityContext";
import ErrorBoundary from "@/components/ErrorBoundary";

export default function SupplierRootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <DensityProvider>{children}</DensityProvider>
    </ErrorBoundary>
  );
}
