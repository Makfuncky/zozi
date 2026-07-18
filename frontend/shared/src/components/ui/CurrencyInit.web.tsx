"use client";
/**
 * CurrencyInit — runs once on app mount to auto-detect the user's GCC currency
 * from their IP address. Renders nothing visible.
 */
import { useEffect } from "react";
import { useCurrencyStore } from "@/lib/currencyStore";

export default function CurrencyInit() {
  const detectFromIP = useCurrencyStore((s) => s.detectFromIP);
  useEffect(() => {
    detectFromIP();
  }, [detectFromIP]);
  return null;
}