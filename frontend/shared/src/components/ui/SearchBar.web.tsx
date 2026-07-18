import React from "react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  onSubmit?: () => void;
  onFocus?: () => void;
  onBlur?: () => void;
}

export default function SearchBar({ value, onChange, onClear, placeholder, onSubmit, onFocus, onBlur }: SearchBarProps) {
  return (
    <div style={styles.container}>
      <span style={styles.icon}>🔍</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSubmit?.()}
        onFocus={() => onFocus?.()}
        onBlur={() => onBlur?.()}
        placeholder={placeholder ?? "Search products..."}
        style={styles.input}
      />
      {!!value && (
        <button onClick={onClear} style={styles.clearButton}>✕</button>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    backgroundColor: "#0f172a",
    border: "1px solid #1f2937",
    borderRadius: 16,
    padding: "10px 12px",
    gap: "8px",
  },
  icon: {
    color: "#9ca3af",
    fontSize: 18,
  },
  input: {
    flex: 1,
    color: "#f8fafc",
    backgroundColor: "transparent",
    border: "none",
    outline: "none",
    fontSize: 15,
    minWidth: "120px",
  },
  clearButton: {
    border: "none",
    background: "transparent",
    color: "#9ca3af",
    cursor: "pointer",
    fontSize: 14,
  },
};
