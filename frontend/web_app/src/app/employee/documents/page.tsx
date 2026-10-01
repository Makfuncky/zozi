"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Download,
  Upload,
  FolderOpen,
  RefreshCw,
  FileCheck,
  Shield,
} from "@/lib/icons";
import { useToastStore } from "@/stores/toastStore";
import { ErrorState } from "@/components/employee/ErrorBoundary";
import { Button } from "@/components/ui/Button";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";

interface Document {
  id: number;
  name: string;
  type: string;
  category: string;
  file_url: string;
  uploaded_at: string;
  expires_at: string | null;
  status: string;
}

export default function EmployeeDocumentsPage() {
  const { addToast } = useToastStore();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docName, setDocName] = useState("");
  const [docCategory, setDocCategory] = useState("personal");

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiFetch("/api/v1/employee/hr/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(Array.isArray(data) ? data : data?.documents ?? data?.data ?? []);
      }
    } catch {
      setError("Failed to load documents");
      addToast("Failed to load documents", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !docName.trim()) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("name", docName);
      formData.append("category", docCategory);
      const res = await apiFetch("/api/v1/employee/hr/documents", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        setSelectedFile(null);
        setDocName("");
        fetchDocuments();
      }
    } finally {
      setUploading(false);
    }
  };

  const CATEGORIES = [
    { value: "personal", label: "Personal" },
    { value: "contract", label: "Contract" },
    { value: "policy", label: "Policy" },
    { value: "tax", label: "Tax" },
    { value: "other", label: "Other" },
  ];

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Documents</h1>
          <p className="text-sm text-text-muted mt-1">Your personal document vault</p>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleUpload}
        className="rounded-xl border border-border bg-surface p-5 space-y-4"
      >
        <h2 className="text-sm font-semibold text-text flex items-center gap-2">
          <Upload className="h-4 w-4 text-primary" />
          Upload Document
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Document Name</label>
            <input
              type="text"
              value={docName}
              onChange={(e) => setDocName(e.target.value)}
              placeholder="Employment Contract"
              className="w-full rounded-lg border bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Category</label>
            <select
              value={docCategory}
              onChange={(e) => setDocCategory(e.target.value)}
              className="w-full appearance-none rounded-lg border bg-surface-1 px-3 py-2 pr-8 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">File</label>
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-text file:mr-2 file:rounded-lg file:border-0 file:bg-primary/10 file:px-3 file:py-2 file:text-xs file:font-medium file:text-primary hover:file:bg-primary/20"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <Button type="submit" isLoading={uploading} disabled={!selectedFile || !docName.trim()} leftIcon={<Upload className="h-4 w-4" />}>
            Upload
          </Button>
        </div>
      </motion.form>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-xl border border-border bg-surface p-5"
      >
        <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-info" />
          My Documents
        </h2>
        {loading ? (
          <PanelLoadingState count={3} blockClassName="h-14 rounded-xl bg-surface-2 animate-pulse" />
        ) : documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg bg-surface-2 p-3"
              >
                <div className="flex items-center gap-3">
                  {doc.status === "verified" ? (
                    <FileCheck className="h-4 w-4 text-success" />
                  ) : (
                    <FileText className="h-4 w-4 text-text-faint" />
                  )}
                  <div>
                    <p className="text-xs font-medium text-text">{doc.name}</p>
                    <p className="text-xs text-text-muted capitalize">
                      {doc.category} &middot; {doc.uploaded_at}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {doc.status === "verified" && (
                    <Shield className="h-3.5 w-3.5 text-success" />
                  )}
                  {doc.file_url && (
                    <a
                      href={doc.file_url}
                      className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="h-8 w-8 text-text-faint mx-auto mb-3" />
            <p className="text-sm text-text-muted">No documents uploaded</p>
          </div>
        )}
      </motion.div>
    </PanelContent>
  );
}
