"use client";

import { Suspense } from "react";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import PayrollWorkflow from "@/components/ems/PayrollWorkflow";

export default function PayrollPage() {
  return (
    <AdminLayout title="Payroll Pipeline">
      <PanelContent>
        <Suspense fallback={<PanelLoadingState count={3} />}>
          <PayrollWorkflow />
        </Suspense>
      </PanelContent>
    </AdminLayout>
  );
}
