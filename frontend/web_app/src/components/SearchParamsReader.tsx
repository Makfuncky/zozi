"use client";

import React from "react";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function SearchParamsInner({ children }: { children: (searchParams: URLSearchParams | null) => React.ReactNode }) {
  const searchParams = useSearchParams();
  return children(searchParams);
}

export function SearchParamsReader({ children }: { children: (searchParams: URLSearchParams | null) => React.ReactNode }) {
  return (
    <Suspense fallback={null}>
      <SearchParamsInner>{children}</SearchParamsInner>
    </Suspense>
  );
}