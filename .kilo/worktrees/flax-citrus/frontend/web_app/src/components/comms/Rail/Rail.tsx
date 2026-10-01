"use client";

import { useMemo, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Inbox, MessageCircle, Users, Hash, Mail, Video,
  Contact2, FileText, AtSign, Shield, FileSearch,
  Search, Bell, BellOff, Pin, MoreHorizontal, Star,
} from "@/lib/icons";
import { useComm, type Modality, type ThreadSummary } from "../CommShell";
import { useDrag } from "../DragProvider";
import { useCommState } from "@/hooks/useCommState";
import EmailFolderTree from "./EmailFolderTree";
import ThreadContextMenu, { useContextMenu } from "./ThreadContextMenu";

// ── Density row height map ────────────────────────────────────────────────

const ROW_HEIGHTS: Record<string, string> = {
  compact: "py-1.5",
  normal: "py-2",
  expanded: "py-3",
};

// ── Modality Definitions ──────────────────────────────────────────────────

interface ModalityDef {
  key: Modality;
  label: string;
  icon: typeof Inbox;
}

const MODALITIES: ModalityDef[] = [
  { key: "inbox",      label: "Unified Inbox", icon: Inbox },
  { key: "direct",     label: "Direct",        icon: MessageCircle },
  { key: "groups",     label: "Groups",        icon: Users },
  { key: "channels",   label: "Channels",      icon: Hash },
  { key: "email",      label: "Email",         icon: Mail },
  { key: "meet",       label: "Meet",          icon: Video },
  { key: "contacts",   label: "Contacts",      icon: Contact2 },
  { key: "files",      label: "Files",         icon: FileText },
  { key: "mentions",   label: "@ Mentions",    icon: AtSign },
  { key: "security",   label: "Security/DLP",  icon: Shield },
  { key: "ediscovery", label: "eDiscovery",    icon: FileSearch },
];

// ── Transport Glyph ───────────────────────────────────────────────────────

const TRANSPORT_GLYPH: Record<string, typeof Inbox> = {
  chat: MessageCircle,
  group: Users,
  email: Mail,
  video: Video,
  contact: Contact2,
};

function TransportGlyph({ transport }: { transport: string }) {
  const Icon = TRANSPORT_GLYPH[transport] || MessageCircle;
  return <Icon className="w-3.5 h-3.5 text-text-faint shrink-0" />;
}

// ── Components ────────────────────────────────────────────────────────────

function ModalityIconStrip({
  modalities, active, onSelect, collapsed,
}: {
  modalities: ModalityDef[];
  active: Modality;
  onSelect: (m: Modality) => void;
  collapsed: boolean;
}) {
  return (
    <div className={`flex ${collapsed ? "flex-col items-center gap-1 py-2" : "items-center gap-1 px-2 py-1.5 border-b border-border"}`}>
      {modalities.map((m) => (
        <button
          key={m.key}
          onClick={() => onSelect(m.key)}
          data-active={m.key === active}
          className={`comm-icon-item relative ${collapsed ? "" : "flex-1 gap-2 px-3"} ${m.key === active ? "bg-primary/10 text-primary" : "text-text-muted hover:text-text hover:bg-surface-2"}`}
          title={collapsed ? m.label : undefined}
        >
          <m.icon className="w-4 h-4 shrink-0" />
          {!collapsed && (
            <span className="text-[11px] font-medium truncate">{m.label}</span>
          )}
          {m.key === active && !collapsed && (
            <motion.div layoutId="modality-pill" className="absolute inset-0 rounded-lg border border-primary/30 bg-primary/5" />
          )}
        </button>
      ))}
    </div>
  );
}

function ThreadRow({ thread, onSelect, active, density, onContextMenu }: {
  thread: ThreadSummary;
  onSelect: (t: ThreadSummary) => void;
  active: boolean;
  density: "compact" | "normal" | "expanded";
  onContextMenu?: (t: ThreadSummary, e: React.MouseEvent) => void;
}) {
  const { startDrag, endDrag } = useDrag();
  const rowHeight = ROW_HEIGHTS[density] || ROW_HEIGHTS.normal;

  const handleDragStart = useCallback(
    (e: React.DragEvent) => {
      startDrag({ type: "thread", thread }, e);
    },
    [thread, startDrag]
  );

  const handleContext = useCallback(
    (e: React.MouseEvent) => {
      if (thread.transport === "email" && onContextMenu) {
        onContextMenu(thread, e);
      }
    },
    [thread, onContextMenu]
  );

  return (
    <div
      onClick={() => onSelect(thread)}
      onContextMenu={handleContext}
      draggable
      onDragStart={handleDragStart}
      onDragEnd={endDrag}
      data-active={active}
      className={`comm-row group ${rowHeight} cursor-grab active:cursor-grabbing`}
    >
      {/* Avatar / glyph */}
      <div className="relative w-9 h-9 rounded-full bg-surface-2 flex items-center justify-center shrink-0 overflow-hidden">
        {thread.peerAvatar ? (
          <img src={thread.peerAvatar} alt="" className="w-full h-full object-cover" />
        ) : thread.transport === "group" || thread.transport === "email" ? (
          <div className="flex items-center justify-center w-full h-full text-text-muted">
            <TransportGlyph transport={thread.transport} />
          </div>
        ) : (
          <span className="text-[11px] font-bold text-text-muted">
            {thread.title.charAt(0).toUpperCase()}
          </span>
        )}
        {thread.transport === "chat" && (
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-surface bg-emerald-500 dot-online" />
        )}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[13px] font-semibold text-text truncate font-display">
            {thread.title}
          </span>
          <span className="text-[10px] text-text-faint tabular-nums shrink-0">
            {formatRelativeTime(thread.updatedAt)}
          </span>
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <TransportGlyph transport={thread.transport} />
          <span className="text-[11px] text-text-muted truncate flex-1">
            {thread.preview}
          </span>
          {thread.unread > 0 && (
            <span className="comm-unread-badge shrink-0 min-w-[18px] h-[18px] rounded-full bg-primary text-[9px] font-bold text-white flex items-center justify-center px-1">
              {thread.unread > 99 ? "99+" : thread.unread}
            </span>
          )}
          {thread.isPinned && <Pin className="w-3 h-3 text-text-faint shrink-0" />}
          {thread.isMuted && <BellOff className="w-3 h-3 text-text-faint shrink-0" />}
        </div>
      </div>

      {/* Quick actions on hover */}
      <div className="quick flex items-center gap-0.5 ml-1">
        <button className="p-1 rounded-md hover:bg-surface-2 text-text-faint hover:text-text transition-colors" title="More">
          <MoreHorizontal className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

// ── Main Rail Component ───────────────────────────────────────────────────

export default function CommRail() {
  const {
    modality, setModality, lens, setLens,
    railCollapsed,
    activeThread, setActiveThread,
    threads,
    density,
    activeFolder,
  } = useComm();

  const [filterText, setFilterText] = useState("");
  const { loading: isLoadingThreads, error: isErrorThreads } = useCommState("comm-threads");

  // ── Context menu state ──────────────────────────────────────────
  const { targetThread, position, openMenu, closeMenu } = useContextMenu();
  const [refreshKey, setRefreshKey] = useState(0);
  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
    window.dispatchEvent(new CustomEvent("comm-refetch"));
  }, []);

  // Apply lens filter
  const lensFiltered = useMemo(() => {
    if (lens === "unread") return threads.filter((t) => t.unread > 0);
    if (lens === "mentions") return threads.filter((t) => (t as any).mentions || false);
    if (lens === "starred") return threads.filter((t) => t.isPinned);
    return threads;
  }, [threads, lens]);

  // Apply modality filter
  const modalityFiltered = useMemo(() => {
    switch (modality) {
      case "inbox": return lensFiltered;
      case "direct": return lensFiltered.filter((t) => t.transport === "chat");
      case "groups": return lensFiltered.filter((t) => t.transport === "group" && t.channelType !== "channel");
      case "channels": return lensFiltered.filter((t) => t.transport === "group" && t.channelType === "channel");
      case "email":
        if (activeFolder) {
          return lensFiltered.filter(
            (t) => t.transport === "email" && t.folder === activeFolder
          );
        }
        return lensFiltered.filter((t) => t.transport === "email");
      case "mentions": return lensFiltered;
      default: return lensFiltered;
    }
  }, [lensFiltered, modality, activeFolder]);

  // Apply text filter
  const filtered = useMemo(() => {
    if (!filterText.trim()) return modalityFiltered;
    const q = filterText.toLowerCase();
    return modalityFiltered.filter(
      (t) => t.title.toLowerCase().includes(q) || t.preview.toLowerCase().includes(q)
    );
  }, [modalityFiltered, filterText]);

  // If collapsed, show only the icon strip
  if (railCollapsed) {
    return (
      <ModalityIconStrip
        modalities={MODALITIES}
        active={modality}
        onSelect={setModality}
        collapsed={true}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Modality strip */}
      <ModalityIconStrip
        modalities={MODALITIES}
        active={modality}
        onSelect={setModality}
        collapsed={false}
      />

      {/* Email folder tree — shown only in email modality */}
      {modality === "email" && <EmailFolderTree />}

      {/* Lens chips + local search */}
      <div className="px-2 py-2 border-b border-border space-y-2">
        <div className="flex items-center gap-1.5">
          {(["all", "unread", "mentions", "starred"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLens(l)}
              data-active={lens === l}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-colors ${
                lens === l
                  ? "text-primary bg-primary/10"
                  : "text-text-muted hover:text-text hover:bg-surface-2"
              }`}
            >
              {l === "all" ? "All" : l === "unread" ? "Unread" : l === "mentions" ? "@Me" : "★"}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-faint" />
          <input
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter conversations…"
            className="w-full rounded-lg border border-border bg-surface-1 pl-8 pr-3 py-1.5 text-[11px] text-text placeholder:text-text-faint focus:outline-none focus:border-primary/40 transition-colors"
          />
        </div>
      </div>

      {/* Loading skeleton */}
      {threads.length === 0 && isLoadingThreads && (
        <div className="flex-1 overflow-y-auto p-1.5 space-y-2" aria-label="Loading conversations">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-2 py-2 animate-pulse">
              <div className="w-9 h-9 rounded-full bg-surface-2 shrink-0" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-3/4 rounded bg-surface-2" />
                <div className="h-2.5 w-1/2 rounded bg-surface-2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {threads.length === 0 && isErrorThreads && (
        <div className="flex-1 flex flex-col items-center justify-center py-12 text-center px-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-danger/10 mb-3">
            <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-xs font-semibold text-text mb-1">Failed to load inbox</p>
          <p className="text-[10px] text-text-faint mb-3 max-w-[160px]">Could not fetch conversations. Check your connection.</p>
          <button
            onClick={() => {
              window.dispatchEvent(new CustomEvent("comm-refetch"));
              document.querySelector(".comm-shell")?.classList.remove("comm-threads-error");
              document.querySelector(".comm-shell")?.classList.add("comm-threads-loading");
            }}
            className="theme-btn-primary rounded-lg px-3 py-1.5 text-[10px] font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Thread list */}
      <div className={`flex-1 overflow-y-auto p-1.5 space-y-0.5 ${threads.length === 0 ? 'hidden' : ''}`}>
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Inbox className="w-10 h-10 text-text-faint/30 mb-2" />
            <p className="text-xs text-text-muted">No conversations yet</p>
            <p className="text-[10px] text-text-faint mt-0.5">Select a modality or start a new conversation</p>
          </div>
        ) : (
          <>
            {filtered.map((thread) => (
              <ThreadRow
                key={thread.id}
                thread={thread}
                active={activeThread?.id === thread.id}
                onSelect={setActiveThread}
                density={density}
                onContextMenu={openMenu}
              />
            ))}
            {/* Right-click context menu for email threads */}
            {targetThread && (
              <ThreadContextMenu
                thread={targetThread}
                position={position}
                onClose={closeMenu}
                onMoved={handleRefresh}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Utility ───────────────────────────────────────────────────────────────

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
