"use client";
import AdminLayout from "@/components/AdminLayout";
import { PermissionsContent } from "./_components/permissions-content";

export default function PermissionsPage() {
  return (
    <AdminLayout title="Permissions">
      <PermissionsContent />
    </AdminLayout>
  );
}
