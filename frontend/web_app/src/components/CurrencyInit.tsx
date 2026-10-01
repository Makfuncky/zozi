"use client";

import { useEffect, useRef } from "react";
import { useCurrencyStore } from "@/lib/currencyStore";

export default function CurrencyInit() {
	const detectFromIP = useCurrencyStore((state) => state.detectFromIP);
	const markHydrated = useCurrencyStore((state) => state.markHydrated);
	const hasRun = useRef(false);

	useEffect(() => {
		if (hasRun.current) return;
		hasRun.current = true;

		// Detect currency from IP (respects user selection if locked)
		void detectFromIP().finally(() => {
			// Mark as hydrated after detection completes
			// This triggers a re-render with the actual currency
			markHydrated();
		});
	}, [detectFromIP, markHydrated]);

	return null;
}
