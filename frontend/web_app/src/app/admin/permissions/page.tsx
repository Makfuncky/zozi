"use client";
import AdminLayout from "@/components/AdminLayout";
import { PermissionsContent } from "./permissions-content";

export default function PermissionsPage() {
  return (
    <AdminLayout title="Permissions">
      <PermissionsContent />
    </AdminLayout>
  );
}
