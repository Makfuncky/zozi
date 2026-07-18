"use client";
import AdminLayout from "@/components/AdminLayout";
import { Suspense } from "react";
import { EmployeesContent } from "./employees-content";

export default function EmployeesPage() {
  return (
    <AdminLayout title="Human Capital Management" headerMode="compact">
      <Suspense>
        <EmployeesContent />
      </Suspense>
    </AdminLayout>
  );
}
