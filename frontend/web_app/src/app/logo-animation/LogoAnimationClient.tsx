"use client";

import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import BrandLoading from "@/components/BrandLoading";

const LogoAnimation = dynamic(
  () => import("@shared/logo/LogoAnimation"),
  { ssr: false }
);

function AnimationWrapper() {
  const params  = useSearchParams();
  const theme   = params?.get("theme") === "light" ? "light" : "dark";
  const tagline = params?.get("tagline") ?? "Trust Delivered";

  return (
    <LogoAnimation
      theme={theme}
      tagline={tagline}
      className="w-screen h-screen"
    />
  );
}

export default function LogoAnimationClient() {
  return (
    <Suspense
      fallback={
        <BrandLoading fullscreen className="bg-[#060e1c]" />
      }
    >
      <AnimationWrapper />
    </Suspense>
  );
}


