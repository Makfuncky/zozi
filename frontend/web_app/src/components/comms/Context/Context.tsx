"use client";

import { useMemo, useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  FileText,
  Pin,
  Sparkles,
  Shield,
  Search,
  Download,
  Eye,
  Paperclip,
  ImageIcon,
  FileJson,
  Star,
  X,
  MessageCircle,
} from "@/lib/icons";
import { useComm } from "../CommShell";
import { useDrag, DropZone } from "../DragProvider";

// ── Tab Config ────────────────────────────────────────────────────────────

interface ContextTab {
  key: string;
  label: string;
  icon: typeof Users;
}

const TABS: ContextTab[] = [
  { key: "people",   label: "People / 360",   icon: Users },
  { key: "shared",   label: "Shared files",   icon: FileText },
  { key: "pinned",   label: "Pinned & tasks", icon: Pin },
  { key: "ai",       label: "AI · DLP",       icon: Sparkles },
  { key: "audit",    label: "Audit",          icon: Shield },
];

// ── Sample data for demo ──────────────────────────────────────────────────

interface FileItem {
  name: string;
  type: string;
  sender: string;
  date: string;
  size: string;
}

const SAMPLE_FILES: FileItem[] = [
  { name: "Q3_report.pdf",          type: "pdf",  sender: "Aisha", date: "2h ago",   size: "2.4 MB" },
  { name: "invoice_final.docx",     type: "doc",  sender: "Karim", date: "1d ago",   size: "156 KB" },
  { name: "mockup_v3.fig",          type: "fig",  sender: "Layla", date: "3d ago",   size: "8.1 MB" },
  { name: "meeting_notes.md",       type: "md",   sender: "You",   date: "1w ago",   size: "12 KB"  },
  { name: "product_shot.png",       type: "img",  sender: "Omar",  date: "1w ago",   size: "3.2 MB" },
  { name: "specification_v2.pdf",   type: "pdf",  sender: "Aisha", date: "2w ago",   size: "1.8 MB" },
];

const TYPE_ICONS: Record<string, typeof FileText> = {
  pdf: FileText,
  doc: FileText,
  fig: FileJson,
  md: FileText,
  img: ImageIcon,
};

function FileIcon({ type }: { type: string }) {
  const Icon = TYPE_ICONS[type] || Paperclip;
  return <Icon className="w-4 h-4 text-text-muted" />;
}

// ── Tab Content Components ────────────────────────────────────────────────

function People360() {
  const { activeThread } = useComm();
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-2/50">
        <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center">
          <span className="text-sm font-bold text-text-muted">
            {activeThread?.title?.charAt(0)?.toUpperCase() || "?"}
          </span>
        </div>
        <div>
          <p className="text-sm font-semibold text-text">{activeThread?.title || "Unknown"}</p>
          <p className="text-[10px] text-text-muted">
            {activeThread?.transport === "chat" ? "Direct message" : "Group conversation"}
          </p>
        </div>
      </div>

      {/* Participant list */}
      <div>
        <h4 className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2 px-1">
          Participants
        </h4>
        <div className="space-y-1.5">
          {["Aisha Al-Mamari", "Karim Benali", "Layla Hassan"].map((name) => (
            <div key={name} className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-surface-2 transition-colors cursor-pointer">
              <div className="relative w-7 h-7 rounded-full bg-surface-2 flex items-center justify-center shrink-0">
                <span className="text-[9px] font-bold text-text-muted">{name.charAt(0)}</span>
                <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border-2 border-surface bg-success" />
              </div>
              <div className="min-w-0">
                <p className="text-[12px] font-medium text-text truncate">{name}</p>
                <p className="text-[9px] text-text-faint">Online</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cross-transport stats */}
      <div className="rounded-xl bg-surface-2/30 p-3">
        <h4 className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">
          Conversation History
        </h4>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded-lg bg-surface-2/50">
            <p className="text-sm font-bold text-text">12</p>
            <p className="text-[9px] text-text-faint">Chats</p>
          </div>
          <div className="p-2 rounded-lg bg-surface-2/50">
            <p className="text-sm font-bold text-text">3</p>
            <p className="text-[9px] text-text-faint">Emails</p>
          </div>
          <div className="p-2 rounded-lg bg-surface-2/50">
            <p className="text-sm font-bold text-text">1</p>
            <p className="text-[9px] text-text-faint">Calls</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SharedFiles() {
  return (
    <div>
      <div className="relative mb-3">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-faint" />
        <input
          placeholder="Search files…"
          className="w-full rounded-lg border border-border bg-surface-1 pl-8 pr-3 py-1.5 text-[11px] text-text placeholder:text-text-faint focus:outline-none focus:border-primary/40 transition-colors"
        />
      </div>
      <div className="space-y-1 max-h-[400px] overflow-y-auto">
        {SAMPLE_FILES.map((file, i) => (
          <div
            key={i}
            className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-surface-2 transition-colors cursor-pointer group"
          >
            <div className="w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center shrink-0">
              <FileIcon type={file.type} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-medium text-text truncate">{file.name}</p>
              <p className="text-[9px] text-text-faint">{file.sender} · {file.size}</p>
            </div>
            <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
              <button className="p-1 rounded hover:bg-surface-3 text-text-muted" title="Preview">
                <Eye className="w-3.5 h-3.5" />
              </button>
              <button className="p-1 rounded hover:bg-surface-3 text-text-muted" title="Download">
                <Download className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
      <p className="text-[9px] text-text-faint text-center mt-2">
        {SAMPLE_FILES.length} files shared in this thread
      </p>
    </div>
  );
}

function PinnedTasks() {
  const { setCtxTab } = useComm();
  const { dragPayload } = useDrag();
  const [droppedTasks, setDroppedTasks] = useState<
    Array<{ id: string; text: string; threadTitle: string; done: boolean }>
  >([]);

  // Create a task from a dragged thread (called by DropZone onDrop)
  const handleThreadDrop = useCallback(
    (threadTitle: string) => {
      setDroppedTasks((prev) => [
        ...prev,
        {
          id: `task-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          text: `Follow up on "${threadTitle}"`,
          threadTitle,
          done: false,
        },
      ]);
      // Switch to pinned tab so user sees the new task
      setCtxTab("pinned");
    },
    [setCtxTab]
  );

  // Initial tasks (demo data)
  const initialTasks = [
    { text: "Send invoice to finance", done: false },
    { text: "Schedule follow-up meeting", done: true },
    { text: "Review contract draft", done: false },
  ];

  // Combined: demo tasks + dropped tasks
  const allTasks = [...initialTasks, ...droppedTasks.map((t) => ({ text: t.text, done: t.done }))];

  // Visual feedback when dragging a thread over the context
  const canDropThread = dragPayload?.type === "thread";

  return (
    <DropZone zone="context-panel" onDrop={(payload) => {
      if (payload.type === "thread") handleThreadDrop(payload.thread.title);
    }}>
      <div className={`space-y-3 transition-all ${canDropThread ? "ring-2 ring-primary/40 rounded-xl p-1" : ""}`}>
        {/* Pinned Messages section */}
        <div className="rounded-xl bg-surface-2/30 p-3 space-y-2">
          <h4 className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-1">Pinned Messages</h4>
          <div className="flex items-start gap-2.5 p-2 rounded-lg bg-surface-2/50">
            <Pin className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
            <div>
              <p className="text-[11px] text-text">Approved the Q3 budget — please proceed with the vendor contracts</p>
              <p className="text-[9px] text-text-faint mt-0.5">Aisha · 2d ago</p>
            </div>
          </div>
        </div>

        {/* Tasks section — accepts thread drops */}
        <div
          className={`rounded-xl p-3 space-y-2 transition-all duration-200 ${
            canDropThread
              ? "bg-primary/10 border-2 border-dashed border-primary/40"
              : "bg-surface-2/30 border-2 border-transparent"
          }`}
        >
          <h4 className="flex items-center gap-1.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-1">
            <Star className="w-3 h-3" /> Tasks
            {canDropThread && (
              <span className="ml-auto text-[9px] text-primary font-normal animate-pulse">
                Drop here to create task
              </span>
            )}
          </h4>

          {/* Dropped thread tasks */}
          {droppedTasks.map((task) => (
            <div
              key={task.id}
              className="flex items-start gap-2.5 p-2 rounded-lg bg-primary/5 border border-primary/20"
            >
              <MessageCircle className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
              <div className="min-w-0 flex-1">
                <span className="text-[11px] text-text font-medium">{task.text}</span>
                <p className="text-[8px] text-text-faint mt-0.5">From: {task.threadTitle}</p>
              </div>
              <input
                type="checkbox"
                checked={task.done}
                onChange={() => {
                  setDroppedTasks((prev) =>
                    prev.map((t) => (t.id === task.id ? { ...t, done: !t.done } : t))
                  );
                }}
                className="mt-0.5 w-3.5 h-3.5 rounded border-border text-primary focus:ring-primary/30 shrink-0"
              />
            </div>
          ))}

          {/* Initial demo tasks */}
          {initialTasks.map((task, i) => (
            <label key={i} className="flex items-start gap-2.5 p-1.5 rounded-lg hover:bg-surface-2/50 transition-colors cursor-pointer">
              <input
                type="checkbox"
                checked={task.done}
                readOnly
                className="mt-0.5 w-3.5 h-3.5 rounded border-border text-primary focus:ring-primary/30"
              />
              <span className={`text-[11px] ${task.done ? "line-through text-text-muted" : "text-text"}`}>
                {task.text}
              </span>
            </label>
          ))}

          {/* Empty state */}
          {allTasks.length === 0 && (
            <p className="text-[10px] text-text-faint text-center py-4">
              No tasks yet. Drag a thread here to create one.
            </p>
          )}
        </div>
      </div>
    </DropZone>
  );
}

function AiDlp() {
  return (
    <div className="space-y-3">
      {/* AI Card */}
      <div className="rounded-xl bg-surface-2/30 p-3 space-y-2">
        <div className="flex items-center gap-1.5 mb-1">
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">AI Assistant</span>
        </div>
        <div className="space-y-1">
          {["Summarize thread", "Draft reply", "Extract action items"].map((action) => (
            <button
              key={action}
              className="w-full text-left text-[11px] text-text-muted hover:text-text px-2 py-1.5 rounded-lg hover:bg-surface-2 transition-colors"
            >
              {action}
            </button>
          ))}
        </div>
      </div>

      {/* DLP Status */}
      <div className="rounded-xl bg-surface-2/30 p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <Shield className="w-3.5 h-3.5 text-success" />
          <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">DLP Status</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-success font-medium">
          <span className="w-2 h-2 rounded-full bg-success" />
          No violations detected
        </div>
        <p className="text-[9px] text-text-faint mt-1">All messages scanned. Content policy compliant.</p>
      </div>
    </div>
  );
}

function AuditView() {
  return (
    <div className="space-y-2">
      {[
        { action: "Message sent", time: "10:24 AM", user: "You" },
        { action: "File shared: Q3_report.pdf", time: "10:23 AM", user: "Aisha" },
        { action: "Call started · 12m 34s", time: "9:15 AM", user: "Karim" },
        { action: "Thread created", time: "Yesterday", user: "Layla" },
      ].map((event, i) => (
        <div key={i} className="flex items-start gap-2.5 p-2 rounded-lg hover:bg-surface-2 transition-colors">
          <div className="w-1.5 h-1.5 rounded-full bg-text-faint mt-1.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-[11px] text-text">{event.action}</p>
            <p className="text-[9px] text-text-faint">{event.user} · {event.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main Context Component ────────────────────────────────────────────────

export default function CommContext() {
  const { ctxTab, setCtxTab, activeThread } = useComm();

  if (!activeThread) {
    return (
      <div className="p-4">
        <div className="flex flex-col items-center justify-center h-full text-center py-12">
          <Users className="w-8 h-8 text-text-faint/30 mb-2" />
          <p className="text-xs text-text-muted">Select a conversation</p>
          <p className="text-[10px] text-text-faint mt-0.5">to see context</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Tab strip */}
      <div className="flex border-b border-border shrink-0 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setCtxTab(tab.key)}
            data-active={ctxTab === tab.key}
            className={`flex items-center gap-1.5 px-3 py-2.5 text-[10px] font-semibold border-b-2 transition-colors shrink-0 ${
              ctxTab === tab.key
                ? "border-primary text-primary"
                : "border-transparent text-text-muted hover:text-text hover:border-text-faint"
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-3">
        {ctxTab === "people" && <People360 />}
        {ctxTab === "shared" && <SharedFiles />}
        {ctxTab === "pinned" && <PinnedTasks />}
        {ctxTab === "ai" && <AiDlp />}
        {ctxTab === "audit" && <AuditView />}
      </div>
    </div>
  );
}
