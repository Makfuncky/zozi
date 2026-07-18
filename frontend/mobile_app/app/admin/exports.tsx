import React, { useMemo, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { Stack } from "expo-router";

import { apiFetch } from "@/lib/api";
import { BackgroundJob, downloadBackgroundJobResult, trackBackgroundJob } from "@/lib/backgroundJobs";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";
import { canAccessAdminEmailManagement } from "@shared/adminPermissions";

type ExportType = "users" | "orders" | "products" | "coupons" | "audit-logs";

interface ExportJobState {
  status: string;
  jobId: string | null;
  filename: string | null;
  error: string | null;
}

interface ExportDefinition {
  type: ExportType;
  title: string;
  description: string;
  endpoint: string;
}

const EXPORTS: ExportDefinition[] = [
  { type: "users", title: "Users", description: "Customer, supplier, and staff account export.", endpoint: "/admin/export/users?background=true" },
  { type: "orders", title: "Orders", description: "Order totals, shipping, and payment status export.", endpoint: "/admin/export/orders?background=true" },
  { type: "products", title: "Products", description: "Catalog, pricing, stock, and supplier mapping export.", endpoint: "/admin/export/products?background=true" },
  { type: "coupons", title: "Coupons", description: "Discount code performance and lifecycle export.", endpoint: "/admin/export/coupons?background=true" },
  { type: "audit-logs", title: "Audit Logs", description: "Security and moderation activity export.", endpoint: "/admin/export/audit-logs?background=true&days=30" },
];

export default function AdminExportsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminEmailManagement(user?.role);
  const [jobs, setJobs] = useState<Record<ExportType, ExportJobState>>({
    users: { status: "idle", jobId: null, filename: null, error: null },
    orders: { status: "idle", jobId: null, filename: null, error: null },
    products: { status: "idle", jobId: null, filename: null, error: null },
    coupons: { status: "idle", jobId: null, filename: null, error: null },
    "audit-logs": { status: "idle", jobId: null, filename: null, error: null },
  });

  const styles = useMemo(() => createStyles(theme), [theme]);

  const setJobState = (type: ExportType, patch: Partial<ExportJobState>) => {
    setJobs((prev) => ({
      ...prev,
      [type]: {
        ...prev[type],
        ...patch,
      },
    }));
  };

  const queueExport = async (definition: ExportDefinition) => {
    const current = jobs[definition.type];
    if (current.status === "queued" || current.status === "running") {
      return;
    }

    try {
      const job = await apiFetch<BackgroundJob<{ filename?: string }>>(definition.endpoint);
      setJobState(definition.type, {
        status: job.status,
        jobId: job.id,
        filename: null,
        error: null,
      });

      void trackBackgroundJob(job, {
        label: `${definition.title} export`,
        description: definition.description,
        route: "/admin/exports",
        queuedToast: `${definition.title} export queued`,
        successToast: false,
        errorToast: false,
        onUpdate: (update) => {
          setJobState(definition.type, {
            status: update.status,
            jobId: update.id,
            filename: update.result?.filename ?? null,
            error: update.error ?? null,
          });
        },
      })
        .then(async (finalJob) => {
          if (finalJob.status !== "completed") {
            throw new Error(finalJob.error || `${definition.title} export failed`);
          }

          const filename = finalJob.result?.filename || `${definition.type}.csv`;
          setJobState(definition.type, {
            status: finalJob.status,
            jobId: finalJob.id,
            filename,
            error: null,
          });
          await downloadBackgroundJobResult(finalJob.id, filename);
        })
        .catch((error) => {
          const message = error instanceof Error ? error.message : `${definition.title} export failed`;
          setJobState(definition.type, {
            status: "failed",
            error: message,
          });
          Alert.alert("Export failed", message);
        });
    } catch (error) {
      const message = error instanceof Error ? error.message : `${definition.title} export failed`;
      setJobState(definition.type, {
        status: "failed",
        error: message,
      });
      Alert.alert("Export failed", message);
    }
  };

  if (!canAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: "Exports" }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.surface0 }} contentContainerStyle={{ padding: 16, paddingBottom: 48 }}>
      <Stack.Screen options={{ title: "Exports" }} />

      <Text style={[s.title, { marginBottom: 4 }]}>Background Exports</Text>
      <Text style={[s.textMuted, { marginBottom: 16 }]}>Queue exports, keep watching progress while navigating, and share the CSV when it finishes.</Text>

      {EXPORTS.map((definition) => {
        const job = jobs[definition.type];
        const inFlight = job.status === "queued" || job.status === "running";
        const statusColor = job.status === "completed"
          ? theme.colors.success
          : job.status === "failed"
            ? theme.colors.danger
            : inFlight
              ? theme.colors.brand
              : theme.colors.textFaint;

        return (
          <View key={definition.type} style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={styles.cardHeader}>
              <View style={{ flex: 1, paddingRight: 12 }}>
                <Text style={[s.text, { fontWeight: "800", fontSize: theme.fontSize.md }]}>{definition.title}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, marginTop: 4 }]}>{definition.description}</Text>
              </View>
              <TouchableOpacity
                disabled={inFlight}
                onPress={() => queueExport(definition)}
                style={[styles.button, { backgroundColor: theme.colors.brand, opacity: inFlight ? 0.6 : 1 }]}
              >
                {inFlight ? <ActivityIndicator color={theme.colors.onBrand} size="small" /> : <Text style={styles.buttonText}>Export</Text>}
              </TouchableOpacity>
            </View>

            <View style={[styles.statusRow, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={{ color: statusColor, fontSize: theme.fontSize.xs, fontWeight: "800" }}>{String(job.status).toUpperCase()}</Text>
              {job.jobId ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Job {job.jobId}</Text> : null}
            </View>
            {job.filename ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginTop: 8 }]}>Artifact: {job.filename}</Text> : null}
            {job.error ? <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.xs, marginTop: 8 }}>{job.error}</Text> : null}
          </View>
        );
      })}
    </ScrollView>
  );
}

const createStyles = (theme: ReturnType<typeof import("@/theme").getTheme>) =>
  StyleSheet.create({
    card: {
      borderWidth: 1,
      borderRadius: 16,
      padding: 14,
      marginBottom: 12,
      gap: 10,
    },
    cardHeader: {
      flexDirection: "row",
      alignItems: "center",
    },
    button: {
      borderRadius: 12,
      paddingHorizontal: 14,
      paddingVertical: 10,
      minWidth: 92,
      alignItems: "center",
      justifyContent: "center",
    },
    buttonText: {
      color: theme.colors.onBrand,
      fontWeight: "800",
      fontSize: theme.fontSize.sm,
    },
    statusRow: {
      borderWidth: 1,
      borderRadius: 12,
      paddingHorizontal: 10,
      paddingVertical: 8,
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 8,
    },
  });