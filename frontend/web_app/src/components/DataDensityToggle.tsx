"use client";

import { Rows3, AlignJustify, StretchVertical } from "@/lib/icons";
import { useDensity, type Density } from "@/lib/densityContext";

const OPTIONS: { value: Density; label: string; Icon: React.ElementType }[] = [
  { value: "compact", label: "Compact", Icon: Rows3 },
  { value: "normal",  label: "Normal",  Icon: StretchVertical },
  { value: "expanded", label: "Expanded", Icon: AlignJustify },
];

export default function DataDensityToggle() {
  const { density, setDensity } = useDensity();

  return (
    <div
      className="flex rounded-lg border border-border bg-surface-2 p-0.5"
      title="Data density"
      role="group"
      aria-label="Data density"
    >
      {OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          onClick={() => setDensity(value)}
          title={label}
          aria-label={`${label} density`}
          aria-pressed={density === value}
          className={`rounded-md p-1.5 transition-colors ${
            density === value
              ? "bg-surface text-text shadow-sm"
              : "text-text-muted hover:text-text"
          }`}
        >
          <Icon className="h-3.5 w-3.5" />
        </button>
      ))}
    </div>
  );
}


