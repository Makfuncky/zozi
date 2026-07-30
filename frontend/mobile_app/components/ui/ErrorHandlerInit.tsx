import "@/sentry.config";
import { useEffect } from "react";
import { globalErrorHandler } from "@/lib/globalErrorHandler";
import { initErrorReporter, stopErrorReporter } from "@/lib/errorReporter";

export default function ErrorHandlerInit() {
  useEffect(() => {
    globalErrorHandler.initialize();
    initErrorReporter();
    return () => {
      stopErrorReporter();
    };
  }, []);

  return null;
}
