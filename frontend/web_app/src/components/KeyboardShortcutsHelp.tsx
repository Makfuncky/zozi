"use client";

import { useEffect, useMemo, useState } from "react";
import QuickDetailModal from "@/components/QuickDetailModal";

type HelpScope = "admin" | "supplier" | "logistics";

const SCOPE_SHORTCUTS: Record<HelpScope, Array<{ key: string; description: string }>> = {
  admin: [
    { key: "?", description: "Open keyboard shortcuts help" },
    { key: "j", description: "Next page on list workspaces" },
    { key: "k", description: "Previous page on list workspaces" },
    { key: "Ctrl + Enter", description: "Send inline reply in tickets" },
  ],
  supplier: [
    { key: "?", description: "Open keyboard shortcuts help" },
    { key: "Quick Shipment", description: "Open the parcel-record modal from the header" },
    { key: "Expand order", description: "Open the full supplier parcel workflow" },
  ],
  logistics: [
    { key: "?", description: "Open keyboard shortcuts help" },
    { key: "j", description: "Next shipment page" },
    { key: "k", description: "Previous shipment page" },
    { key: "Scan QR", description: "Jump into the scan workspace for handoff confirmation" },
  ],
};

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

export default function KeyboardShortcutsHelp({ scope }: { scope: HelpScope }) {
  const [open, setOpen] = useState(false);
  const shortcuts = useMemo(() => SCOPE_SHORTCUTS[scope], [scope]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isTypingTarget(event.target)) return;
      if (event.key === "?" || (event.key === "/" && event.shiftKey)) {
        event.preventDefault();
        setOpen(true);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open keyboard shortcuts help"
        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface-1 text-xs font-semibold text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
      >
        ?
      </button>

      <QuickDetailModal
        open={open}
        onClose={() => setOpen(false)}
        title="Keyboard Shortcuts"
        subtitle="Available shortcuts for this workspace"
        widthClassName="max-w-xl"
      >
        <div className="space-y-2">
          {shortcuts.map((item) => (
            <div key={`${scope}-${item.key}`} className="flex items-center justify-between gap-4 rounded-xl border border-border bg-surface-1 px-4 py-3">
              <span className="rounded-lg bg-surface px-2 py-1 text-xs font-semibold text-text">{item.key}</span>
              <span className="text-sm text-text-muted">{item.description}</span>
            </div>
          ))}
        </div>
      </QuickDetailModal>
    </>
  );
}


