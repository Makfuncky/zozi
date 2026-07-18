"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Mail, BarChart3, FileText, Users,
  Send, Eye, MousePointer, ShieldAlert
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import EmailCampaignManager from "@/components/admin/EmailCampaignManager";
import EmailTemplateManager from "@/components/admin/EmailTemplateManager";
import EmailProviderConfigManager from "@/components/admin/EmailProviderConfigManager";
import EmailSuppressionManager from "@/components/admin/EmailSuppressionManager";

type TabType = "overview" | "campaigns" | "templates" | "provider" | "suppressions";

const CAMPAIGN_STATUS_STYLES: Record<string, string> = {
  sent: "theme-chip-success",
  sending: "theme-chip-info",
  scheduled: "theme-chip-warning",
};

export default function AdminEmailPanel() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  const tabs = [
    { id: "overview" as TabType, name: "Overview", icon: BarChart3 },
    { id: "campaigns" as TabType, name: "Campaigns", icon: Send },
    { id: "templates" as TabType, name: "Templates", icon: FileText },
    { id: "provider" as TabType, name: "Delivery Settings", icon: Mail },
    { id: "suppressions" as TabType, name: "Suppressions", icon: ShieldAlert },
  ];

  return (
    <PanelContent className="space-y-4">
      <PanelTabs
        items={tabs.map((tab) => ({ key: tab.id, label: tab.name, icon: tab.icon }))}
        value={activeTab}
        onChange={setActiveTab}
      />
      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {activeTab === "overview" && <EmailOverview onSelectTab={setActiveTab} />}
        {activeTab === "campaigns" && <EmailCampaignManager />}
        {activeTab === "templates" && <EmailTemplateManager />}
        {activeTab === "provider" && <EmailProviderConfigManager />}
        {activeTab === "suppressions" && <EmailSuppressionManager />}
      </motion.div>
    </PanelContent>
  );
}

export function EmailOverview({ onSelectTab }: { onSelectTab: (tab: TabType) => void }) {
  const [stats, setStats] = useState<{
    total_subscribers: number;
    active_campaigns: number;
    total_campaigns: number;
    total_sent: number;
    open_rate: number;
    click_rate: number;
    recent_campaigns: Array<{
      id: number;
      name: string;
      status: string;
      sent_at: string | null;
      recipient_count: number;
    }>;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/admin/email/stats")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setStats(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <PanelLoadingState count={3} blockClassName="h-24 animate-pulse rounded-xl bg-surface-2" />
    );
  }

  const totalSubscribers = stats?.total_subscribers ?? 0;
  const totalSent = stats?.total_sent ?? 0;
  const openRate = stats?.open_rate ?? 0;
  const clickRate = stats?.click_rate ?? 0;
  const recentCampaigns = stats?.recent_campaigns ?? [];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        {[
          { icon: Users,        label: "Subscribers",   value: totalSubscribers.toLocaleString(), tone: "text-info"    },
          { icon: Send,         label: "Emails Sent",    value: totalSent.toLocaleString(),        tone: "text-success" },
          { icon: Eye,          label: "Avg Open Rate",  value: `${openRate}%`,                    tone: "text-info"    },
          { icon: MousePointer, label: "Avg Click Rate", value: `${clickRate}%`,                   tone: "text-warning" },
        ].map(({ icon: Icon, label, value, tone }) => (
          <div key={label} className="theme-card rounded-xl border p-2.5">
            <div className="mb-2 flex items-center gap-2">
              <Icon className={`h-4 w-4 ${tone}`} />
              <span className="text-xs text-text-faint">{label}</span>
            </div>
            <p className="text-sm font-semibold text-text">{value}</p>
          </div>
        ))}
      </div>

      {/* Recent Campaigns */}
      <div className="theme-card overflow-hidden rounded-xl border">
        <div className="border-b border-border px-4 py-2.5">
          <h3 className="text-xs font-bold text-text">Recent Campaigns</h3>
        </div>
        <div className="divide-y divide-border">
          {recentCampaigns.length === 0 ? (
            <p className="px-4 py-4 text-xs text-text-faint">No campaigns yet.</p>
          ) : recentCampaigns.map((campaign) => (
            <div key={campaign.id} className="flex items-center justify-between px-4 py-2.5">
              <div>
                <h4 className="text-xs font-semibold text-text">{campaign.name}</h4>
                <div className="mt-0.5 flex items-center gap-2.5">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    CAMPAIGN_STATUS_STYLES[campaign.status] || "theme-chip-muted"
                  }`}>
                    {campaign.status}
                  </span>
                  <span className="text-[11px] text-text-faint">
                    {(campaign.recipient_count ?? 0).toLocaleString()} recipients
                  </span>
                </div>
              </div>
              {campaign.sent_at && (
                <p className="text-[11px] text-text-faint">
                  {new Date(campaign.sent_at).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="theme-card rounded-xl border p-4">
        <h3 className="mb-3 text-xs font-bold text-text">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <button onClick={() => onSelectTab("campaigns")} className="flex items-center gap-3 rounded-xl border border-border p-3 text-left transition-colors hover:bg-surface-2">
            <Mail className="h-5 w-5 shrink-0 text-info" />
            <div>
              <p className="text-xs font-semibold text-text">Create Campaign</p>
              <p className="text-[11px] text-text-faint">Start a new email campaign</p>
            </div>
          </button>
          <button onClick={() => onSelectTab("templates")} className="flex items-center gap-3 rounded-xl border border-border p-3 text-left transition-colors hover:bg-surface-2">
            <FileText className="h-5 w-5 shrink-0 text-success" />
            <div>
              <p className="text-xs font-semibold text-text">New Template</p>
              <p className="text-[11px] text-text-faint">Design email template</p>
            </div>
          </button>
          <button onClick={() => onSelectTab("provider")} className="flex items-center gap-3 rounded-xl border border-border p-3 text-left transition-colors hover:bg-surface-2">
            <BarChart3 className="h-5 w-5 shrink-0 text-warning" />
            <div>
              <p className="text-xs font-semibold text-text">Manage Delivery</p>
              <p className="text-[11px] text-text-faint">Update provider credentials and send a live test</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
