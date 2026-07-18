"use client";

import { ReactNode } from "react";
import { useDensity } from "@/lib/densityContext";

type ActionTone = "default" | "primary" | "success" | "warning" | "danger";

export interface InlineActionButton {
  label: string;
  icon: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  tone?: ActionTone;
}

interface Props {
  actions: InlineActionButton[];
}

const TONE_STYLES: Record<ActionTone, string> = {
  default: "text-text-muted hover:bg-surface-2 hover:text-text",
  primary: "text-primary hover:bg-primary/10",
  success: "text-success hover:bg-success/10",
  warning: "text-warning hover:bg-warning/10",
  danger: "text-danger hover:bg-danger/10",
};

export default function InlineActionButtons({ actions }: Props) {
  const { density } = useDensity();
  const buttonSizeClass = density === "compact" ? "h-7 w-7" : density === "expanded" ? "h-9 w-9" : "h-8 w-8";
  const iconSizeClass = density === "compact" ? "[&_svg]:h-3 [&_svg]:w-3" : density === "expanded" ? "[&_svg]:h-4 [&_svg]:w-4" : "[&_svg]:h-3.5 [&_svg]:w-3.5";

  return (
    <div className="isolate inline-flex overflow-hidden rounded-lg border border-border bg-surface-1 shadow-sm">
      {actions.map((action, index) => (
        <button
          key={`${action.label}-${index}`}
          type="button"
          onClick={action.onClick}
          disabled={action.disabled}
          aria-label={action.label}
          title={action.label}
          className={`flex items-center justify-center border-l border-border/70 transition-colors first:border-l-0 disabled:opacity-40 ${buttonSizeClass} ${iconSizeClass} ${
            TONE_STYLES[action.tone ?? "default"]
          }`}
        >
          {action.icon}
        </button>
      ))}
    </div>
  );
}


