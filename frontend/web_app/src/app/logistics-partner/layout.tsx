import { DensityProvider } from "@/lib/densityContext";
import ErrorBoundary from "@/components/ErrorBoundary";

export default function LogisticsPartnerRootLayout({ children }: { children: React.ReactNode }) {
  return <DensityProvider><ErrorBoundary>{children}</ErrorBoundary></DensityProvider>;
}
