"use client";

import { Shield, ShieldCheck } from "@/lib/icons";
import { useComm } from "../../CommShell";

export default function B2BMasked() {
  const { activeThread } = useComm();

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Shield className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-base font-bold text-text mb-2">
          {activeThread?.title || "Masked B2B Conversation"}
        </h2>
        <div className="flex items-center justify-center gap-1.5 text-[11px] text-text-muted mb-3">
          <ShieldCheck className="w-3.5 h-3.5 text-primary" />
          <span>End-to-end masked · Proxy active</span>
        </div>
        <p className="text-xs text-text-muted">
          This conversation is routed through a masked proxy channel. The true
          identity of the external party is protected.
        </p>
        <button className="mt-4 px-3 py-1.5 rounded-lg bg-surface-2 text-[11px] text-text-muted hover:text-text hover:bg-surface-3 transition-colors">
          Reveal contact (requires authorization)
        </button>
      </div>
    </div>
  );
}
