"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, MessageCircle, Mail, Video, Users, Hash, FileText, AtSign,
  Plus, ArrowRight, ArrowUpRight,
} from "@/lib/icons";

interface PaletteResult {
  type: "person" | "thread" | "file" | "room" | "action";
  label: string;
  description?: string;
  icon: typeof Search;
  action: () => void;
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PaletteResult[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const paletteRef = useRef<HTMLDivElement>(null);

  // ⌘K toggle
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
    }
  }, [open]);

  // Click outside
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (paletteRef.current && !paletteRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const search = useCallback((q: string) => {
    setQuery(q);
    if (!q.trim()) {
      setResults([
        { type: "action", label: "New group chat…", icon: Users, description: "Start a group conversation", action: () => {} },
        { type: "action", label: "New channel…", icon: Hash, description: "Create a topic channel", action: () => {} },
        { type: "action", label: "Schedule meeting…", icon: Video, description: "Create a video room", action: () => {} },
        { type: "action", label: "Compose email…", icon: Mail, description: "Write a new email", action: () => {} },
        { type: "action", label: "Jump to #oman-finance", icon: ArrowUpRight, description: "Navigate to channel", action: () => {} },
      ]);
      setSelectedIdx(0);
      return;
    }
    const ql = q.toLowerCase();
    setResults([
      { type: "person", label: q, icon: MessageCircle, description: "Chat with…", action: () => {} },
      { type: "action", label: `Search "${q}" in messages`, icon: Search, description: "Full-text search across channels", action: () => {} },
      { type: "action", label: `Search "${q}" in files`, icon: FileText, description: "Find attachments", action: () => {} },
    ]);
    setSelectedIdx(0);
  }, []);

  const handleKey = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSelectedIdx((i) => Math.min(i + 1, results.length - 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setSelectedIdx((i) => Math.max(i - 1, 0)); }
    if (e.key === "Enter" && results[selectedIdx]) {
      results[selectedIdx].action();
      setOpen(false);
    }
  }, [results, selectedIdx]);

  return (
    <>
      {/* Trigger (⌘K) */}
      <button
        onClick={() => setOpen(true)}
        className="relative flex-1 max-w-md group cursor-pointer"
      >
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-faint" />
          <div className="w-full rounded-xl border border-border bg-surface-1 pl-9 pr-3 py-2 text-[11px] text-text-faint text-left transition-colors group-hover:border-primary/30">
            Search people, messages, files, rooms…
          </div>
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[9px] text-text-faint bg-surface-2 rounded-md px-1.5 py-0.5 font-mono border border-border">
            ⌘K
          </kbd>
        </div>
      </button>

      {/* Overlay */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
            className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh]"
          >
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={() => setOpen(false)}
            />

            {/* Palette */}
            <motion.div
              ref={paletteRef}
              initial={{ opacity: 0, scale: 0.96, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: -8 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="relative w-full max-w-lg rounded-2xl theme-card border border-border shadow-2xl overflow-hidden"
            >
              {/* Search input */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
                <Search className="w-4 h-4 text-text-muted shrink-0" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => search(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Search people, messages, files, rooms, actions…"
                  className="flex-1 bg-transparent border-0 outline-none text-sm text-text placeholder:text-text-faint"
                />
              </div>

              {/* Results */}
              <div className="max-h-[360px] overflow-y-auto p-2 space-y-0.5">
                {results.length === 0 ? (
                  <div className="py-8 text-center text-xs text-text-muted">
                    No results
                  </div>
                ) : (
                  results.map((r, i) => (
                    <button
                      key={`${r.type}-${r.label}-${i}`}
                      onClick={() => { r.action(); setOpen(false); }}
                      data-active={i === selectedIdx}
                      className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-left transition-colors data-[active=true]:bg-primary/10 text-text hover:bg-surface-2"
                    >
                      <r.icon className="w-4 h-4 text-text-muted shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-[13px] font-medium truncate">{r.label}</div>
                        {r.description && (
                          <div className="text-[10px] text-text-faint truncate">{r.description}</div>
                        )}
                      </div>
                      <ArrowRight className="w-3 h-3 text-text-faint opacity-0 group-hover:opacity-100" />
                    </button>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center gap-3 px-4 py-2 border-t border-border text-[9px] text-text-faint">
                <span><kbd className="px-1 py-0.5 rounded bg-surface-2 font-mono">↑↓</kbd> Navigate</span>
                <span><kbd className="px-1 py-0.5 rounded bg-surface-2 font-mono">↵</kbd> Open</span>
                <span><kbd className="px-1 py-0.5 rounded bg-surface-2 font-mono">Esc</kbd> Close</span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
