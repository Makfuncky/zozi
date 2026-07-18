"use client";

import { useEffect } from "react";
import { useLocaleStore } from "@/lib/localeStore";

export default function LocaleInit() {
  const hydrateLocale = useLocaleStore((state) => state.hydrateLocale);

  useEffect(() => {
    hydrateLocale();
  }, [hydrateLocale]);

  return null;
}


