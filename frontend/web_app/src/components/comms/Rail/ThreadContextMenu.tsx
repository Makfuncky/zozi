"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import {
  Inbox, Send, Archive, Trash2, Star, FileText,
  Check, Loader2, ChevronRight,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import type { ThreadSummary } from "../CommShell";

// ── Types ──────────────────────────────────────────────────────────────────

interface FolderDef {
  id: number;
  name: string;
  folder_type: string;
  icon: string | null;
  sort_order: number;
  is_system: boolean;
  count: number;
  unread: number;
}

interface MenuPosition {
  x: number;
  y: number;
}

// ── Icons per folder name ──────────────────────────────────────────────────

const FOLDER_ICONS: Record<string, typeof Inbox> = {
  inbox: Inbox,
  sent: Send,
  drafts: Star,
  archive: Archive,
  trash: Trash2,
  starred: Star,
};

function getIcon(name: string): typeof Inbox {
  const key = name.toLowerCase();
  return FOLDER_ICONS[key] || FileText;
}

// ── Props ──────────────────────────────────────────────────────────────────

interface ThreadContextMenuProps {
  thread: ThreadSummary;
  position: MenuPosition;
  onClose: () => void;
  onMoved: () => void;
}

// ── Component ──────────────────────────────────────────────────────────────

export default function ThreadContextMenu({
  thread,
  position,
  onClose,
  onMoved,
}: ThreadContextMenuProps) {
  const [folders, setFolders] = useState<FolderDef[]>([]);
  const [loading, setLoading] = useState(true);
  const [movingId, setMovingId] = useState<number | null>(null);
  const [doneId, setDoneId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // ── Fetch folders on mount ────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch("/email-gateway/folders");
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        const data = await parseJsonResponse(res);
        if (!cancelled) setFolders(data.folders || []);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ── Move email to folder ──────────────────────────────────────────────
  const handleMove = useCallback(
    async (folderId: number) => {
      setMovingId(folderId);
      setError(null);
      const emailId = parseInt(thread.id, 10);
      if (Number.isNaN(emailId)) {
        setError("Invalid email ID");
        setMovingId(null);
        return;
      }
      try {
        const res = await apiFetch(`/email-gateway/folders/${emailId}/move`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ folder_id: folderId }),
        });
        if (!res.ok) {
          const errData = await parseJsonResponse(res);
          throw new Error(errData?.detail || `Server error ${res.status}`);
        }
        setDoneId(folderId);
        setTimeout(() => {
          onClose();
          onMoved();
        }, 400);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Move failed");
        setMovingId(null);
      }
    },
    [thread.id, onClose, onMoved]
  );

  // ── Click outside / Escape to close ──────────────────────────────────
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKey);
    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [onClose]);

  // ── Clamp position to viewport ───────────────────────────────────────
  const adjustedPosition = { ...position };
  if (typeof window !== "undefined") {
    adjustedPosition.x = Math.min(adjustedPosition.x, window.innerWidth - 220);
    adjustedPosition.y = Math.min(adjustedPosition.y, window.innerHeight - 300);
  }

  return (
    <div
      ref={menuRef}
      className="fixed z-50 w-[200px] rounded-xl border border-border bg-surface shadow-xl backdrop-blur-xl overflow-hidden"
      style={{ left: adjustedPosition.x, top: adjustedPosition.y }}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-border bg-surface-1/50">
        <p className="text-[11px] font-semibold text-text truncate">
          {thread.title}
        </p>
        <p className="text-[9px] text-text-faint">Move to folder</p>
      </div>

      {/* Folder list */}
      <div className="max-h-[220px] overflow-y-auto p-1">
        {loading && (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="w-4 h-4 text-text-muted animate-spin" />
          </div>
        )}

        {error && (
          <div className="px-2 py-3 text-center">
            <p className="text-[10px] text-danger">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-1 text-[9px] text-text-muted hover:text-text underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {!loading && !error && folders.length === 0 && (
          <div className="px-2 py-3 text-center">
            <p className="text-[10px] text-text-faint">No folders found</p>
          </div>
        )}

        {!loading &&
          folders.map((f) => {
            const Icon = getIcon(f.name);
            const isMoving = movingId === f.id;
            const isDone = doneId === f.id;

            return (
              <button
                key={f.id}
                onClick={() => !isMoving && !isDone && handleMove(f.id)}
                disabled={isMoving || isDone}
                className={`flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-[11px] font-medium transition-all ${
                  isDone
                    ? "bg-emerald-500/10 text-emerald-600"
                    : "text-text hover:bg-surface-2 disabled:opacity-50"
                }`}
              >
                {isMoving ? (
                  <Loader2 className="w-3.5 h-3.5 shrink-0 animate-spin" />
                ) : isDone ? (
                  <Check className="w-3.5 h-3.5 shrink-0 text-emerald-500" />
                ) : (
                  <Icon className="w-3.5 h-3.5 shrink-0 text-text-muted" />
                )}
                <span className="truncate flex-1 text-left capitalize">
                  {f.name}
                </span>
                <span className="text-[9px] text-text-faint tabular-nums">
                  {f.count || ""}
                </span>
                {!isMoving && !isDone && (
                  <ChevronRight className="w-3 h-3 text-text-faint opacity-0 group-hover:opacity-100" />
                )}
              </button>
            );
          })}
      </div>
    </div>
  );
}

// ── Hook to manage context menu state ──────────────────────────────────────

export function useContextMenu() {
  const [menuState, setMenuState] = useState<{
    thread: ThreadSummary | null;
    position: MenuPosition;
  }>({ thread: null, position: { x: 0, y: 0 } });

  const open = useCallback((thread: ThreadSummary, e: React.MouseEvent) => {
    e.preventDefault();
    setMenuState({ thread, position: { x: e.clientX, y: e.clientY } });
  }, []);

  const close = useCallback(() => {
    setMenuState({ thread: null, position: { x: 0, y: 0 } });
  }, []);

  return {
    targetThread: menuState.thread,
    position: menuState.position,
    openMenu: open,
    closeMenu: close,
  };
}
