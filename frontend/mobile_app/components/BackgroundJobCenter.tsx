import React, { useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useRouter } from "expo-router";

import { trackBackgroundJob } from "@/lib/backgroundJobs";
import { useBackgroundJobStore } from "@/lib/backgroundJobStore";
import { useThemeStore } from "@/lib/themeStore";

function formatTimestamp(value?: string | null): string {
  if (!value) return "Just now";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Just now";
  return date.toLocaleString();
}

export default function BackgroundJobCenter() {
  const router = useRouter();
  const { theme } = useThemeStore();
  const jobs = useBackgroundJobStore((state) => state.jobs);
  const removeJob = useBackgroundJobStore((state) => state.removeJob);
  const clearFinishedJobs = useBackgroundJobStore((state) => state.clearFinishedJobs);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    jobs.forEach((job) => {
      if (job.status === "queued" || job.status === "running") {
        void trackBackgroundJob(job, {
          label: job.label,
          description: job.description ?? undefined,
          route: job.route ?? undefined,
          queuedToast: false,
          successToast: false,
          errorToast: false,
        }).catch(() => undefined);
      }
    });
  }, [jobs]);

  const sortedJobs = useMemo(
    () => [...jobs].sort((left, right) => Date.parse(right.updated_at_local) - Date.parse(left.updated_at_local)),
    [jobs],
  );
  const activeCount = sortedJobs.filter((job) => job.status === "queued" || job.status === "running").length;

  if (sortedJobs.length === 0) {
    return null;
  }

  return (
    <View pointerEvents="box-none" style={styles.wrapper}>
      <TouchableOpacity
        activeOpacity={0.92}
        onPress={() => setOpen((current) => !current)}
        style={[
          styles.pill,
          {
            backgroundColor: theme.colors.surface1,
            borderColor: theme.colors.border,
          },
        ]}
      >
        <View style={[styles.dot, { backgroundColor: activeCount > 0 ? theme.colors.brand : theme.colors.textFaint }]} />
        <View style={{ flex: 1 }}>
          <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: theme.fontSize.sm }}>Background Jobs</Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>
            {activeCount > 0 ? `${activeCount} active` : `${sortedJobs.length} recent`}
          </Text>
        </View>
        <Text style={{ color: theme.colors.textMuted, fontWeight: "700" }}>{open ? "▾" : "▴"}</Text>
      </TouchableOpacity>

      {open ? (
        <View
          style={[
            styles.panel,
            {
              backgroundColor: theme.colors.surface1,
              borderColor: theme.colors.border,
            },
          ]}
        >
          <View style={styles.headerRow}>
            <View style={{ flex: 1, paddingRight: 10 }}>
              <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: theme.fontSize.sm }}>Progress & History</Text>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>
                Jobs continue updating while you move between screens.
              </Text>
            </View>
            <TouchableOpacity onPress={() => clearFinishedJobs()}>
              <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.xs }}>Clear done</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={{ maxHeight: 260 }} contentContainerStyle={{ gap: 8 }}>
            {sortedJobs.map((job) => {
              const statusColor = job.status === "completed"
                ? theme.colors.success
                : job.status === "failed"
                  ? theme.colors.danger
                  : theme.colors.brand;
              const route = job.route;

              return (
                <View
                  key={job.id}
                  style={[
                    styles.jobCard,
                    {
                      backgroundColor: theme.colors.surface2,
                      borderColor: theme.colors.border,
                    },
                  ]}
                >
                  <View style={styles.headerRow}>
                    <View style={{ flex: 1, paddingRight: 10 }}>
                      <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.sm }} numberOfLines={1}>
                        {job.label}
                      </Text>
                      {job.description ? (
                        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }} numberOfLines={2}>
                          {job.description}
                        </Text>
                      ) : null}
                    </View>
                    <TouchableOpacity onPress={() => removeJob(job.id)}>
                      <Text style={{ color: theme.colors.textFaint, fontWeight: "700" }}>✕</Text>
                    </TouchableOpacity>
                  </View>

                  <View style={styles.metaRow}>
                    <View style={[styles.badge, { backgroundColor: `${statusColor}22` }]}>
                      <Text style={{ color: statusColor, fontWeight: "700", fontSize: 10 }}>{String(job.status).toUpperCase()}</Text>
                    </View>
                    <Text style={{ color: theme.colors.textFaint, fontSize: theme.fontSize.xs }}>{job.kind}</Text>
                    {route ? (
                      <TouchableOpacity onPress={() => router.push(route as never)}>
                        <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>Open</Text>
                      </TouchableOpacity>
                    ) : null}
                  </View>

                  {job.error ? (
                    <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.xs, marginTop: 6 }}>{job.error}</Text>
                  ) : null}
                  {typeof job.result === "object" && job.result && "filename" in job.result && typeof job.result.filename === "string" ? (
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 6 }}>
                      Artifact: {job.result.filename}
                    </Text>
                  ) : null}
                  <Text style={{ color: theme.colors.textFaint, fontSize: 10, marginTop: 6 }}>
                    Updated {formatTimestamp(job.updated_at_local)}
                  </Text>
                </View>
              );
            })}
          </ScrollView>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: "absolute",
    left: 14,
    right: 14,
    bottom: 150,
    zIndex: 9998,
  },
  pill: {
    borderWidth: 1,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  panel: {
    marginTop: 8,
    borderWidth: 1,
    borderRadius: 22,
    padding: 12,
    gap: 10,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  jobCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 10,
  },
  metaRow: {
    marginTop: 8,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flexWrap: "wrap",
  },
  badge: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
});