"use client";

import dynamic from "next/dynamic";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs, PanelCard, PanelGrid, PanelSection, PanelStatCard, PanelActionBar, PanelDivider } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { Network, Crown, Users, Lock, Building2, ChevronRight, Sparkles, ArrowRight } from "@/lib/icons";
import OrgChartTree from "@/components/ems/OrgChartTree";
import { Button } from "@/components/ui/Button";

const StaffContent = dynamic(() => import("../staff/_components/staff-content").then((m) => m.StaffContent), { ssr: false });
const EmployeesContent = dynamic(() => import("../employees/_components/employees-content").then((m) => m.EmployeesContent), { ssr: false });
const PermissionsContent = dynamic(() => import("../permissions/_components/permissions-content").then((m) => m.PermissionsContent), { ssr: false });

type OrgSection = "overview" | "hierarchy" | "staff" | "employees" | "permissions";

export default function OrganizationPage() {
  const searchParams = useSearchParams();
  const section = (searchParams?.get("section") ?? "overview") as OrgSection;
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const sections = [
    { key: "overview" as OrgSection, label: "Overview", icon: Sparkles },
    { key: "hierarchy" as OrgSection, label: "Org Chart", icon: Network },
    ...(isAdmin ? [
      { key: "staff" as OrgSection, label: "Staff Accounts", icon: Crown },
      { key: "employees" as OrgSection, label: "Employees", icon: Users },
      { key: "permissions" as OrgSection, label: "Permissions", icon: Lock },
    ] : []),
  ];

  return (
    <AdminLayout title="Organization">
      <PanelContent>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-2xl font-display font-bold text-text">Organization</h1>
            <p className="text-text-muted text-sm mt-1">Org chart, staff, employee records, and permissions</p>
          </div>
        </div>

        <PanelTabs items={sections} value={section} onChange={(s) => {
          const url = new URL(window.location.href);
          url.searchParams.set("section", s);
          window.history.pushState({}, "", url.toString());
        }} />

        <Suspense fallback={<PanelLoadingState count={4} />}>
          <AnimatePresence mode="wait">
            <motion.div key={section} initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}>
              {section === "overview" && <OrgOverview />}
              {section === "hierarchy" && <OrgHierarchySection />}
              {section === "staff" && <StaffSection />}
              {section === "employees" && <EmployeesSection />}
              {section === "permissions" && <PermissionsSection />}
            </motion.div>
          </AnimatePresence>
        </Suspense>
      </PanelContent>
    </AdminLayout>
  );
}

function OrgOverview() {
  const navigate = (section: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set("section", section);
    window.history.pushState({}, "", url.toString());
  };

  return (
    <PanelSection className="mt-4">
      <PanelGrid cols={4}>
        <PanelStatCard label="Org Units" value="—" icon={Building2}
          color="from-primary/20 to-accent/20" subtitle="Total organizational units"
          onClick={() => navigate("hierarchy")} />
        <PanelStatCard label="Staff Accounts" value="—" icon={Crown}
          color="from-amber-500/20 to-orange-500/20" subtitle="Admin and support staff"
          onClick={() => navigate("staff")} />
        <PanelStatCard label="Employees" value="—" icon={Users}
          color="from-emerald-500/20 to-teal-500/20" subtitle="Active employee records"
          onClick={() => navigate("employees")} />
        <PanelStatCard label="Roles" value="—" icon={Lock}
          color="from-violet-500/20 to-purple-500/20" subtitle="Permission roles defined"
          onClick={() => navigate("permissions")} />
      </PanelGrid>

      <PanelCard>
        <PanelCard.Header>Quick Actions</PanelCard.Header>
        <PanelGrid cols={4} gap="sm">
          {[
            { label: "View Org Chart", section: "hierarchy", icon: Network, color: "text-primary" },
            { label: "Manage Staff", section: "staff", icon: Crown, color: "text-amber-500" },
            { label: "Employee Records", section: "employees", icon: Users, color: "text-emerald-500" },
            { label: "Role Permissions", section: "permissions", icon: Lock, color: "text-violet-500" },
          ].map((item) => (
            <button key={item.label} onClick={() => navigate(item.section)}
              className="flex items-center gap-3 p-4 rounded-xl bg-surface-1 hover:bg-surface-2
                transition-colors text-left group">
              <item.icon className={`w-5 h-5 ${item.color}`} />
              <span className="text-sm font-medium text-text flex-1">{item.label}</span>
              <ArrowRight className="w-4 h-4 text-text-muted group-hover:translate-x-0.5 transition-transform flex-shrink-0" />
            </button>
          ))}
        </PanelGrid>
      </PanelCard>
    </PanelSection>
  );
}

function OrgHierarchySection() {
  return (
    <PanelSection className="mt-4" title="Organization Hierarchy"
      icon={<Network className="w-5 h-5 text-primary" />}>
      <OrgChartTree />
    </PanelSection>
  );
}

function StaffSection() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return <PanelLoadingState />;
  return <StaffContent />;
}

function EmployeesSection() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return <PanelLoadingState />;
  return <EmployeesContent />;
}

function PermissionsSection() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return <PanelLoadingState />;
  return <PermissionsContent />;
}
