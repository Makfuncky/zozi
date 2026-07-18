import { Suspense } from "react";
import BrandLoading from "@/components/BrandLoading";
import SocialAuthCallbackClient from "./SocialAuthCallbackClient";

export default function SocialAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-surface-base px-4 text-text">
          <div className="theme-card rounded-2xl border px-6 py-8 text-center text-sm">
            <BrandLoading label="Loading authentication..." />
          </div>
        </main>
      }
    >
      <SocialAuthCallbackClient />
    </Suspense>
  );
}



