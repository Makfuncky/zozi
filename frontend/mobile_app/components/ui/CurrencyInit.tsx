import { useEffect } from "react";
import { useCurrencyStore } from "@/lib/currencyStore";

export default function CurrencyInit() {
  const detectFromIP = useCurrencyStore((s) => s.detectFromIP);

  useEffect(() => {
    detectFromIP();
  }, [detectFromIP]);

  return null;
}
