"use client";
import { cn } from "@/lib/utils";
import { AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";
type AlertTone = "success" | "danger" | "warning" | "info";
const toneConfig: Record<AlertTone, { bg: string; border: string; text: string; Icon: React.ComponentType<{ className?: string }> }> = {
  success: { bg: "bg-success/10", border: "border-success/30", text: "text-success", Icon: CheckCircle },
  danger: { bg: "bg-danger/10", border: "border-danger/30", text: "text-danger", Icon: AlertCircle },
  warning: { bg: "bg-warning/10", border: "border-warning/30", text: "text-warning", Icon: AlertTriangle },
  info: { bg: "bg-info/10", border: "border-info/30", text: "text-info", Icon: Info },
};
interface AlertProps { tone: AlertTone; title?: string; children: React.ReactNode; className?: string; }
export function Alert({ tone, title, children, className }: AlertProps) {
  const config = toneConfig[tone]; const Icon = config.Icon;
  return (
    <div className={cn("flex items-start gap-3 rounded-xl border p-4", config.bg, config.border, className)}>
      <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", config.text)} />
      <div className="flex-1">
        {title && <p className={cn("text-sm font-semibold", config.text)}>{title}</p>}
        <p className="text-sm text-text-muted">{children}</p>
      </div>
    </div>
  );
}
