"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Save,
  Globe,
  Loader2,
  AlertCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";

const MotionDiv = motion.div as typeof motion.div;

interface HeadlineForm {
  title: string;
  summary: string;
  category: string;
  priority: string;
  ai_sentiment: "positive" | "neutral" | "negative";
  country_code: string;
}

const SENTIMENTS: HeadlineForm["ai_sentiment"][] = ["positive", "neutral", "negative"];
const PRIORITIES = ["low", "normal", "high"];

export default function CommandCenterHeadlinesCreatePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { addToast } = useToastStore();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<HeadlineForm>({
    title: "",
    summary: "",
    category: "general",
    priority: "normal",
    ai_sentiment: "neutral",
    country_code: "",
  });

  const headlineId = searchParams?.get("id");
  const isEditing = !!headlineId;

  const fetchHeadline = useCallback(async (id: number) => {
    try {
      const res = await apiFetch(`/admin/executive-news?limit=100`);
      const data = await res.json().catch(() => []);
      const found = Array.isArray(data) ? data.find((item: any) => item.id === id) : null;
      if (found) {
        setForm({
          title: found.title ?? "",
          summary: found.summary ?? "",
          category: found.category ?? "general",
          priority: found.priority ?? "normal",
          ai_sentiment: found.ai_sentiment ?? "neutral",
          country_code: found.country_code ?? "",
        });
      }
    } catch {
      addToast("Failed to load headline", "error");
    }
  }, [addToast]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
      router.push("/admin/login");
      return;
    }
    if (headlineId) {
      fetchHeadline(Number(headlineId));
    }
  }, [isLoading, isLoggedIn, user, router, headlineId, fetchHeadline]);

  const updateField = (field: keyof HeadlineForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.summary.trim()) {
      addToast("Title and summary are required", "error");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        summary: form.summary.trim(),
        category: form.category || "general",
        priority: form.priority || "normal",
        ai_sentiment: form.ai_sentiment || "neutral",
        country_code: form.country_code || undefined,
        is_published: true,
      };

      // Try POST for create. If backend doesn't support it yet, show actionable error.
      const res = await apiFetch("/admin/executive-news", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        addToast(isEditing ? "Headline updated" : "Headline published", "success");
        router.push("/admin/command-center/headlines");
      } else {
        const text = await res.text().catch(() => "");
        addToast(`Failed to save headline${text ? `: ${text}` : ""}`, "error");
      }
    } catch {
      addToast("Failed to save headline", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AdminLayout title={isEditing ? "Edit Headline" : "Publish News"} headerMode="compact">
      <PanelContent>
        <button
          onClick={() => router.push("/admin/command-center/headlines")}
          className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2 mb-4"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Headlines
        </button>

        <motion.form
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="theme-card rounded-xl border p-5 space-y-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <Globe className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-bold text-text">Headline Details</h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-text-muted mb-1">Title</label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => updateField("title", e.target.value)}
                placeholder="Enter headline title"
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
                required
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-text-muted mb-1">Summary</label>
              <textarea
                value={form.summary}
                onChange={(e) => updateField("summary", e.target.value)}
                placeholder="Brief summary for the headline"
                rows={3}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted mb-1">Category</label>
              <select
                value={form.category}
                onChange={(e) => updateField("category", e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
              >
                <option value="general">General</option>
                <option value="market">Market</option>
                <option value="policy">Policy</option>
                <option value="operations">Operations</option>
                <option value="finance">Finance</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted mb-1">Priority</label>
              <select
                value={form.priority}
                onChange={(e) => updateField("priority", e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted mb-1">Sentiment</label>
              <select
                value={form.ai_sentiment}
                onChange={(e) => updateField("ai_sentiment", e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
              >
                {SENTIMENTS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted mb-1">Country (optional)</label>
              <input
                type="text"
                value={form.country_code}
                onChange={(e) => updateField("country_code", e.target.value.toUpperCase())}
                placeholder="OM, AE, SA, etc."
                maxLength={2}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <p className="text-[11px] text-text-faint flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Ensure content is approved before publishing.
            </p>
            <button
              type="submit"
              disabled={saving}
              className="theme-btn-primary rounded-lg px-5 py-2 text-xs font-semibold flex items-center gap-2 disabled:opacity-60"
            >
              {saving ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Save className="h-3.5 w-3.5" />
              )}
              {isEditing ? "Update Headline" : "Publish News"}
            </button>
          </div>
        </motion.form>
      </PanelContent>
    </AdminLayout>
  );
}


