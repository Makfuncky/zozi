"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Inbox, Send, Archive, Trash2, Star, Plus, X, ChevronDown,
  FileText, FileCheck, Loader2, Edit3,
} from "@/lib/icons";
import { useComm } from "../CommShell";
import { apiFetch, parseJsonResponse } from "@/lib/api";

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

const FOLDER_ICONS: Record<string, typeof Inbox> = {
  inbox: Inbox,
  sent: Send,
  drafts: Edit3,
  archive: Archive,
  trash: Trash2,
  starred: Star,
};

function getFolderIcon(folder: FolderDef): typeof Inbox {
  const name = folder.name.toLowerCase();
  if (FOLDER_ICONS[name]) return FOLDER_ICONS[name];
  return folder.is_system ? FileText : FileCheck;
}

// ── Component ──────────────────────────────────────────────────────────────

export default function EmailFolderTree() {
  const { activeFolder, setActiveFolder } = useComm();
  const [folders, setFolders] = useState<FolderDef[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const renameInputRef = useRef<HTMLInputElement>(null);

  // ── Fetch folders ──────────────────────────────────────────────────
  const fetchFolders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch("/email-gateway/folders");
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await parseJsonResponse(res);
      setFolders(data.folders || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load folders");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFolders();
  }, [fetchFolders]);

  // ── Create folder ──────────────────────────────────────────────────
  const handleCreate = useCallback(async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    try {
      const res = await apiFetch("/email-gateway/folders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      await parseJsonResponse(res);
      setShowCreateForm(false);
      setNewName("");
      await fetchFolders();
    } catch (err) {
      console.error("Failed to create folder:", err);
    } finally {
      setCreating(false);
    }
  }, [newName, fetchFolders]);

  // ── Rename folder (double-click) ───────────────────────────────────
  const startRename = useCallback((folder: FolderDef) => {
    setRenamingId(folder.id);
    setRenameValue(folder.name);
    // Focus the input after React renders it
    setTimeout(() => renameInputRef.current?.focus(), 50);
  }, []);

  const handleRename = useCallback(async () => {
    const name = renameValue.trim();
    if (!name || renamingId === null) {
      setRenamingId(null);
      return;
    }
    try {
      const res = await apiFetch(`/email-gateway/folders/${renamingId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) {
        const errData = await parseJsonResponse(res);
        console.error("Rename failed:", errData?.detail || res.statusText);
      }
      setRenamingId(null);
      await fetchFolders();
    } catch (err) {
      console.error("Rename failed:", err);
      setRenamingId(null);
    }
  }, [renameValue, renamingId, fetchFolders]);

  const cancelRename = useCallback(() => {
    setRenamingId(null);
    setRenameValue("");
  }, []);

  // ── Delete folder ──────────────────────────────────────────────────
  const handleDelete = useCallback(
    async (folderId: number, e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        const res = await apiFetch(`/email-gateway/folders/${folderId}`, {
          method: "DELETE",
        });
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        await fetchFolders();
      } catch (err) {
        console.error("Failed to delete folder:", err);
      }
    },
    [fetchFolders]
  );

  // ── Loading state ──────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="px-3 py-2">
        <div className="flex items-center gap-2 text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">
          <Inbox className="w-3 h-3" />
          Folders
        </div>
        <div className="space-y-1">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-7 rounded-lg bg-surface-2 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-3 py-2">
        <div className="text-[10px] text-text-faint">{error}</div>
      </div>
    );
  }

  // ── Group folders by type ──────────────────────────────────────────
  const systemFolders = folders.filter((f) => f.is_system);
  const customFolders = folders.filter((f) => !f.is_system);

  return (
    <div className="px-2 py-2 border-b border-border">
      {/* Header with collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between w-full px-2 py-1.5 rounded-lg hover:bg-surface-2 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Inbox className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
            Folders
          </span>
        </div>
        <ChevronDown
          className={`w-3 h-3 text-text-faint transition-transform ${
            collapsed ? "-rotate-90" : ""
          }`}
        />
      </button>

      {/* Folder list */}
      {!collapsed && (
        <div className="mt-1 space-y-0.5">
          {/* System folders */}
          {systemFolders.map((f) => {
            const Icon = getFolderIcon(f);
            const isActive = activeFolder === f.name;
            return (
              <button
                key={f.id}
                onClick={() => setActiveFolder(isActive ? null : f.name)}
                data-active={isActive}
                className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-[11px] font-medium transition-colors hover:bg-surface-2 data-[active=true]:bg-primary/10 data-[active=true]:text-primary"
              >
                <Icon className="w-3.5 h-3.5 shrink-0 text-text-muted" />
                <span className="truncate flex-1 text-left capitalize">
                  {f.name}
                </span>
                {f.unread > 0 && (
                  <span className="min-w-[16px] h-4 rounded-full bg-primary text-[8px] font-bold text-white flex items-center justify-center px-1">
                    {f.unread > 99 ? "99+" : f.unread}
                  </span>
                )}
                {f.count > 0 && f.unread === 0 && (
                  <span className="text-[9px] text-text-faint tabular-nums">
                    {f.count}
                  </span>
                )}
              </button>
            );
          })}

          {/* Divider + custom folders */}
          {customFolders.length > 0 && (
            <div className="border-t border-border my-1" />
          )}
          {customFolders.map((f) => {
            const isActive = activeFolder === f.name;
            const isRenaming = renamingId === f.id;
            return (
              <div key={f.id} className="group flex items-center">
                {isRenaming ? (
                  <div className="flex items-center gap-1 flex-1 px-2 py-1">
                    <FileText className="w-3.5 h-3.5 shrink-0 text-text-muted" />
                    <input
                      ref={renameInputRef}
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRename();
                        if (e.key === "Escape") cancelRename();
                      }}
                      onBlur={handleRename}
                      className="flex-1 rounded border border-primary/40 bg-surface-1 px-1.5 py-0.5 text-[11px] text-text outline-none"
                    />
                  </div>
                ) : (
                  <button
                    onClick={() => setActiveFolder(isActive ? null : f.name)}
                    onDoubleClick={() => startRename(f)}
                    data-active={isActive}
                    className="flex items-center gap-2 flex-1 px-2 py-1.5 rounded-lg text-[11px] font-medium transition-colors hover:bg-surface-2 data-[active=true]:bg-primary/10 data-[active=true]:text-primary"
                  >
                    <FileText className="w-3.5 h-3.5 shrink-0 text-text-muted" />
                    <span className="truncate flex-1 text-left">{f.name}</span>
                    {f.count > 0 && (
                      <span className="text-[9px] text-text-faint tabular-nums">
                        {f.count}
                      </span>
                    )}
                  </button>
                )}
                {!isRenaming && (
                  <button
                    onClick={(e) => handleDelete(f.id, e)}
                    className="p-1 rounded hover:bg-surface-2 text-text-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-all"
                    title="Delete folder"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })}

          {/* Create folder form */}
          <div className="pt-1">
            {showCreateForm ? (
              <div className="flex items-center gap-1 px-2">
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreate();
                    if (e.key === "Escape") {
                      setShowCreateForm(false);
                      setNewName("");
                    }
                  }}
                  placeholder="Folder name"
                  className="flex-1 rounded border border-border bg-surface-1 px-2 py-1 text-[10px] text-text placeholder:text-text-faint outline-none focus:border-primary/40 transition-colors"
                  autoFocus
                />
                <button
                  onClick={handleCreate}
                  disabled={creating || !newName.trim()}
                  className="p-1 rounded hover:bg-surface-2 text-primary disabled:opacity-40"
                >
                  <Loader2 className={`w-3 h-3 ${creating ? "animate-spin" : ""}`} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center gap-1.5 w-full px-2 py-1 rounded-lg text-[10px] text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
              >
                <Plus className="w-3 h-3" />
                <span>New Folder</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
