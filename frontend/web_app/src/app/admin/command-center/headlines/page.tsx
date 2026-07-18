"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Globe,
  Plus,
  RefreshCw,
  Trash2,
  ExternalLink,
  Tag,
  Calendar,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";

const MotionDiv = motion.div as typeof motion.div;

interface Headline {
  id: number;
  title: string;
  summary: string;
  category: string;
  priority: string;
  country_code?: string;
  published_at: string;
  ai_sentiment: "positive" | "neutral" | "negative";
}

export default function CommandCenterHeadlinesPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { addToast } = useToastStore();
  const [headlines, setHeadlines] = useState<Headline[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHeadlines = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/admin/executive-news?limit=50");
      const data = await res.json().catch(() => []);
      if (res.ok && Array.isArray(data)) {
        setHeadlines(data);
      }
    } catch {
      addToast("Failed to load headlines", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
      router.push("/admin/login");
      return;
    }
    fetchHeadlines();
  }, [isLoading, isLoggedIn, user, router, fetchHeadlines]);

  const handleDelete = async (id: number) => {
    try {
      const res = await apiFetch(`/admin/executive-news/${id}`, { method: "DELETE" });
      if (res.ok) {
        setHeadlines((prev) => prev.filter((h) => h.id !== id));
        addToast("Headline deleted", "success");
      } else {
        addToast("Failed to delete headline", "error");
      }
    } catch {
      addToast("Failed to delete headline", "error");
    }
  };

  const sentimentColor = (sentiment: Headline["ai_sentiment"]) => {
    if (sentiment === "positive") return "text-success bg-success/10 border-success/20";
    if (sentiment === "negative") return "text-danger bg-danger/10 border-danger/20";
    return "text-text-muted bg-surface-2 border-border";
  };

  const priorityBadge = (priority: string) => {
    const style =
      priority === "high"
        ? "bg-danger/10 text-danger border-danger/20"
        : priority === "normal"
        ? "bg-info/10 text-info border-info/20"
        : "bg-surface-2 text-text-muted border-border";
    return <span className={`text-[10px] px-2 py-0.5 rounded border ${style}`}>{priority}</span>;
  };

  return (
    <AdminLayout title="Market Headlines" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push("/admin/command-center")}
            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back
          </button>
          <button
            onClick={() => router.push("/admin/command-center/headlines/create")}
            className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <Plus className="h-3.5 w-3.5" />
            Create News
          </button>
        </div>

        {loading ? (
          <PanelLoadingState count={6} blockClassName="h-28 animate-pulse rounded-xl bg-surface-2" />
        ) : headlines.length === 0 ? (
          <div className="theme-card rounded-xl border p-8 text-center">
            <Globe className="mx-auto h-8 w-8 text-text-faint mb-2" />
            <p className="text-sm text-text-muted">No market headlines yet.</p>
            <button
              onClick={() => router.push("/admin/command-center/headlines/create")}
              className="theme-btn-primary rounded-lg px-4 py-2 text-xs font-semibold mt-4"
            >
              Publish your first news
            </button>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {headlines.map((headline) => (
              <MotionDiv
                key={headline.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="theme-card rounded-xl border p-4 flex flex-col"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${sentimentColor(headline.ai_sentiment)}`}>
                    {headline.ai_sentiment}
                  </span>
                  {priorityBadge(headline.priority)}
                </div>
                <h3 className="text-sm font-semibold text-text line-clamp-2">{headline.title}</h3>
                <p className="mt-1 text-[11px] text-text-muted line-clamp-3 flex-1">{headline.summary}</p>
                <div className="mt-3 flex items-center justify-between text-[10px] text-text-faint">
                  <span className="flex items-center gap-1">
                    <Tag className="h-3 w-3" />
                    {headline.category}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(headline.published_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => router.push(`/admin/command-center/headlines/create?id=${headline.id}`)}
                    className="theme-btn-secondary rounded-md px-2 py-1 text-[10px] font-semibold flex-1"
                  >
                    Edit
                  </button>
                  <Button variant="danger" className="theme-btn-secondary rounded-md px-2 py-1 text-[10px] font-semibold text-danger border-danger/20 flex items-center justify-center gap-1" onClick={() => handleDelete(headline.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </MotionDiv>
            ))}
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}


