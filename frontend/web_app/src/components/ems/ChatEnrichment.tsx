"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Smile, Edit3, Trash2, GripVertical, X, Check,
  AlertCircle, Loader2, Send, MoreHorizontal,
  MessageCircle, Reply, Flag, Mic, Paperclip,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { useToastStore } from "@/lib/toastStore";
import { cn } from "@/lib/utils";

// ─── Emoji Picker ───────────────────────────────────────────────

const EMOJI_LIST = [
  "👍", "❤️", "😂", "🎉", "🔥", "😊", "🚀", "👏",
  "💯", "✨", "🙌", "🤝", "💪", "🎯", "🌟", "💡",
  "🤔", "👀", "🙏", "💜", "⭐", "🏆", "✅", "❌",
];

interface EmojiPickerProps {
  onSelect: (emoji: string) => void;
  onClose: () => void;
}

export function EmojiPicker({ onSelect, onClose }: EmojiPickerProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  return (
    <motion.div ref={ref} initial={{ opacity: 0, scale: 0.95, y: -4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: -4 }}
      className="absolute bottom-full left-0 mb-2 p-2.5 rounded-2xl glass-panel shadow-xl
        border border-border z-50 w-64">
      <div className="grid grid-cols-8 gap-1">
        {EMOJI_LIST.map((emoji) => (
          <button key={emoji} onClick={() => onSelect(emoji)}
            className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-surface-2
              text-lg transition-colors">
            {emoji}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

// ─── Reaction Bar ────────────────────────────────────────────────

interface ReactionBarProps {
  messageId: number;
  messageType: string;
  reactions: Record<string, { employee_id: number; timestamp: string }[]>;
  currentUserId: number;
  onReactionToggle: (emoji: string) => void;
}

export function ReactionBar({ messageId, messageType, reactions, currentUserId, onReactionToggle }: ReactionBarProps) {
  return (
    <div className="flex items-center gap-1 flex-wrap mt-1">
      {Object.entries(reactions).map(([emoji, users]) => {
        const hasReacted = users.some((u) => u.employee_id === currentUserId);
        return (
          <motion.button key={emoji} whileTap={{ scale: 0.9 }}
            onClick={() => onReactionToggle(emoji)}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs transition-all",
              hasReacted
                ? "bg-primary/15 text-primary border border-primary/25"
                : "bg-surface-2 text-text-muted hover:bg-surface-3 border border-transparent",
            )}>
            <span className="text-sm">{emoji}</span>
            <span className="font-medium">{users.length}</span>
          </motion.button>
        );
      })}
    </div>
  );
}

// ─── Message Actions Toolbar ─────────────────────────────────────

interface MessageActionsProps {
  messageId: number;
  messageType: string;
  isOwn: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onReact: (emoji: string) => void;
}

export function MessageActions({ messageId, messageType, isOwn, onEdit, onDelete, onReact }: MessageActionsProps) {
  const [showEmoji, setShowEmoji] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <div className="relative">
        <button onClick={() => setShowEmoji(!showEmoji)}
          className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
          <Smile className="w-3.5 h-3.5" />
        </button>
        <AnimatePresence>
          {showEmoji && <EmojiPicker onSelect={(e) => { onReact(e); setShowEmoji(false); }}
            onClose={() => setShowEmoji(false)} />}
        </AnimatePresence>
      </div>
      {isOwn && (
        <>
          <button onClick={onEdit}
            className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
            <Edit3 className="w-3.5 h-3.5" />
          </button>
          <button onClick={onDelete}
            className="p-1.5 rounded-lg hover:bg-danger/10 text-text-muted hover:text-danger transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </>
      )}
    </div>
  );
}

// ─── Inline Message Editor ───────────────────────────────────────

interface MessageEditorProps {
  initialBody: string;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}

export function MessageEditor({ initialBody, onSave, onCancel }: MessageEditorProps) {
  const [body, setBody] = useState(initialBody);
  const [saving, setSaving] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    ref.current?.focus();
    ref.current?.setSelectionRange(body.length, body.length);
  }, []);

  const handleSave = async () => {
    if (!body.trim()) return;
    setSaving(true);
    try {
      await onSave(body);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex gap-2 items-start">
      <textarea ref={ref} value={body} onChange={(e) => setBody(e.target.value)}
        className="flex-1 px-3 py-2 rounded-xl bg-surface border border-primary/30 text-text text-sm
          resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
        rows={2} />
      <div className="flex gap-1 pt-1">
        <button onClick={handleSave} disabled={saving || !body.trim()}
          className="p-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
        </button>
        <button onClick={onCancel}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-muted transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ─── Typing Indicator ────────────────────────────────────────────

interface TypingIndicatorProps {
  typingUsers: string[];
}

export function TypingIndicator({ typingUsers }: TypingIndicatorProps) {
  if (typingUsers.length === 0) return null;

  const text = typingUsers.length === 1
    ? `${typingUsers[0]} is typing...`
    : typingUsers.length === 2
      ? `${typingUsers[0]} and ${typingUsers[1]} are typing...`
      : `${typingUsers[0]} and ${typingUsers.length - 1} others are typing...`;

  return (
    <div className="flex items-center gap-2 px-4 py-1.5 text-xs text-text-muted">
      <div className="flex gap-0.5">
        <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span>{text}</span>
    </div>
  );
}

// ─── Legal Hold Banner ──────────────────────────────────────────

interface LegalHoldBannerProps {
  isActive: boolean;
  reason?: string;
}

export function LegalHoldBanner({ isActive, reason }: LegalHoldBannerProps) {
  if (!isActive) return null;

  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-warning/10 border-b border-warning/20 text-xs text-warning">
      <Flag className="w-3.5 h-3.5 flex-shrink-0" />
      <span className="font-medium">Legal Hold Active</span>
      {reason && <span className="text-text-muted">— {reason}</span>}
    </div>
  );
}

// ─── Voice Note Player ──────────────────────────────────────────

interface VoiceNotePlayerProps {
  url: string;
  duration: number;
  waveform?: number[];
}

export function VoiceNotePlayer({ url, duration, waveform }: VoiceNotePlayerProps) {
  const [playing, setPlaying] = useState(false);

  const formatDuration = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const bars = waveform || Array.from({ length: 20 }, () => Math.random());

  return (
    <button onClick={() => setPlaying(!playing)}
      className="flex items-center gap-3 px-3 py-2 rounded-xl bg-surface-2 hover:bg-surface-3 transition-colors group">
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
        playing ? "bg-danger text-white" : "bg-primary/20 text-primary",
      )}>
        <Mic className="w-4 h-4" />
      </div>
      <div className="flex items-center gap-0.5 h-6">
        {bars.slice(0, 15).map((bar, i) => (
          <div key={i} className={cn(
            "w-0.5 rounded-full transition-all",
            playing ? "bg-primary" : "bg-text-muted/40",
          )}
            style={{
              height: `${Math.max(4, (bar as number) * 40)}px`,
              animation: playing ? `voiceWave 0.5s ease-in-out infinite ${i * 0.05}s` : "none",
            }} />
        ))}
      </div>
      <span className="text-xs text-text-muted">{formatDuration(duration)}</span>
    </button>
  );
}
