import { DensityProvider } from "@/lib/densityContext";

export default function LogisticsPartnerRootLayout({ children }: { children: React.ReactNode }) {
  return <DensityProvider>{children}</DensityProvider>;
}


