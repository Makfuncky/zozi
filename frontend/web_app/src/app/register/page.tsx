import { Suspense } from "react";
import BrandLoading from "@/components/BrandLoading";
import RegisterClient from "./RegisterClient";

export default function RegisterPage() {
  return (
    <Suspense fallback={<BrandLoading fullscreen label="Loading registration..." />}>
      <RegisterClient />
    </Suspense>
  );
}
