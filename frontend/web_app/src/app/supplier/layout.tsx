import { DensityProvider } from "@/lib/densityContext";

export default function SupplierRootLayout({ children }: { children: React.ReactNode }) {
  return <DensityProvider>{children}</DensityProvider>;
}


