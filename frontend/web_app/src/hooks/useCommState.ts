"use client";

import { useState, useEffect } from "react";

/**
 * Watches `.comm-shell` CSS classes set by UnifiedInboxBridge and exposes
 * them as simple `loading` / `error` booleans.
 *
 * Pass the class prefix, e.g. `"comm-threads"` → watches
 * `comm-threads-loading` and `comm-threads-error`.
 *
 * Usage:
 * ```tsx
 * const { loading, error } = useCommState("comm-threads");
 * // → loading when .comm-shell has class "comm-threads-loading"
 * // → error   when .comm-shell has class "comm-threads-error"
 * ```
 */
export function useCommState(prefix: "comm-threads" | "comm-messages"): {
  loading: boolean;
  error: boolean;
} {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const shell = document.querySelector(".comm-shell");
    if (!shell) return;

    const loadingClass = `${prefix}-loading`;
    const errorClass = `${prefix}-error`;

    const mo = new MutationObserver(() => {
      setLoading(shell.classList.contains(loadingClass));
      setError(shell.classList.contains(errorClass));
    });
    mo.observe(shell, { attributes: true, attributeFilter: ["class"] });

    // Read initial state
    setLoading(shell.classList.contains(loadingClass));
    setError(shell.classList.contains(errorClass));

    return () => mo.disconnect();
  }, [prefix]);

  return { loading, error };
}
