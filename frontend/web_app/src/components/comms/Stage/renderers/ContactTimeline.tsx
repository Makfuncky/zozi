"use client";

import { MessageCircle, Mail, Video, Phone, Calendar } from "@/lib/icons";
import { useComm } from "../../CommShell";

export default function ContactTimeline() {
  const { activeThread } = useComm();
  const name = activeThread?.title || "Contact";

  const events = [
    { type: "chat", label: "Chat conversation", detail: "12 messages", time: "2h ago", icon: MessageCircle },
    { type: "email", label: "Email thread", detail: "3 emails exchanged", time: "1d ago", icon: Mail },
    { type: "call", label: "Video call", detail: "24m 12s", time: "3d ago", icon: Video },
    { type: "chat", label: "Chat conversation", detail: "5 messages", time: "1w ago", icon: MessageCircle },
    { type: "email", label: "Invoice attached", detail: "INV-2024-0891", time: "2w ago", icon: Mail },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Profile hero */}
      <div className="flex items-center gap-4 p-4 rounded-xl bg-surface-2/30">
        <div className="w-14 h-14 rounded-full bg-surface-2 flex items-center justify-center text-xl font-bold text-text-muted">
          {name.charAt(0).toUpperCase()}
        </div>
        <div>
          <h2 className="text-base font-bold text-text">{name}</h2>
          <p className="text-xs text-text-muted">Sales Director · Oman</p>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="flex items-center gap-1 text-[10px] text-text-muted"><MessageCircle className="w-3 h-3" />12</span>
            <span className="flex items-center gap-1 text-[10px] text-text-muted"><Mail className="w-3 h-3" />3</span>
            <span className="flex items-center gap-1 text-[10px] text-text-muted"><Video className="w-3 h-3" />1</span>
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="flex gap-2">
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-white text-[11px] font-semibold hover:bg-primary/90 transition-colors">
          <MessageCircle className="w-3.5 h-3.5" />
          Message
        </button>
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-2 text-text text-[11px] font-semibold hover:bg-surface-3 transition-colors">
          <Calendar className="w-3.5 h-3.5" />
          Schedule
        </button>
      </div>

      {/* Timeline */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-3">
          Conversation History
        </h3>
        <div className="space-y-2">
          {events.map((ev, i) => (
            <div key={i} className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-surface-2 transition-colors cursor-pointer">
              <div className="w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center shrink-0">
                <ev.icon className="w-4 h-4 text-text-muted" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[12px] font-medium text-text">{ev.label}</p>
                <p className="text-[10px] text-text-faint">{ev.detail}</p>
              </div>
              <span className="text-[9px] text-text-faint shrink-0">{ev.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
