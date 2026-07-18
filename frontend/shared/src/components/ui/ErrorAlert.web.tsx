import React from "react";
import { cn } from "../../utils";

interface ErrorAlertProps {
  message: string;
  type?: "error" | "success" | "info";
}

const STYLES = {
  error: "bg-danger/10 border border-danger/30 text-danger",
  success: "bg-success/10 border border-success/30 text-success",
  info: "bg-info/10 border border-info/30 text-info",
};

export default function ErrorAlert({
  message,
  type = "error",
}: ErrorAlertProps) {
  if (!message) return null;
  return (
    <div className={cn("mb-4 p-4 rounded-xl", STYLES[type])}>
      <p className="text-sm">{message}</p>
    </div>
  );
}