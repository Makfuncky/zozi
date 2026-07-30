"use client";

import { Mail, FileText, ChevronDown, Reply } from "@/lib/icons";
import { type Message, useComm, type ReplyContext } from "../../CommShell";

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

/** Build a ReplyContext from an email message.
 *  Pre-fills the subject and switches to email mode,
 *  but the user must type the recipient address.
 */
function buildReplyCtx(msg: Message): ReplyContext {
  return {
    email: msg,
    to: [],
    toNames: [],
    cc: [],
    subject: "Re:",
    messageId: parseInt(msg.id, 10) || 0,
  };
}

export default function EmailView({ messages }: { messages: Message[] }) {
  const { setReplyToEmail, setSendAs } = useComm();

  const handleReply = (msg: Message) => {
    const ctx = buildReplyCtx(msg);
    setReplyToEmail(ctx);
    setSendAs("email");
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {messages.map((msg) => (
        <div key={msg.id} className="rounded-xl border border-border bg-surface overflow-hidden group">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-surface-1/50">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-surface-2 flex items-center justify-center">
                <span className="text-[9px] font-bold text-text-muted">{msg.senderName.charAt(0).toUpperCase()}</span>
              </div>
              <div>
                <p className="text-[12px] font-semibold text-text">{msg.senderName}</p>
                <p className="text-[9px] text-text-faint">to me</p>
              </div>
            </div>
            <span className="text-[10px] text-text-faint">{formatTime(msg.createdAt)}</span>
          </div>
          <div className="px-4 py-3 text-[13px] text-text leading-relaxed whitespace-pre-wrap">
            {msg.body}
          </div>
          {msg.attachments && msg.attachments.length > 0 && (
            <div className="px-4 pb-3 flex flex-wrap gap-2">
              {msg.attachments.map((att, i) => (
                <div key={i} className="flex items-center gap-2 rounded-lg border border-border bg-surface-1 px-3 py-2 text-[11px]">
                  <FileText className="w-3.5 h-3.5 text-text-muted" />
                  <span className="text-text truncate max-w-[150px]">{att.name}</span>
                </div>
              ))}
            </div>
          )}
          <div className="px-4 pb-3 flex items-center gap-2">
            <button className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text transition-colors">
              <ChevronDown className="w-3 h-3" />
              Show quoted text
            </button>
            <span className="text-[9px] text-text-faint">·</span>
            <button
              onClick={() => handleReply(msg)}
              className="flex items-center gap-1 text-[10px] text-text-muted hover:text-primary transition-colors"
            >
              <Reply className="w-3 h-3" />
              Reply
            </button>
          </div>
        </div>
      ))}
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <Mail className="w-10 h-10 text-text-faint/30 mb-2" />
          <p className="text-xs text-text-muted">No emails in this thread</p>
        </div>
      )}
    </div>
  );
}
