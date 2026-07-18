"use client";

import { useEffect } from "react";
import { useCurrencyStore } from "@/lib/currencyStore";

export default function CurrencyInit() {
	const detectFromIP = useCurrencyStore((state) => state.detectFromIP);

	useEffect(() => {
		void detectFromIP();
	}, [detectFromIP]);

	return null;
}


