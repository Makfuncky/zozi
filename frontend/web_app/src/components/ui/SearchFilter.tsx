"use client";
import * as React from "react";

type SearchFilterProps = {
  value?: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  className?: string;
  filters?: Array<{ key: string; label: string; value: string; options: Array<{ value: string; label: string }> }>;
};

export const SearchFilter: React.FC<SearchFilterProps> = ({ value, onChange, placeholder = "Search...", className = "" }) => (
  <div className={`flex items-center gap-2 ${className}`}>
    <input
      type="search"
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-sm outline-none focus:border-primary"
    />
  </div>
);
export default SearchFilter;
