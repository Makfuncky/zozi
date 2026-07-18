import React from "react";

interface ThemeToggleProps {
  theme: "light" | "dark";
  onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  return (
    <button
      onClick={onToggle}
      className="group rounded-lg border border-border bg-surface-1 p-2 text-text-muted transition-colors hover:border-border-light hover:bg-surface-2"
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      type="button"
    >
      {theme === "dark" ? "☀️" : "🌙"}
    </button>
  );
}
