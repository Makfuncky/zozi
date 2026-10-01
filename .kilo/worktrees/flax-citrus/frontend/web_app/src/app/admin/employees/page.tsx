"use client";
import AdminLayout from "@/components/AdminLayout";
import dynamic from "next/dynamic";
import { PanelLoadingState } from "@/components/PanelPage";

const EmployeesContent = dynamic(() => import("./_components/employees-content").then(m => ({ default: m.EmployeesContent })), {
  loading: () => <PanelLoadingState count={4} blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse" />
});

export default function EmployeesPage() {
  return (
    <AdminLayout title="Human Capital Management" headerMode="compact">
      <EmployeesContent />
    </AdminLayout>
  );
}
