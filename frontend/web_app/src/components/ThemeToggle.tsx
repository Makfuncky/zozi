"use client";

import { memo, useEffect, useState } from "react";
import { useThemeStore } from "@/lib/themeStore";

interface ThemeToggleButtonProps {
  theme: "light" | "dark";
  onToggle: () => void;
}

const ThemeToggleButton = memo(function ThemeToggleButton({ theme, onToggle }: ThemeToggleButtonProps) {
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
});

export default memo(function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    // Render a stable placeholder that matches the server output to avoid hydration mismatch.
    return (
      <button
        className="group rounded-lg border border-border bg-surface-1 p-2 text-text-muted transition-colors hover:border-border-light hover:bg-surface-2"
        aria-label="Toggle theme"
        disabled
      />
    );
  }

  return <ThemeToggleButton theme={theme} onToggle={toggleTheme} />;
});


