import { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "@/lib/icons";

interface SearchableComboBoxProps {
  inputId: string;
  ariaLabel: string;
  value: string;
  options: string[];
  placeholder: string;
  searchPlaceholder: string;
  emptyLabel: string;
  disabled?: boolean;
  allowCustomEntry?: boolean;
  onChange: (value: string) => void;
}

export function SearchableComboBox({
  inputId,
  ariaLabel,
  value,
  options,
  placeholder,
  searchPlaceholder,
  emptyLabel,
  disabled = false,
  allowCustomEntry = false,
  onChange,
}: SearchableComboBoxProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const normalizedValue = value.trim();
  const filteredOptions = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return options;
    return options.filter((option) => option.toLowerCase().includes(normalizedQuery));
  }, [options, query]);
  const hasExactMatch = options.some((option) => option.toLowerCase() === query.trim().toLowerCase());
  const showCustomAction = allowCustomEntry && query.trim().length > 0 && !hasExactMatch;

  useEffect(() => {
    if (!open) {
      setQuery("");
      return;
    }
    const timeoutId = window.setTimeout(() => {
      searchInputRef.current?.focus();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const handleSelect = (nextValue: string) => {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        id={inputId}
        type="button"
        role="combobox"
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-controls={`${inputId}-listbox`}
        disabled={disabled}
        onClick={() => {
          if (disabled) return;
          setOpen((current) => !current);
        }}
        className="theme-input flex h-9 w-full items-center justify-between rounded-xl border px-3 text-left text-xs transition-colors focus:border-primary focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className={normalizedValue ? "text-text" : "text-text-faint"}>{normalizedValue || placeholder}</span>
        <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-text-faint transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open ? (
        <div className="absolute left-0 right-0 top-[calc(100%+6px)] z-30 overflow-hidden rounded-2xl border border-border bg-surface-base shadow-lg shadow-black/10">
          <div className="border-b border-border p-2.5">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
              <input
                ref={searchInputRef}
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={searchPlaceholder}
                className="theme-input h-9 w-full rounded-xl border px-9 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div id={`${inputId}-listbox`} role="listbox" className="max-h-56 overflow-y-auto py-1">
            {filteredOptions.map((option) => {
              const active = option.toLowerCase() === normalizedValue.toLowerCase();
              return (
                <button
                  key={option}
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => handleSelect(option)}
                  className={`flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition-colors ${active ? "bg-primary/10 text-primary" : "text-text-muted hover:bg-surface-2 hover:text-text"}`}
                >
                  <span className="flex-1">{option}</span>
                  {active ? <Check className="h-3.5 w-3.5 shrink-0" /> : null}
                </button>
              );
            })}

            {showCustomAction ? (
              <button
                type="button"
                onClick={() => handleSelect(query.trim())}
                className="flex w-full items-center gap-2 border-t border-border px-3 py-2 text-left text-xs font-semibold text-text transition-colors hover:bg-surface-2"
              >
                <span className="flex-1">Use "{query.trim()}"</span>
              </button>
            ) : null}

            {filteredOptions.length === 0 && !showCustomAction ? (
              <div className="px-3 py-2 text-xs text-text-faint">{emptyLabel}</div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}


