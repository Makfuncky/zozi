"use client";

import { useEffect } from "react";
import { globalErrorHandler } from "@/lib/globalErrorHandler";
import { initErrorReporter } from "@/lib/errorReporter";

export default function ErrorHandlerInit() {
	useEffect(() => {
		globalErrorHandler.initialize();
		initErrorReporter();
	}, []);

	return null;
}


