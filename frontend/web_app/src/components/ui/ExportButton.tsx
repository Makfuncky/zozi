"use client";
import * as React from "react";

type ExportButtonProps = {
  onExport?: (format: string) => void;
  formats?: string[];
  className?: string;
  label?: string;
};

export const ExportButton: React.FC<ExportButtonProps> = ({ onExport, formats = ["csv"], className = "", label = "Export" }) => (
  <div className={`flex gap-2 ${className}`}>
    {formats.map((f) => (
      <button
        key={f}
        type="button"
        onClick={() => onExport?.(f)}
        className="rounded-lg border border-border px-3 py-1 text-xs hover:bg-surface-2"
      >
        {label} {f.toUpperCase()}
      </button>
    ))}
  </div>
);
export default ExportButton;
