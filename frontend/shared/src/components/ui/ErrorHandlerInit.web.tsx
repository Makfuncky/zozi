"use client";

import { useEffect } from "react";
import { globalErrorHandler } from "@/lib/globalErrorHandler";

export default function ErrorHandlerInit() {
  useEffect(() => {
    globalErrorHandler.initialize();
  }, []);

  return null;
}