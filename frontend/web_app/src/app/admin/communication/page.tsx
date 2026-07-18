"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Mail, MessageSquare, Video, Megaphone } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminEmailPanel from "@/components/admin/AdminEmailPanel";
import AdminChatPanel from "@/components/admin/AdminChatPanel";
import AdminVideoPanel from "@/components/admin/AdminVideoPanel";

type CommTab = "email" | "chat" | "video";

const TAB_ITEMS: { key: CommTab; label: string; icon: typeof Mail; desc: string }[] = [
  { key: "email", label: "Email", icon: Mail, desc: "Campaigns, templates, provider & suppressions" },
  { key: "chat", label: "Chat", icon: MessageSquare, desc: "Employee chat, entity threads & B2B messaging" },
  { key: "video", label: "Video", icon: Video, desc: "Secure video conferencing & boardrooms" },
];

export default function AdminCommunicationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<CommTab>(
    (searchParams?.get("tab") as CommTab) || "email"
  );

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
      router.replace("/admin/login");
    }
  }, [authLoading, isLoggedIn, router, user?.role]);

  if (authLoading) return null;
  if (!isLoggedIn || !isAdminStaffRole(user?.role)) return null;

  const selectTab = (tab: CommTab) => {
    setActiveTab(tab);
    router.replace(`/admin/communication?tab=${tab}`, { scroll: false });
  };

  const activeMeta = TAB_ITEMS.find((t) => t.key === activeTab)!;

  return (
    <AdminLayout title="Communication" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-[11px] text-text-faint">
            <Megaphone className="h-3.5 w-3.5 text-primary" />
            <span>Unified internal &amp; external communication hub</span>
          </div>
          <PanelTabs
            items={TAB_ITEMS.map((t) => ({ key: t.key, label: t.label, icon: t.icon }))}
            value={activeTab}
            onChange={selectTab}
          />
          <p className="text-[11px] text-text-muted">{activeMeta.desc}</p>
        </div>

        {/* Active communication system */}
        {activeTab === "email" && <AdminEmailPanel />}
        {activeTab === "chat" && <AdminChatPanel />}
        {activeTab === "video" && <AdminVideoPanel />}
      </PanelContent>
    </AdminLayout>
  );
}
