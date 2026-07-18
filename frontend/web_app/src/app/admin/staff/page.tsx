"use client";
import AdminLayout from "@/components/AdminLayout";
import { StaffContent } from "./staff-content";

export default function AdminStaffPage() {
  return (
    <AdminLayout title="Staff">
      <StaffContent />
    </AdminLayout>
  );
}
