"use client";

import { useRef, useMemo, useEffect, useState, useCallback } from "react";
import {
  MessageCircle, CheckCheck, FileText, ChevronUp, Loader2,
  Search, X, ChevronDown, ChevronUp as ChevronUpIcon,
} from "@/lib/icons";
import { useComm, type Message } from "../../CommShell";
import { useChatHistory, type ChatHistoryMessage } from "@/hooks/useChatHistory";

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

// ── Date utilities ──────────────────────────────────────────────────────

/** Extract the calendar date (YYYY-MM-DD) from an ISO string or Date. */
function calendarDate(input: string | Date): string {
  const d = typeof input === "string" ? new Date(input) : input;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Format a date as "Today", "Yesterday", "March 15", or "March 15, 2024". */
function formatDateLabel(iso: string): string {
  const d = new Date(iso);

  const today = new Date();
  const todayCal = calendarDate(today);
  const yesterdayCal = calendarDate(new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1));
  const msgCal = calendarDate(d);

  if (msgCal === todayCal) return "Today";
  if (msgCal === yesterdayCal) return "Yesterday";

  const sameYear = d.getFullYear() === today.getFullYear();
  return d.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}

// ── Date Separator ──────────────────────────────────────────────────────

function DateSeparator({ date }: { date: string }) {
  const label = formatDateLabel(date);
  return (
    <div className="relative flex items-center gap-3 py-2" role="separator" aria-label={label}>
      <div className="flex-1 h-px bg-border/60" />
      <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider shrink-0 select-none">
        {label}
      </span>
      <div className="flex-1 h-px bg-border/60" />
    </div>
  );
}

// ── Message Bubble with search highlighting ─────────────────────────────

/**
 * Split text into segments around a search query, returning an array of
 * `{ text, match }` objects so the caller can highlight matches.
 */
function highlightText(text: string, query: string): Array<{ text: string; match: boolean }> {
  if (!query.trim()) return [{ text, match: false }];
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`(${escaped})`, "gi");
  const parts = text.split(regex);
  const result: Array<{ text: string; match: boolean }> = [];
  for (const part of parts) {
    if (part.length === 0) continue;
    result.push({ text: part, match: regex.test(part) || part.toLowerCase() === query.toLowerCase() });
  }
  return result;
}

function MessageBubble({
  message, isOwn, searchQuery, isActiveMatch,
}: {
  message: Message;
  isOwn: boolean;
  searchQuery?: string;
  isActiveMatch?: boolean;
}) {
  const bodySegments = useMemo(
    () => (searchQuery ? highlightText(message.body, searchQuery) : [{ text: message.body, match: false }]),
    [message.body, searchQuery],
  );

  return (
    <div
      className={`flex gap-2.5 ${isOwn ? "flex-row-reverse" : ""} msg-enter ${
        isActiveMatch ? "msg-search-active" : ""
      }`}
      data-msg-id={message.id}
    >
      <div className="w-7 h-7 rounded-full bg-surface-2 flex items-center justify-center shrink-0 mt-0.5">
        <span className="text-[9px] font-bold text-text-muted">
          {message.senderName.charAt(0).toUpperCase()}
        </span>
      </div>

      <div className={`max-w-[75%] ${isOwn ? "items-end" : "items-start"} flex flex-col`}>
        {!isOwn && (
          <span className="text-[10px] font-medium text-text-muted mb-0.5 px-1">
            {message.senderName}
          </span>
        )}
        <div
          className={`rounded-2xl px-3.5 py-2 text-[13px] leading-relaxed ${
            isOwn
              ? "bg-primary/15 text-text rounded-br-md"
              : "bg-surface-2 text-text rounded-bl-md"
          } ${isActiveMatch ? "ring-2 ring-primary/40 bg-primary/5" : ""}`}
        >
          {bodySegments.map((seg, i) =>
            seg.match ? (
              <mark
                key={i}
                className="bg-amber-300/40 text-text rounded-sm px-0.5"
              >
                {seg.text}
              </mark>
            ) : (
              <span key={i}>{seg.text}</span>
            )
          )}
        </div>

        {message.attachments && message.attachments.length > 0 && (
          <div className="flex gap-1.5 mt-1">
            {message.attachments.map((att, i) => (
              <div key={i} className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-2.5 py-1.5 text-[10px] text-text-muted">
                <FileText className="w-3 h-3" />
                <span className="truncate max-w-[100px]">{att.name}</span>
              </div>
            ))}
          </div>
        )}

        <div className={`flex items-center gap-1.5 mt-0.5 px-1 ${isOwn ? "flex-row-reverse" : ""}`}>
          <span className="text-[9px] text-text-faint">{formatTime(message.createdAt)}</span>
          {isOwn && (
            <CheckCheck className={`w-3 h-3 ${message.readBy && message.readBy.length > 0 ? "text-primary tick-read" : "text-text-faint tick-sent"}`} />
          )}
          {message.reactions && Object.keys(message.reactions).length > 0 && (
            <div className="flex items-center gap-0.5">
              {Object.entries(message.reactions).map(([emoji, users]) => (
                <span key={emoji} className="text-[11px] bg-surface-2 rounded-full px-1.5 py-0.5">
                  {emoji}{users.length > 1 ? users.length : ""}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** Convert a canonical ChatHistoryMessage into a Message for display. */
function histToMsg(h: ChatHistoryMessage, threadId: string): Message {
  return {
    id: String(h.id),
    threadId,
    senderId: String(h.sender_id),
    senderName: h.sender_name,
    body: h.body,
    createdAt: h.created_at,
    transport: "chat" as const,
  };
}

// ── Typing Indicator ────────────────────────────────────────────────────

function TypingIndicator({ names }: { names: string[] }) {
  if (names.length === 0) return null;

  let label: string;
  if (names.length === 1) {
    label = `${names[0]} is typing…`;
  } else if (names.length === 2) {
    label = `${names[0]} and ${names[1]} are typing…`;
  } else {
    label = `${names[0]} and ${names.length - 1} others are typing…`;
  }

  return (
    <div className="flex items-center gap-2 px-1 py-1.5 text-[11px] text-text-muted animate-pulse">
      <span className="flex items-center gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-text-faint/40 animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 rounded-full bg-text-faint/40 animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-1.5 h-1.5 rounded-full bg-text-faint/40 animate-bounce" style={{ animationDelay: "300ms" }} />
      </span>
      <span className="font-medium">{label}</span>
    </div>
  );
}

// ── Message Search Bar ──────────────────────────────────────────────────

function MessageSearchBar({
  query,
  onQueryChange,
  matchIndex,
  totalMatches,
  onPrev,
  onNext,
  onClose,
}: {
  query: string;
  onQueryChange: (q: string) => void;
  matchIndex: number;
  totalMatches: number;
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (e.shiftKey) onPrev();
      else onNext();
    }
    if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div className="sticky top-0 z-10 flex items-center gap-2 px-3 py-2 bg-surface/95 backdrop-blur-sm border-b border-border rounded-t-xl">
      <Search className="w-3.5 h-3.5 text-text-muted shrink-0" />
      <input
        ref={inputRef}
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search messages…"
        className="flex-1 bg-transparent border-0 outline-none text-[12px] text-text placeholder:text-text-faint"
      />
      {totalMatches > 0 && (
        <span className="text-[10px] text-text-muted tabular-nums shrink-0 min-w-[4ch] text-right">
          {matchIndex + 1}/{totalMatches}
        </span>
      )}
      {totalMatches === 0 && query.trim().length > 0 && (
        <span className="text-[10px] text-text-faint shrink-0">No results</span>
      )}
      <div className="flex items-center gap-0.5">
        <button
          onClick={onPrev}
          disabled={totalMatches === 0}
          className="p-1 rounded hover:bg-surface-2 text-text-muted hover:text-text disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Previous match (Shift+Enter)"
        >
          <ChevronUpIcon className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onNext}
          disabled={totalMatches === 0}
          className="p-1 rounded hover:bg-surface-2 text-text-muted hover:text-text disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Next match (Enter)"
        >
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>
      <button
        onClick={onClose}
        className="p-1 rounded hover:bg-surface-2 text-text-muted hover:text-text transition-colors"
        title="Close search (Esc)"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ── Message list with date separators ───────────────────────────────────

function withDateSeparators(msgs: Message[]): Array<Message | { __kind: "date-separator"; date: string }> {
  if (msgs.length === 0) return [];

  const result: Array<Message | { __kind: "date-separator"; date: string }> = [];
  let prevDate = calendarDate(msgs[0].createdAt);
  result.push({ __kind: "date-separator", date: msgs[0].createdAt });
  result.push(msgs[0]);

  for (let i = 1; i < msgs.length; i++) {
    const curDate = calendarDate(msgs[i].createdAt);
    if (curDate !== prevDate) {
      result.push({ __kind: "date-separator", date: msgs[i].createdAt });
      prevDate = curDate;
    }
    result.push(msgs[i]);
  }

  return result;
}

// ── Props ────────────────────────────────────────────────────────────────

interface ChatStreamProps {
  messages: Message[];
  threadId?: number;
  typingUserNames?: string[];
}

// ── Component ────────────────────────────────────────────────────────────

export default function ChatStream({ messages, threadId, typingUserNames = [] }: ChatStreamProps) {
  const { activeThread } = useComm();
  const scrollRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const prevMsgCountRef = useRef(messages.length);

  // ── Search state ──────────────────────────────────────────────
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);

  const {
    olderMessages,
    loading: loadingOlder,
    hasMore,
    loadMore,
  } = useChatHistory(threadId);

  // ── Scroll-preservation refs ───────────────────────────────────
  const olderCountRef = useRef(olderMessages.length);
  const prevScrollHeightRef = useRef(0);

  if (scrollRef.current && olderMessages.length > olderCountRef.current) {
    prevScrollHeightRef.current = scrollRef.current.scrollHeight;
  }

  // Build the full message list: history (older) + live messages (newer)
  const allMessages = useMemo(() => {
    const threadIdStr = activeThread?.id ?? "";
    const history = olderMessages.map((h) => histToMsg(h, threadIdStr));
    return [...history, ...messages];
  }, [olderMessages, messages, activeThread?.id]);

  // Memoize the message list WITH date separators interleaved
  const renderedItems = useMemo(() => withDateSeparators(allMessages), [allMessages]);

  // ── Search logic ──────────────────────────────────────────────
  // Compute which messages match the search query and which match
  // index is currently active. Only messages (not separators) match.
  const matchingMessageIds = useMemo(() => {
    if (!searchQuery.trim()) return new Set<string>();
    const q = searchQuery.toLowerCase();
    const ids = new Set<string>();
    for (const msg of allMessages) {
      if (msg.body.toLowerCase().includes(q)) {
        ids.add(msg.id);
      }
    }
    return ids;
  }, [allMessages, searchQuery]);

  // Ordered list of matching message IDs (for navigation order)
  const matchOrder = useMemo(() => {
    if (!searchQuery.trim()) return [] as string[];
    const q = searchQuery.toLowerCase();
    return allMessages.filter((m) => m.body.toLowerCase().includes(q)).map((m) => m.id);
  }, [allMessages, searchQuery]);

  const totalMatches = matchOrder.length;

  // Clamp match index when match count changes
  useEffect(() => {
    if (currentMatchIndex >= totalMatches) {
      setCurrentMatchIndex(Math.max(0, totalMatches - 1));
    }
  }, [totalMatches, currentMatchIndex]);

  // Scroll the current match into view
  useEffect(() => {
    if (!isSearchOpen || totalMatches === 0) return;
    const matchId = matchOrder[currentMatchIndex];
    if (!matchId) return;

    const el = scrollRef.current?.querySelector(`[data-msg-id="${matchId}"]`);
    if (el) {
      el.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [currentMatchIndex, isSearchOpen, totalMatches, matchOrder]);

  const handleSearchPrev = useCallback(() => {
    setCurrentMatchIndex((prev) => (prev > 0 ? prev - 1 : totalMatches - 1));
  }, [totalMatches]);

  const handleSearchNext = useCallback(() => {
    setCurrentMatchIndex((prev) => (prev < totalMatches - 1 ? prev + 1 : 0));
  }, [totalMatches]);

  const openSearch = useCallback(() => {
    setIsSearchOpen(true);
    setSearchQuery("");
    setCurrentMatchIndex(0);
  }, []);

  const closeSearch = useCallback(() => {
    setIsSearchOpen(false);
    setSearchQuery("");
    setCurrentMatchIndex(0);
  }, []);

  // Keyboard: Cmd+F / Ctrl+F to open, Escape to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Cmd+F / Ctrl+F — open search
      if ((e.metaKey || e.ctrlKey) && e.key === "f") {
        e.preventDefault();
        openSearch();
        return;
      }
      // Escape — close search if open
      if (e.key === "Escape" && isSearchOpen) {
        closeSearch();
        e.preventDefault();
        return;
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isSearchOpen, openSearch, closeSearch]);

  // ── Auto-scroll to bottom ─────────────────────────────────────
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (isNearBottom && messages.length > prevMsgCountRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
    prevMsgCountRef.current = messages.length;
  }, [messages.length]);

  // ── Scroll preservation ───────────────────────────────────────
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const prevCount = olderCountRef.current;
    olderCountRef.current = olderMessages.length;

    if (olderMessages.length > prevCount) {
      const diff = el.scrollHeight - prevScrollHeightRef.current;
      if (diff > 0) {
        el.scrollTop += diff;
      }
    }
  }, [olderMessages.length]);

  // ── IntersectionObserver ──────────────────────────────────────
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasMore || loadingOlder) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMore && !loadingOlder) {
          loadMore();
        }
      },
      { root: scrollRef.current, threshold: 0 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loadingOlder, loadMore]);

  return (
    <div className="flex flex-col min-h-0 flex-1">
      {/* Search bar — sticky at top of the message area */}
      {isSearchOpen && (
        <MessageSearchBar
          query={searchQuery}
          onQueryChange={(q) => {
            setSearchQuery(q);
            setCurrentMatchIndex(0);
          }}
          matchIndex={currentMatchIndex}
          totalMatches={totalMatches}
          onPrev={handleSearchPrev}
          onNext={handleSearchNext}
          onClose={closeSearch}
        />
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 scroll-smooth">
        {/* Scroll sentinel */}
        <div ref={sentinelRef} aria-hidden className="h-0" />

        {/* Load earlier messages button */}
        {hasMore && !loadingOlder && (
          <div className="flex justify-center pb-1">
            <button
              onClick={loadMore}
              className="flex items-center gap-1.5 rounded-full px-4 py-1.5 text-[10px] font-semibold
                         bg-surface-2/60 hover:bg-surface-2 text-text-muted hover:text-text
                         border border-border/40 transition-colors"
            >
              <ChevronUp className="w-3 h-3" />
              Load earlier messages
            </button>
          </div>
        )}

        {/* Loading indicator */}
        {loadingOlder && (
          <div className="flex justify-center py-2">
            <div className="flex items-center gap-2 text-[10px] text-text-muted">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Loading earlier messages…
            </div>
          </div>
        )}

        {/* Empty state */}
        {renderedItems.length === 0 && !loadingOlder && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageCircle className="w-10 h-10 text-text-faint/30 mb-2" />
            <p className="text-xs text-text-muted">No messages yet</p>
            <p className="text-[10px] text-text-faint mt-0.5">Start the conversation below</p>
          </div>
        )}

        {/* Message list with date separators */}
        {renderedItems.map((item) => {
          if ("__kind" in item && item.__kind === "date-separator") {
            return <DateSeparator key={item.date} date={item.date} />;
          }
          const msg = item as Message;
          const idxInMatchOrder = matchOrder.indexOf(msg.id);
          const isActiveMatch = idxInMatchOrder >= 0 && idxInMatchOrder === currentMatchIndex;
          return (
            <MessageBubble
              key={msg.id}
              message={msg}
              isOwn={msg.senderId === "me"}
              searchQuery={isSearchOpen ? searchQuery : undefined}
              isActiveMatch={isActiveMatch}
            />
          );
        })}

        {/* Typing indicator */}
        <TypingIndicator names={typingUserNames} />
      </div>
    </div>
  );
}
