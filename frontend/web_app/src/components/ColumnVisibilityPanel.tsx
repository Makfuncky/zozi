"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Eye } from "@/lib/icons";

export interface ColumnVisibilityOption {
  key: string;
  label: string;
  visible: boolean;
  locked?: boolean;
}

interface Props {
  columns: ColumnVisibilityOption[];
  onToggle: (key: string) => void;
  align?: "left" | "right";
}

export default function ColumnVisibilityPanel({ columns, onToggle, align = "right" }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label="Toggle visible columns"
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs font-medium text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
      >
        <Eye className="h-3.5 w-3.5" />
        Columns
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          className={`glass-dropdown absolute top-full z-[999] mt-2 min-w-52 rounded-xl p-2 ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">
            Visible Columns
          </p>
          <div className="space-y-1">
            {columns.map((column) => (
              <label
                key={column.key}
                className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs transition-colors ${
                  column.locked ? "cursor-not-allowed text-text-faint" : "cursor-pointer text-text hover:bg-surface-2"
                }`}
              >
                <input
                  type="checkbox"
                  checked={column.visible}
                  disabled={column.locked}
                  onChange={() => onToggle(column.key)}
                  className="h-3.5 w-3.5 rounded accent-primary"
                />
                <span>{column.label}</span>
                {column.locked ? <span className="ml-auto text-[10px] uppercase text-text-faint">Fixed</span> : null}
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


