"use client";

import { useMemo } from "react";
import { Wifi, Keyboard } from "@/lib/icons";
import { useComm, type WsStatus } from "./CommShell";

// ── Status indicator config ───────────────────────────────────────────────

const STATUS_CONFIG: Record<WsStatus, {
  dot: string;
  ring: string;
  label: string;
}> = {
  connected: {
    dot: "bg-emerald-500",
    ring: "bg-emerald-500",
    label: "Connected",
  },
  reconnecting: {
    dot: "bg-amber-400",
    ring: "bg-amber-400",
    label: "Reconnecting…",
  },
  disconnected: {
    dot: "bg-red-400",
    ring: "bg-red-400",
    label: "Disconnected",
  },
};

// ── Component ─────────────────────────────────────────────────────────────

export default function StatusDock() {
  const { modality, wsStatus } = useComm();
  const config = STATUS_CONFIG[wsStatus];

  const label = useMemo(() => {
    switch (modality) {
      case "inbox": return "Unified Inbox";
      case "direct": return "Direct Messages";
      case "groups": return "Groups";
      case "channels": return "Channels";
      case "email": return "Email";
      case "meet": return "Video Meet";
      case "contacts": return "Contacts";
      case "files": return "Shared Files";
      case "mentions": return "@ Mentions";
      case "security": return "Security / DLP";
      case "ediscovery": return "eDiscovery";
      default: return "Communication Hub";
    }
  }, [modality]);

  return (
    <>
      {/* Status dot with ping animation only when connected */}
      <span className="relative flex w-2 h-2">
        {wsStatus === "connected" && (
          <span className={`absolute inset-0 rounded-full ${config.ring} animate-ping opacity-40`} />
        )}
        {wsStatus === "reconnecting" && (
          <span className={`absolute inset-0 rounded-full ${config.ring} animate-pulse opacity-60`} />
        )}
        <span className={`relative w-2 h-2 rounded-full ${config.dot}`} />
      </span>
      <span className="text-[10px]">{config.label}</span>
      <span className="mx-1.5 text-text-faint">·</span>
      <span className="text-[10px]">{label}</span>
      <span className="ml-auto flex items-center gap-1 text-[9px] text-text-faint">
        <Keyboard className="w-2.5 h-2.5" />
        ⌘/ for shortcuts
      </span>
    </>
  );
}
