"use client";

import { Button } from "@/components/ui/Button";

import { useState, useRef } from "react";
import { X, Plus } from "@/lib/icons";
import { BULK_COLOR_HEX_MAP, BULK_COLOR_PRESETS, normalizeDraftColorValue } from "../draftUtils";

interface ColorPickerFieldProps {
  /** Hidden-accessible input id for label association. */
  inputId: string;
  /** Comma-separated string of selected colors, e.g. "Black, Red". */
  value: string;
  /** Called whenever the selection changes. Receives the updated comma-separated string. */
  onChange: (value: string) => void;
}

function parseColors(value: string): string[] {
  return value
    .split(",")
    .map((color) => normalizeDraftColorValue(color))
    .filter(Boolean);
}

function formatColors(colors: string[]): string {
  return colors.join(", ");
}

export function ColorPickerField({ inputId, value, onChange }: ColorPickerFieldProps) {
  const [customEntry, setCustomEntry] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const selected = parseColors(value);

  const toggleColor = (color: string) => {
    const normalizedColor = normalizeDraftColorValue(color);
    if (!normalizedColor) return;
    const exists = selected.some(
      (selectedColor) => selectedColor.toLowerCase() === normalizedColor.toLowerCase(),
    );
    if (exists) {
      onChange(formatColors(selected.filter((selectedColor) => selectedColor.toLowerCase() !== normalizedColor.toLowerCase())));
    } else {
      onChange(formatColors([...selected, normalizedColor]));
    }
  };

  const addCustom = () => {
    const normalized = normalizeDraftColorValue(customEntry);
    if (!normalized) return;
    toggleColor(normalized);
    setCustomEntry("");
    inputRef.current?.focus();
  };

  return (
    <div className="space-y-2">
      {/* Hidden input keeps the value accessible for label association + testing */}
      <input
        id={inputId}
        type="text"
        aria-label="Color"
        readOnly
        value={value}
        className="sr-only"
        tabIndex={-1}
      />

      {/* Preset color swatches */}
      <div className="flex flex-wrap gap-2">
        {BULK_COLOR_PRESETS.map((color) => {
          const hex = BULK_COLOR_HEX_MAP[color] ?? "#cccccc";
          const isSelected = selected.some(
            (selectedColor) => selectedColor.toLowerCase() === color.toLowerCase(),
          );
          return (
            <button
              key={color}
              type="button"
              aria-label={color}
              aria-pressed={isSelected}
              title={color}
              onClick={() => toggleColor(color)}
              className={`h-7 w-7 shrink-0 rounded-full transition-all ${
                isSelected
                  ? "ring-2 ring-primary ring-offset-2 scale-110 shadow-md shadow-primary/25"
                  : "ring-1 ring-border/50 hover:ring-primary/40 hover:scale-105"
              }`}
              style={{ backgroundColor: hex }}
            />
          );
        })}
      </div>

      {/* Selected colors as removable chips */}
      {selected.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {selected.map((color) => {
            const hex = BULK_COLOR_HEX_MAP[color] ?? "#cccccc";
            return (
              <span
                key={color}
                className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary"
              >
                <span
                  className="h-3 w-3 shrink-0 rounded-full ring-1 ring-black/10"
                  style={{ backgroundColor: hex }}
                  aria-hidden="true"
                />
                {color}
                <Button variant="primary" className="inline-flex rounded-full p-px" type="button"
                  aria-label={`Remove ${color}`}
                  onClick={() => toggleColor(color)}
                >
                  <X className="h-2.5 w-2.5" />
                </Button>
              </span>
            );
          })}
        </div>
      ) : (
        <p className="text-[10px] text-text-faint">Select colors above — each becomes a variant combination axis.</p>
      )}

      {/* Custom color input */}
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={customEntry}
          onChange={(event) => setCustomEntry(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addCustom();
            }
          }}
          placeholder="Custom color…"
          className="theme-input h-8 flex-1 rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
        />
        <button
          type="button"
          onClick={addCustom}
          disabled={!customEntry.trim()}
          className="inline-flex h-8 items-center gap-1 rounded-xl border border-border px-3 text-xs font-semibold text-text-muted transition-colors hover:border-primary/40 hover:text-text disabled:opacity-40"
        >
          <Plus className="h-3 w-3" />
          Add
        </button>
      </div>
    </div>
  );
}


