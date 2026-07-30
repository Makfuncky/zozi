"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/AdminLayout";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import {
  Plus, Sun, Moon, Maximize2, Rows3,
} from "@/lib/icons";
import CommShell, { CommProvider, useComm } from "@/components/comms/CommShell";
import CommRail from "@/components/comms/Rail/Rail";
import CommStage from "@/components/comms/Stage/Stage";
import CommContext from "@/components/comms/Context/Context";
import CommandPalette from "@/components/comms/CommandPalette";
import LensChips from "@/components/comms/LensChips";
import StatusDock from "@/components/comms/StatusDock";
import UnifiedInboxBridge from "@/components/comms/UnifiedInboxBridge";
import { DragProvider } from "@/components/comms/DragProvider";

// ── Command Bar ───────────────────────────────────────────────────────────

function CommandBar() {
  const { density, setDensity, setModality } = useComm();
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "dark" : "light");
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
  };

  const toggleDensity = () => {
    const next = density === "compact" ? "normal" : density === "normal" ? "expanded" : "compact";
    setDensity(next);
  };

  return (
    <>
      <CommandPalette />
      <LensChips />

      <div className="flex items-center gap-2 ml-auto">
        <button
          onClick={toggleDensity}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors"
          title={`Density: ${density}`}
        >
          <Rows3 className="w-3.5 h-3.5" />
        </button>

        <button className="flex items-center gap-1.5 rounded-lg bg-primary text-white px-3 py-1.5 text-[11px] font-semibold hover:bg-primary/90 transition-colors">
          <Plus className="w-3.5 h-3.5" />
          New
        </button>

        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors"
          title="Toggle theme"
        >
          {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>

        <button className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors" title="Fullscreen">
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </>
  );
}



// ── Main Page ─────────────────────────────────────────────────────────────

export default function AdminCommunicationPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
      router.replace("/admin/login");
    }
  }, [authLoading, isLoggedIn, router, user?.role]);

  if (authLoading) return null;
  if (!isLoggedIn || !isAdminStaffRole(user?.role)) return null;

  return (
    <AdminLayout title="Communication" headerMode="compact">
      <CommProvider>
        <DragProvider>
          <UnifiedInboxBridge />
          <CommShell
            bar={<CommandBar />}
            rail={<CommRail />}
            stage={<CommStage />}
            context={<CommContext />}
            dock={<StatusDock />}
          />
        </DragProvider>
      </CommProvider>
    </AdminLayout>
  );
}
