"use client";

import { AlertTriangle, Users, Clock, CheckCircle } from "@/lib/icons";
import { useComm } from "../../CommShell";

export default function IncidentRoom() {
  const { activeThread } = useComm();

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {/* Incident banner */}
      <div className="rounded-xl bg-error/10 border border-error/30 p-4">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="w-5 h-5 text-error" />
          <span className="text-sm font-bold text-text">Incident Active</span>
          <span className="ml-auto rounded-full bg-error/20 text-error text-[9px] font-semibold px-2 py-0.5">
            SEV-1
          </span>
        </div>
        <p className="text-[12px] text-text-muted">
          {activeThread?.title || "Critical incident response"}
        </p>
      </div>

      {/* Action items */}
      <div className="rounded-xl bg-surface-2/30 p-3 space-y-2">
        <h3 className="text-[10px] font-semibold text-text-muted uppercase tracking-wider flex items-center gap-1.5">
          <CheckCircle className="w-3 h-3" /> Action Items
        </h3>
        {[
          { text: "Assess impact scope", done: true, assignee: "Aisha" },
          { text: "Notify stakeholders", done: true, assignee: "Karim" },
          { text: "Deploy hotfix", done: false, assignee: "DevOps" },
          { text: "Post-incident review", done: false, assignee: "You" },
        ].map((item, i) => (
          <label key={i} className="flex items-start gap-2.5 p-1.5 rounded-lg hover:bg-surface-2/50 transition-colors cursor-pointer">
            <input type="checkbox" checked={item.done} readOnly className="mt-0.5 w-3.5 h-3.5 rounded border-border text-primary focus:ring-primary/30" />
            <div className="min-w-0">
              <span className={`text-[11px] ${item.done ? "line-through text-text-muted" : "text-text"}`}>
                {item.text}
              </span>
              <p className="text-[9px] text-text-faint">{item.assignee}</p>
            </div>
          </label>
        ))}
      </div>

      {/* SLA */}
      <div className="rounded-xl bg-surface-2/30 p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-text-muted" />
          <span className="text-[11px] text-text">Response SLA</span>
        </div>
        <span className="text-[11px] font-semibold text-success">Within target</span>
      </div>

      {/* Participants */}
      <div className="rounded-xl bg-surface-2/30 p-3">
        <h3 className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Users className="w-3 h-3" /> Responders
        </h3>
        <div className="space-y-1.5">
          {["Aisha Al-Mamari", "Karim Benali", "Layla Hassan", "Omar Rashid"].map((name) => (
            <div key={name} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-surface-2 transition-colors">
              <div className="w-6 h-6 rounded-full bg-surface-2 flex items-center justify-center text-[8px] font-bold text-text-muted">
                {name.charAt(0)}
              </div>
              <span className="text-[11px] text-text">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
