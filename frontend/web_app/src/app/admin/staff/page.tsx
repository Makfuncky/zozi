"use client";
import AdminLayout from "@/components/AdminLayout";
import dynamic from "next/dynamic";
import { PanelLoadingState } from "@/components/PanelPage";

const StaffContent = dynamic(() => import("./_components/staff-content").then(m => ({ default: m.StaffContent })), {
  loading: () => <PanelLoadingState count={4} blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse" />
});

export default function AdminStaffPage() {
  return (
    <AdminLayout title="Staff">
      <StaffContent />
    </AdminLayout>
  );
}
