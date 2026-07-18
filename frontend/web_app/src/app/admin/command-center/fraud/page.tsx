"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import FraudDetectionDashboard from "@/components/FraudDetectionDashboard";

export default function CommandCenterFraudPage() {
  const router = useRouter();

  return (
    <AdminLayout title="Fraud Detection" headerMode="compact">
      <PanelContent>
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => router.push("/admin/command-center")}
            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back
          </button>
        </div>
        <FraudDetectionDashboard />
      </PanelContent>
    </AdminLayout>
  );
}


