"use client";

import { useEffect, useState, useCallback } from "react";
import { FileCheck2, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface SupplierDoc {
  id: number;
  supplier_id: number;
  supplier_username?: string;
  document_type: string;
  document_name: string;
  file_url: string;
  status: string;
  review_note?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export default function SupplierDocumentsTab() {
  const [supplierDocs, setSupplierDocs] = useState<SupplierDoc[]>([]);
  const [supplierDocsLoading, setSupplierDocsLoading] = useState(false);
  const [supplierDocActionId, setSupplierDocActionId] = useState<number | null>(null);
  const [supplierDocNotes, setSupplierDocNotes] = useState<Record<number, string>>({});
  const [supplierDocStatusFilter, setSupplierDocStatusFilter] = useState("");

  const fetchSupplierDocs = useCallback(async () => {
    setSupplierDocsLoading(true);
    try {
      const params = supplierDocStatusFilter ? `?status=${supplierDocStatusFilter}` : "";
      const res = await apiFetch(`/admin/suppliers/documents${params}`);
      if (res.ok) setSupplierDocs(await res.json());
    } catch {}
    setSupplierDocsLoading(false);
  }, [supplierDocStatusFilter]);

  useEffect(() => { fetchSupplierDocs(); }, [fetchSupplierDocs]);

  const handleReviewDoc = async (docId: number, action: "approved" | "rejected") => {
    setSupplierDocActionId(docId);
    try {
      const res = await apiFetch(`/admin/suppliers/documents/${docId}/review`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: action, review_note: supplierDocNotes[docId] ?? "" }),
      });
      if (res.ok) fetchSupplierDocs();
    } catch {}
    setSupplierDocActionId(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-text flex items-center gap-2"><FileCheck2 className="w-4 h-4 theme-status-info" /> Supplier KYC Documents</h2>
          <p className="text-xs text-text-muted mt-1">Review and approve / reject supplier verification documents.</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={supplierDocStatusFilter}
            onChange={(e) => setSupplierDocStatusFilter(e.target.value)}
            className="theme-input rounded-xl border px-3 py-1.5 text-xs"
          >
            <option value="">All statuses</option>
            {["pending", "under_review", "approved", "rejected", "expired"].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button onClick={fetchSupplierDocs} disabled={supplierDocsLoading}
            className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50">
            <RefreshCw className={`w-3.5 h-3.5 ${supplierDocsLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>
      {supplierDocsLoading ? (
        <div className="grid gap-3">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-20 rounded-2xl bg-surface-2 animate-pulse" />)}</div>
      ) : supplierDocs.length === 0 ? (
        <div className="py-12 text-center text-sm text-text-muted">No documents found.</div>
      ) : (
        <div className="theme-card rounded-2xl border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Doc", "Supplier", "Type", "Status", "Submitted", "Actions"].map((h) => (
                    <th key={h} className="p-4 text-left text-xs font-semibold text-text-faint">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {supplierDocs.map((doc) => (
                  <tr key={doc.id} className="border-b border-border/50 last:border-0 hover:bg-surface-2/40 transition-colors">
                    <td className="p-4">
                      <a href={doc.file_url} target="_blank" rel="noopener noreferrer"
                        className="text-xs font-medium text-primary hover:underline">
                        {doc.document_name}
                      </a>
                    </td>
                    <td className="p-4 text-xs text-text-muted">{doc.supplier_username ?? `#${doc.supplier_id}`}</td>
                    <td className="p-4 text-xs text-text-muted capitalize">{doc.document_type.replace(/_/g, " ")}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold ${
                        doc.status === "approved" ? "theme-chip-success" :
                        doc.status === "rejected" ? "theme-chip-danger" :
                        doc.status === "under_review" ? "theme-chip-info" :
                        doc.status === "expired" ? "theme-chip-muted" : "theme-chip-warning"
                      }`}>{doc.status}</span>
                    </td>
                    <td className="p-4 text-xs text-text-faint">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="p-4">
                      <div className="flex flex-col gap-1.5 min-w-48">
                        <input
                          value={supplierDocNotes[doc.id] ?? ""}
                          onChange={(e) => setSupplierDocNotes((prev) => ({ ...prev, [doc.id]: e.target.value }))}
                          placeholder="Review note (optional)"
                          className="theme-input rounded-lg border px-2 py-1 text-xs"
                        />
                        {["pending", "under_review"].includes(doc.status) && (
                          <div className="flex gap-1.5">
                            <button
                              disabled={supplierDocActionId === doc.id}
                              onClick={() => handleReviewDoc(doc.id, "approved")}
                              className="theme-chip-success rounded-lg px-2.5 py-1 text-[10px] font-semibold flex items-center gap-1 disabled:opacity-50"
                            ><CheckCircle className="w-3 h-3" />Approve</button>
                            <button
                              disabled={supplierDocActionId === doc.id}
                              onClick={() => handleReviewDoc(doc.id, "rejected")}
                              className="theme-chip-danger rounded-lg px-2.5 py-1 text-[10px] font-semibold flex items-center gap-1 disabled:opacity-50"
                            ><XCircle className="w-3 h-3" />Reject</button>
                          </div>
                        )}
                        {doc.review_note && <p className="text-[10px] text-text-faint italic">{doc.review_note}</p>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}


