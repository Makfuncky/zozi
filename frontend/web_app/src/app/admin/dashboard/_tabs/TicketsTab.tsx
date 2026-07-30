"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { PanelContent } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { useAdminApi } from "@/lib/useAdminApi";

type TicketStatus = "open" | "pending" | "in_progress" | "resolved" | "closed";

interface TicketRow {
  id: number;
  user_id?: number;
  username?: string;
  subject: string;
  message?: string;
  priority?: string;
  status?: TicketStatus | string;
  created_at?: string;
  updated_at?: string;
}

const STATUS_FILTERS: Array<{ value: string; label: string }> = [
  { value: "", label: "All statuses" },
  { value: "open", label: "Open" },
  { value: "pending", label: "Pending" },
  { value: "in_progress", label: "In progress" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
];

function statusChipClass(status?: string): string {
  switch (status) {
    case "open":
      return "theme-chip-info";
    case "pending":
    case "in_progress":
      return "theme-chip-warning";
    case "resolved":
    case "closed":
      return "theme-chip-success";
    default:
      return "theme-chip-muted";
  }
}

export default function TicketsTab() {
  const router = useRouter();
  // Tickets are global (not country-scoped) — hit /admin/tickets directly.
  const { list } = useAdminApi("/admin/tickets", { countryMode: "global" });

  const [rows, setRows] = useState<TicketRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    const { page, ok, error: err } = await list<TicketRow>({ status: status || undefined, page: 1, page_size: 200 });
    if (ok) {
      setRows(page.data);
      setError(null);
    } else {
      setError(err ?? "Failed to load tickets.");
    }
    setLoading(false);
  }, [list, status]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(
      (t) =>
        String(t.id).includes(q) ||
        (t.subject ?? "").toLowerCase().includes(q) ||
        (t.username ?? "").toLowerCase().includes(q),
    );
  }, [rows, search]);

  const columns = useMemo<EnterpriseColumn<TicketRow>[]>(
    () => [
      { key: "id", label: "#", width: "70px", render: (r) => <span className="font-mono text-xs">#{r.id}</span> },
      { key: "subject", label: "Subject", render: (r) => <span className="font-medium text-text">{r.subject}</span> },
      { key: "username", label: "Requester", render: (r) => r.username || (r.user_id ? `User #${r.user_id}` : "—") },
      {
        key: "priority",
        label: "Priority",
        width: "110px",
        render: (r) => <span className="capitalize">{r.priority || "normal"}</span>,
      },
      {
        key: "status",
        label: "Status",
        width: "130px",
        render: (r) => (
          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusChipClass(r.status)}`}>
            {(r.status || "open").toString().replace("_", " ")}
          </span>
        ),
      },
      {
        key: "created_at",
        label: "Created",
        width: "170px",
        render: (r) => (r.created_at ? new Date(r.created_at).toLocaleString() : "—"),
      },
    ],
    [],
  );

  return (
    <PanelContent title="Tickets" className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by #, subject, or requester..."
          className="theme-input min-w-64 flex-1"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="theme-input min-w-44">
          {STATUS_FILTERS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <button
          onClick={() => void load()}
          className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-primary hover:bg-surface-2"
        >
          Refresh
        </button>
      </div>

      {error ? <div className="theme-card p-4 text-sm text-danger">{error}</div> : null}

      <EnterpriseDataTable<TicketRow>
        columns={columns}
        rows={filtered}
        rowKey={(r) => r.id}
        onRowClick={(r) => router.push(`/admin/tickets/${r.id}`)}
        enableGlobalSearch={false}
        emptyState={
          <div className="p-8 text-center text-sm text-text-muted">
            {loading ? "Loading tickets..." : "No tickets found."}
          </div>
        }
      />
    </PanelContent>
  );
}
