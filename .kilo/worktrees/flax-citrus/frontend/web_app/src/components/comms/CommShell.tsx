"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
  useEffect,
  type Dispatch,
  type SetStateAction,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Plus,
  MessageCircle,
  Mail,
  Video,
  Phone,
  Users,
  Hash,
  AtSign,
  FileText,
  Shield,
  Copy,
  X,
  ChevronDown,
  Maximize2,
  Sun,
  Moon,
} from "@/lib/icons";
import "@/styles/comm.css";

// ── Types ────────────────────────────────────────────────────────────────

export type Transport =
  | "chat" | "group" | "email" | "video" | "contact" | "b2b_masked" | "incident";

export type ReplyContext = {
  email: Message;
  to: string[];
  toNames: string[];
  cc: string[];
  subject: string;
  messageId: number;
} | null;

export type Modality =
  | "inbox" | "direct" | "groups" | "channels" | "email" | "meet"
  | "contacts" | "files" | "mentions" | "security" | "ediscovery";

export interface ThreadSummary {
  id: string;
  transport: Transport;
  title: string;
  preview: string;
  peer?: string;
  peerAvatar?: string;
  unread: number;
  updatedAt: string;
  isPinned?: boolean;
  isMuted?: boolean;
  participants?: number;
  channelType?: string;
  folder?: string;
}

export interface Message {
  id: string;
  threadId: string;
  senderId: string;
  senderName: string;
  body: string;
  attachments?: Array<{ type: string; url: string; name: string }>;
  reactions?: Record<string, string[]>;
  createdAt: string;
  editedAt?: string;
  readBy?: string[];
  transport: Transport;
}

export type Lens = "all" | "unread" | "mentions" | "starred";

export type WsStatus = "connected" | "reconnecting" | "disconnected";

// ── Context ───────────────────────────────────────────────────────────────

interface CommContextValue {
  modality: Modality;
  setModality: (m: Modality) => void;
  lens: Lens;
  setLens: (l: Lens) => void;
  activeThread: ThreadSummary | null;
  setActiveThread: (t: ThreadSummary | null) => void;
  railCollapsed: boolean;
  setRailCollapsed: (v: boolean) => void;
  ctxOpen: boolean;
  setCtxOpen: (v: boolean | ((prev: boolean) => boolean)) => void;
  ctxTab: string;
  setCtxTab: (t: string) => void;
  sendAs: "chat" | "email";
  setSendAs: (v: "chat" | "email") => void;
  threads: ThreadSummary[];
  setThreads: Dispatch<SetStateAction<ThreadSummary[]>>;
  messages: Message[];
  setMessages: Dispatch<SetStateAction<Message[]>>;
  density: "compact" | "normal" | "expanded";
  setDensity: (d: "compact" | "normal" | "expanded") => void;
  wsStatus: WsStatus;
  setWsStatus: (s: WsStatus) => void;
  replyToEmail: ReplyContext;
  setReplyToEmail: (r: ReplyContext) => void;
  activeFolder: string | null;
  setActiveFolder: (f: string | null) => void;
}

const CommCtx = createContext<CommContextValue>(null!);

export function useComm() {
  return useContext(CommCtx);
}

// ── Provider ──────────────────────────────────────────────────────────────

export function CommProvider({ children, initialModality = "inbox" }: {
  children: ReactNode;
  initialModality?: Modality;
}) {
  const [modality, setModality] = useState<Modality>(initialModality);
  const [lens, setLens] = useState<Lens>("all");
  const [activeThread, setActiveThread] = useState<ThreadSummary | null>(null);
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [ctxOpen, setCtxOpen] = useState(true);
  const [ctxTab, setCtxTab] = useState("shared");
  const [sendAs, setSendAs] = useState<"chat" | "email">("chat");
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [wsStatus, setWsStatus] = useState<WsStatus>("disconnected");
  const [density, setDensityState] = useState<"compact" | "normal" | "expanded">("normal");
  const [replyToEmail, setReplyToEmail] = useState<ReplyContext>(null);
  const [activeFolder, setActiveFolder] = useState<string | null>(null);

  // When modality changes away from "email", clear the active folder
  useEffect(() => {
    if (modality !== "email") setActiveFolder(null);
  }, [modality]);

  const setDensity = useCallback((d: "compact" | "normal" | "expanded") => {
    setDensityState(d);
    try { localStorage.setItem("comm-density", d); } catch {}
  }, []);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("comm-density") as "compact" | "normal" | "expanded" | null;
      if (stored) setDensityState(stored);
    } catch {}
  }, []);

  return (
    <CommCtx.Provider value={{
      modality, setModality,
      lens, setLens,
      activeThread, setActiveThread,
      railCollapsed, setRailCollapsed,
      ctxOpen, setCtxOpen,
      ctxTab, setCtxTab,
      sendAs, setSendAs,
      threads, setThreads,
      messages, setMessages,
      density, setDensity,
      wsStatus, setWsStatus,
      replyToEmail, setReplyToEmail,
      activeFolder, setActiveFolder,
    }}>
      {children}
    </CommCtx.Provider>
  );
}

// ── Shell Component ───────────────────────────────────────────────────────

export default function CommShell({
  bar,
  rail,
  stage,
  context,
  dock,
}: {
  bar: ReactNode;
  rail: ReactNode;
  stage: ReactNode;
  context: ReactNode;
  dock: ReactNode;
}) {
   const { railCollapsed, ctxOpen, setRailCollapsed, setCtxOpen, threads, setThreads, activeThread, setActiveThread, setModality, density } = useComm();
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);

  useEffect(() => {
    const check = () => {
      const w = window.innerWidth;
      setIsMobile(w <= 640);
      setIsTablet(w > 640 && w <= 1024);
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // Auto-collapse rail on mobile
  useEffect(() => {
    if (isMobile) setRailCollapsed(true);
  }, [isMobile, setRailCollapsed]);

  // ── Helper: check if an element is visible (not hidden, not display:none) ─
  function isVisible(el: HTMLElement): boolean {
    if (el.hasAttribute("hidden")) return false;
    if (el.closest("[hidden]")) return false;
    try { return !!(el.offsetParent || el.getClientRects().length); } catch { return false; }
  }

  // Keyboard navigation — only active when the comm workspace is focused or visible
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't capture if user is typing in an input
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      // Only fire comm shortcuts when the active element is inside .comm-shell
      // OR when the .comm-shell itself is rendered and visible on screen
      const shell = document.querySelector<HTMLElement>(".comm-shell");
      if (shell) {
        const activeInside = shell.contains(document.activeElement);
        if (!activeInside && !isVisible(shell)) return;
      }

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        if (!threads.length || !activeThread) return setActiveThread(threads[0] || null);
        const idx = threads.findIndex((t) => t.id === activeThread.id);
        if (idx < threads.length - 1) setActiveThread(threads[idx + 1]);
      }
      if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!threads.length || !activeThread) return;
        const idx = threads.findIndex((t) => t.id === activeThread.id);
        if (idx > 0) setActiveThread(threads[idx - 1]);
      }
      if (e.key === "Enter" && activeThread) {
        // Already selected, just ensure it's visible
      }
      if (e.key === "o") {
        e.preventDefault();
        // Mark read — handled by the thread row
      }
      if (e.key === "c") {
        e.preventDefault();
        // Focus composer
        const composer = document.querySelector<HTMLTextAreaElement>(".composer-textarea");
        composer?.focus();
      }
      if (e.key === "v" && activeThread) {
        e.preventDefault();
        setModality("meet");
      }
      if (e.key === "m" && activeThread) {
        e.preventDefault();
        const updated = threads.map((t) => t.id === activeThread.id ? { ...t, isMuted: !t.isMuted } : t);
        setThreads(updated);
        setActiveThread({ ...activeThread, isMuted: !activeThread.isMuted });
      }
      if (e.key === "s" && activeThread) {
        e.preventDefault();
        const updated = threads.map((t) => t.id === activeThread.id ? { ...t, isPinned: !t.isPinned } : t);
        setThreads(updated);
        setActiveThread({ ...activeThread, isPinned: !activeThread.isPinned });
      }
      if (e.key === "u" && activeThread) {
        e.preventDefault();
        const updated = threads.map((t) => t.id === activeThread.id ? { ...t, unread: 1 } : t);
        setThreads(updated);
      }
      if (e.key === "e" && activeThread) {
        e.preventDefault();
        setActiveThread(null);
      }
      if (e.key === "/" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        // Open shortcuts help — handled by StatusDock
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [threads, activeThread, setActiveThread, setModality, setThreads]);

  const railAttr = isMobile
    ? "sheet"
    : railCollapsed
      ? "collapsed"
      : "open";
  const ctxAttr = ctxOpen ? "open" : "closed";

  const densityClass = density === "compact" ? "comm-density-compact" : density === "expanded" ? "comm-density-expanded" : "comm-density-normal";

  return (
    <div className={`comm-shell theme-card ${densityClass}`} data-rail={railAttr} data-ctx={ctxAttr}>
      {/* Ambient layer */}
      <div aria-hidden className="comm-ambient text-primary" />

      {/* Command bar */}
      <header className="comm-bar theme-elevated border-b border-border flex items-center px-3 gap-2">
        {bar}
      </header>

      {/* Modality rail + conversation list */}
      <aside className="comm-rail border-r border-border">
        {rail}
      </aside>

      {/* Stage */}
      <main className="comm-stage">
        {stage}
      </main>

      {/* Context inspector */}
      <AnimatePresence>
        {ctxOpen && (
          <motion.aside
            key="context"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.18 }}
            className="comm-context border-l border-border theme-elevated overflow-y-auto"
          >
            {context}
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Status dock */}
      <footer className="comm-dock theme-elevated border-t border-border flex items-center px-3 gap-2 text-[10px] text-text-muted">
        {dock}
      </footer>
    </div>
  );
}
