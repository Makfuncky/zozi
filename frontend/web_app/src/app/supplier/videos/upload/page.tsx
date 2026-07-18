"use client";

import { Button } from "@/components/ui/Button";

import { useState } from "react";
import { Upload, Film, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent } from "@/components/PanelPage";

export default function SupplierVideoUploadPage() {
  const [productId, setProductId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!file || !productId) {
      setError("Product ID and video file are required.");
      return;
    }
    setSubmitting(true);
    try {
      const form = new FormData();
      form.append("product_id", productId);
      form.append("video", file);
      if (title) form.append("title", title);
      if (description) form.append("description", description);

      const res = await apiFetch("/product-videos/upload", { method: "POST", body: form });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Upload failed");
      }
      setSuccess(true);
      setFile(null);
      setTitle("");
      setDescription("");
      setProductId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SupplierLayout title="Upload Product Video">
      <PanelContent width="narrow">
        <div className="mx-auto max-w-2xl px-4 py-8">
          <h1 className="text-2xl font-bold text-text">Upload Product Video</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-text">Product ID</label>
          <input
            type="number"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-text"
            placeholder="Enter product ID"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-text">Video File</label>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-border px-4 py-6 hover:border-primary">
            <Film className="h-5 w-5 text-text-faint" />
            <span className="text-sm text-text-faint">{file ? file.name : "Select video"}</span>
            <input
              type="file"
              accept="video/*"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-text">Title (optional)</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-text"
            placeholder="Video title"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-text">Description (optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-text"
            rows={4}
            placeholder="Short description"
          />
        </div>
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        {success ? <p className="text-sm text-success">Video uploaded successfully.</p> : null}
        <Button variant="primary" type="submit"
          disabled={submitting}>
          {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {submitting ? "Uploading..." : "Upload Video"}
        </Button>
        </form>
        </div>
      </PanelContent>
    </SupplierLayout>
  );
}
