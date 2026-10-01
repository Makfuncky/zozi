"use client";

import { Plus } from "@/lib/icons";
import { QUICK_ACTIONS } from "@/lib/supplierDashboardConfig";

export function QuickActionsPanel() {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
        <Plus className="h-4 w-4 text-primary" />
        Quick Actions
      </h2>
      <div className="space-y-2">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.route}
            onClick={() => { window.location.href = action.route; }}
            className="w-full flex items-center gap-3 rounded-lg bg-surface-2 px-3 py-2.5 text-left hover:bg-surface-3 transition-colors"
          >
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${action.tone}`}>
              <action.icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-text">{action.label}</p>
              <p className="text-xs text-text-faint">{action.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
