"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Database,
  Download,
  FileDown,
  Loader2,
  Search,
} from "@/lib/icons";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import {
  BackgroundJob,
  downloadBackgroundJobResult,
  trackBackgroundJob,
} from "@/lib/backgroundJobs";
import { useToastStore } from "@/lib/toastStore";
import { useAuth } from "@/lib/useAuth";

type ExportType =
  | "users"
  | "orders"
  | "products"
  | "coupons"
  | "audit-logs"
  | "supplier-payout-transfers"
  | "logistics-payout-transfers"
  | "cod-remittance-transfers";

interface ExportDefinition {
  type: ExportType;
  title: string;
  description: string;
  endpoint: string;
}

interface ExportJobState {
  jobId: string | null;
  status: string;
  filename: string | null;
  error: string | null;
  startedAt: string | null;
  finishedAt: string | null;
}

interface BackupRecord {
  filename: string;
  size_bytes: number;
  created_at: number | string;
  verified?: boolean;
  verification_method?: string | null;
  verified_at?: string | null;
  cloud_synced?: boolean;
  last_restore_drill_at?: string | null;
  last_restore_drill_status?: string | null;
  last_restore_drill_source?: string | null;
}

interface DatabaseColumnDetail {
  name: string;
  type: string;
  nullable: boolean;
  default: string | null;
  primary_key: boolean;
}

interface DatabaseForeignKeyRecord {
  constrained_columns: string[];
  referred_table: string | null;
  referred_columns: string[];
}

interface DatabaseTableRecord {
  name: string;
  row_count: number | null;
  column_count: number;
  columns: string[];
  column_details?: DatabaseColumnDetail[];
  primary_key: string[];
  indexes?: string[];
  index_count: number;
  foreign_keys?: DatabaseForeignKeyRecord[];
  foreign_key_count: number;
  orm_managed: boolean;
}

interface RuntimeServiceStatus {
  label: string;
  status: string;
  active: boolean;
  configured: boolean;
  role: string;
  detail: string;
  location?: string | null;
  exists?: boolean | null;
  host?: string | null;
  database?: string | null;
  driver?: string | null;
  toolchain_ready?: boolean | null;
  available?: boolean;
  backend?: string | null;
  fallback_mode?: string | null;
  shared_state?: boolean;
  backup_format?: string | null;
  backup_strategy?: string | null;
  handles?: string[];
}

interface DatabaseArchitecture {
  mode: string;
  primary_database_engine: string;
  summary: string;
  write_path: string;
  cache_path: string;
}

interface DatabaseOverview {
  status: string;
  inspected_at?: string;
  refresh_interval_seconds?: number;
  database: {
    engine: string;
    driver: string;
    location: string;
    connected: boolean;
    health: string;
    app_env: string;
    runtime_profile: string;
    alembic_version: string | null;
    backup_strategy: string;
  };
  architecture?: DatabaseArchitecture;
  services?: {
    sqlite: RuntimeServiceStatus;
    postgresql: RuntimeServiceStatus;
    redis: RuntimeServiceStatus;
  };
  backup: {
    enabled: boolean;
    artifact_count: number;
    latest_filename: string | null;
    latest_created_at: number | string | null;
    latest_verified: boolean | null;
    latest_size_bytes: number | null;
  };
  totals: {
    table_count: number;
    orm_model_table_count: number;
    managed_table_count: number;
    extra_table_count: number;
    missing_model_table_count: number;
  };
  tables_missing_from_database: string[];
  tables: DatabaseTableRecord[];
}

const EXPORTS: ExportDefinition[] = [
  { type: "users", title: "Users", description: "Customer, supplier, and staff account export.", endpoint: "/admin/export/users?background=true" },
  { type: "orders", title: "Orders", description: "Order totals, shipping, and payment status export.", endpoint: "/admin/export/orders?background=true" },
  { type: "products", title: "Products", description: "Catalog, pricing, stock, and supplier mapping export.", endpoint: "/admin/export/products?background=true" },
  { type: "coupons", title: "Coupons", description: "Discount code performance and lifecycle export.", endpoint: "/admin/export/coupons?background=true" },
  { type: "audit-logs", title: "Audit Logs", description: "Security and moderation activity export.", endpoint: "/admin/export/audit-logs?background=true" },
  { type: "supplier-payout-transfers", title: "Supplier Payout Transfers", description: "Bank-uploadable supplier payout file with recipient IBAN, SWIFT and beneficiary details pre-populated from verified Zozi bank accounts.", endpoint: "/admin/export/supplier-payout-transfers?background=true" },
  { type: "logistics-payout-transfers", title: "Logistics Payout Transfers", description: "Bank-uploadable logistics payout file with recipient IBAN, SWIFT and beneficiary details pre-populated from verified Zozi bank accounts.", endpoint: "/admin/export/logistics-payout-transfers?background=true" },
  { type: "cod-remittance-transfers", title: "COD Remittance Transfers", description: "Outstanding COD remittance instructions with Zozi treasury destination details and transfer references.", endpoint: "/admin/export/cod-remittance-transfers?background=true" },
];

const INITIAL_JOB_STATE: Record<ExportType, ExportJobState> = {
  users: { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  orders: { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  products: { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  coupons: { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  "audit-logs": { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  "supplier-payout-transfers": { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  "logistics-payout-transfers": { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
  "cod-remittance-transfers": { jobId: null, status: "idle", filename: null, error: null, startedAt: null, finishedAt: null },
};

function formatStatusLabel(status: string): string {
  if (status === "idle") return "Ready";
  return status.charAt(0).toUpperCase() + status.slice(1);
}

function statusTone(status: string): string {
  if (status === "completed") return "text-success";
  if (status === "failed") return "text-danger";
  if (status === "running" || status === "queued") return "text-primary";
  return "text-text-faint";
}

function statusIcon(status: string) {
  if (status === "completed") return <CheckCircle2 className="w-4 h-4 text-success" />;
  if (status === "failed") return <AlertCircle className="w-4 h-4 text-danger" />;
  if (status === "running" || status === "queued") return <Loader2 className="w-4 h-4 animate-spin text-primary" />;
  return <Clock3 className="w-4 h-4 text-text-faint" />;
}

function formatBackupDate(value?: number | string | null): string {
  if (value === null || value === undefined || value === "") return "-";
  const parsed = typeof value === "number"
    ? new Date(value < 1_000_000_000_000 ? value * 1000 : value)
    : new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleString();
}

function formatBackupSize(bytes?: number | null): string {
  if (!bytes || bytes < 1) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function formatRuntimeStatusLabel(status?: string | null): string {
  if (!status) return "Unknown";
  return status
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function runtimeStatusTone(status?: string | null): string {
  if (status === "active" || status === "ready") return "border-success/30 text-success";
  if (status === "degraded" || status === "configured") return "border-warning/30 text-warning";
  if (status === "supported" || status === "not_configured") return "border-border text-text-muted";
  return "border-danger/30 text-danger";
}

function formatTableCount(value: number | null): string {
  return value === null ? "scan failed" : `${value}`;
}

async function downloadResponseBlob(response: Response, filename: string) {
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(blobUrl);
}

export default function ExportsPanel() {
  const { user, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((state) => state.addToast);
  const isMountedRef = useRef(true);
  const [auditDays, setAuditDays] = useState("30");
  const [jobs, setJobs] = useState<Record<ExportType, ExportJobState>>(INITIAL_JOB_STATE);
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [backupsLoading, setBackupsLoading] = useState(false);
  const [backupActionKey, setBackupActionKey] = useState<string | null>(null);
  const [databaseOverview, setDatabaseOverview] = useState<DatabaseOverview | null>(null);
  const [databaseLoading, setDatabaseLoading] = useState(false);
  const [tableQuery, setTableQuery] = useState("");
  const isAdmin = user?.role === "admin";

  const loadBackups = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent && isMountedRef.current) {
      setBackupsLoading(true);
    }

    try {
      const response = await apiFetch("/admin/backup/list");
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }

      if (isMountedRef.current) {
        setBackups(Array.isArray(payload.backups) ? (payload.backups as BackupRecord[]) : []);
      }
    } catch (error) {
      if (!options?.silent) {
        addToast(error instanceof Error ? error.message : "Failed to load backups", "error");
      }
    } finally {
      if (isMountedRef.current) {
        setBackupsLoading(false);
      }
    }
  }, [addToast]);

  const loadDatabaseOverview = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent && isMountedRef.current) {
      setDatabaseLoading(true);
    }

    try {
      const response = await apiFetch("/admin/database/overview");
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }

      if (isMountedRef.current) {
        setDatabaseOverview(payload as DatabaseOverview);
      }
    } catch (error) {
      if (!options?.silent) {
        addToast(error instanceof Error ? error.message : "Failed to load database overview", "error");
      }
    } finally {
      if (isMountedRef.current) {
        setDatabaseLoading(false);
      }
    }
  }, [addToast]);

  useEffect(() => {
    isMountedRef.current = true;
    if (authLoading || !isAdmin) {
      return () => {
        isMountedRef.current = false;
      };
    }

    void Promise.all([
      loadBackups({ silent: true }),
      loadDatabaseOverview({ silent: true }),
    ]);
    return () => {
      isMountedRef.current = false;
    };
  }, [authLoading, isAdmin, loadBackups, loadDatabaseOverview]);

  useEffect(() => {
    if (authLoading || !isAdmin) return;

    const refreshIntervalSeconds = databaseOverview?.refresh_interval_seconds ?? 20;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void loadBackups({ silent: true });
      void loadDatabaseOverview({ silent: true });
    }, refreshIntervalSeconds * 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [authLoading, isAdmin, databaseOverview?.refresh_interval_seconds, loadBackups, loadDatabaseOverview]);

  const setJobState = (type: ExportType, patch: Partial<ExportJobState>) => {
    setJobs((prev) => ({
      ...prev,
      [type]: {
        ...prev[type],
        ...patch,
      },
    }));
  };

  const handleExport = async (definition: ExportDefinition) => {
    const type = definition.type;
    const inFlight = jobs[type].status === "queued" || jobs[type].status === "running";
    if (inFlight) return;

    try {
      const endpoint = definition.type === "audit-logs"
        ? `${definition.endpoint}&days=${encodeURIComponent(auditDays || "30")}`
        : definition.endpoint;
      const response = await apiFetch(endpoint);
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }

      const job = payload as BackgroundJob<{ filename?: string }>;
      if (isMountedRef.current) {
        setJobState(type, {
          jobId: job.id,
          status: job.status,
          error: null,
          filename: null,
          startedAt: job.started_at ?? null,
          finishedAt: job.finished_at ?? null,
        });
      }
      const finalJob = await trackBackgroundJob<{ filename?: string }>(job, {
        label: `${definition.title} export`,
        description: definition.description,
        route: "/admin/dashboard?tab=exports",
        queuedToast: `${definition.title} export queued`,
        successToast: false,
        errorToast: false,
        onUpdate: (update) => {
          if (!isMountedRef.current) return;
          setJobState(type, {
            jobId: update.id,
            status: update.status,
            error: update.error ?? null,
            filename: update.result?.filename ?? null,
            startedAt: update.started_at ?? null,
            finishedAt: update.finished_at ?? null,
          });
        },
      });

      if (finalJob.status !== "completed") {
        throw new Error(finalJob.error || `${definition.title} export failed`);
      }

      const filename = finalJob.result?.filename || `${definition.type}.csv`;
      await downloadBackgroundJobResult(finalJob.id, filename);
      if (isMountedRef.current) {
        setJobState(type, {
          jobId: finalJob.id,
          status: finalJob.status,
          filename,
          finishedAt: finalJob.finished_at ?? null,
        });
      }
      addToast(`${definition.title} export downloaded`, "success");
    } catch (error) {
      const message = error instanceof Error ? error.message : `${definition.title} export failed`;
      if (isMountedRef.current) {
        setJobState(type, { status: "failed", error: message });
      }
      addToast(message, "error");
    }
  };

  const handleTriggerBackup = async () => {
    setBackupActionKey("trigger");
    try {
      const response = await apiFetch("/admin/backup/trigger", { method: "POST" });
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }

      await Promise.all([
        loadBackups({ silent: true }),
        loadDatabaseOverview({ silent: true }),
      ]);
      addToast(`Backup created: ${String(payload.filename || "artifact ready")}`, "success");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Backup failed", "error");
    } finally {
      if (isMountedRef.current) {
        setBackupActionKey(null);
      }
    }
  };

  const handleDownloadBackup = async (filename: string) => {
    setBackupActionKey(`download:${filename}`);
    try {
      const response = await apiFetch(`/admin/backup/download/${encodeURIComponent(filename)}`);
      if (!response.ok) {
        const payload = await parseJsonResponse(response);
        throw new Error(getErrorMessage(payload ?? {}));
      }

      await downloadResponseBlob(response, filename);
      addToast(`Backup downloaded: ${filename}`, "success");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Backup download failed", "error");
    } finally {
      if (isMountedRef.current) {
        setBackupActionKey(null);
      }
    }
  };

  const handleRestoreDrill = async (filename?: string) => {
    const key = filename ? `drill:${filename}` : "drill:latest";
    setBackupActionKey(key);
    try {
      const suffix = filename ? `?filename=${encodeURIComponent(filename)}` : "";
      const response = await apiFetch(`/admin/backup/restore-drill${suffix}`, { method: "POST" });
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }

      await Promise.all([
        loadBackups({ silent: true }),
        loadDatabaseOverview({ silent: true }),
      ]);
      addToast(`Restore drill passed for ${String(payload.filename || "latest backup")}`, "success");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Restore drill failed", "error");
    } finally {
      if (isMountedRef.current) {
        setBackupActionKey(null);
      }
    }
  };

  const handleRunHealthCheck = async () => {
    if (authLoading || !isAdmin) return;

    await Promise.all([
      loadDatabaseOverview(),
      loadBackups({ silent: true }),
    ]);
  };

  // ── Reset demo data ───────────────────────────────────────────
  const [resetState, setResetState] = useState<"idle" | "confirm" | "running" | "done" | "error">("idle");
  const [resetResult, setResetResult] = useState<string | null>(null);

  const handleResetDemoData = useCallback(async () => {
    if (resetState === "running") return;
    setResetState("running");
    setResetResult(null);
    try {
      const response = await apiFetch("/admin/reset");
      const payload = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(payload?.detail || "Reset failed");
      }
      setResetResult(`✅ ${payload.detail} — ${payload.total_rows_deleted} rows cleared across ${payload.tables_cleared} tables.`);
      setResetState("done");
      addToast("Demo data reset complete", "success");
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Reset failed";
      setResetResult(`❌ ${msg}`);
      setResetState("error");
      addToast(msg, "error");
    }
  }, [resetState, addToast]);

  // Guard: only admins may use this panel (parent page also guards, but double-check here)
  if (authLoading || !isAdmin) return null;

  const latestBackup = backups[0] ?? null;
  const normalizedTableQuery = tableQuery.trim().toLowerCase();
  const lastInspectedAtLabel = formatBackupDate(databaseOverview?.inspected_at ?? null);
  const refreshIntervalSeconds = databaseOverview?.refresh_interval_seconds ?? 20;
  const architecture = databaseOverview?.architecture;
  const sqliteService = databaseOverview?.services?.sqlite ?? {
    label: "SQLite",
    status: databaseOverview?.database.engine === "sqlite" ? "active" : "supported",
    active: databaseOverview?.database.engine === "sqlite",
    configured: databaseOverview?.database.engine === "sqlite",
    role: "Primary relational database for local file-backed runtime when DATABASE_URL uses sqlite:///.",
    detail: databaseOverview?.database.engine === "sqlite"
      ? "This runtime is currently backed by SQLite."
      : "SQLite support is available for local runtime profiles.",
    location: databaseOverview?.database.location ?? null,
    backup_strategy: databaseOverview?.database.backup_strategy ?? "sqlite online backup API",
  };
  const postgresService = databaseOverview?.services?.postgresql ?? {
    label: "PostgreSQL",
    status: databaseOverview?.database.engine === "postgresql" ? "active" : "supported",
    active: databaseOverview?.database.engine === "postgresql",
    configured: databaseOverview?.database.engine === "postgresql",
    role: "Server-grade relational database option for production and multi-instance deployments.",
    detail: databaseOverview?.database.engine === "postgresql"
      ? "This runtime is currently backed by PostgreSQL."
      : "PostgreSQL is supported as the primary relational database when DATABASE_URL uses postgresql://.",
    host: null,
    database: null,
    backup_strategy: "pg_dump -Fc",
  };
  const redisService = databaseOverview?.services?.redis ?? {
    label: "Redis",
    status: "not_configured",
    active: false,
    configured: false,
    role: "Optional cache and shared ephemeral state store; it does not replace the primary relational database.",
    detail: "Redis detail becomes available when the backend serves the extended live dependency snapshot.",
    backend: "unknown",
    fallback_mode: null,
  };
  const filteredTables = (databaseOverview?.tables ?? []).filter((table) => {
    if (!normalizedTableQuery) return true;
    const searchableColumns = table.columns.join(" ").toLowerCase();
    return table.name.toLowerCase().includes(normalizedTableQuery) || searchableColumns.includes(normalizedTableQuery);
  });

  return (
    <div className="space-y-6">
      <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-text">Background Exports</h2>
          <p className="text-xs text-text-faint">
            Queue large CSV exports, download payout transfer files, and manage verified database backup artifacts from one admin workspace.
          </p>
        </div>
        <label className="flex flex-col gap-1 text-xs text-text-faint">
          Audit log range (days)
          <input
            value={auditDays}
            onChange={(event) => setAuditDays(event.target.value.replace(/[^0-9]/g, ""))}
            className="w-28 rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs text-text focus:border-primary focus:outline-none"
            inputMode="numeric"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="theme-card rounded-xl border p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="mb-1 flex items-center gap-2">
                <Database className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold text-text">Database Operations</h3>
              </div>
              <p className="text-xs text-text-faint">
                Live database health, runtime topology, and schema inspection from one condensed admin workspace.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold text-text-muted">
                Auto-sync every {refreshIntervalSeconds}s
              </span>
              <span className="rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold text-text-muted">
                Last sync {lastInspectedAtLabel}
              </span>
              <button
                type="button"
                onClick={() => void handleRunHealthCheck()}
                aria-label="Run database health check"
                disabled={databaseLoading}
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-4 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2 disabled:opacity-50"
              >
                {databaseLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                Health Check
              </button>
              <button
                type="button"
                onClick={() => latestBackup && void handleDownloadBackup(latestBackup.filename)}
                aria-label="Download latest database backup"
                disabled={!latestBackup || backupActionKey !== null}
                className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-4 py-2 text-xs font-semibold disabled:opacity-50"
              >
                {backupActionKey === `download:${latestBackup?.filename ?? ""}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Download Latest Backup
              </button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,0.85fr)]">
            <div className="rounded-xl border border-border bg-surface-1 p-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Runtime Topology</p>
                  <p className="mt-1 text-xs text-text-muted">
                    {architecture?.summary || "SQLite or PostgreSQL is the primary source of truth, while Redis handles cache and shared runtime state."}
                  </p>
                </div>
                <span className="rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold text-text-muted">
                  Primary {architecture?.primary_database_engine?.toUpperCase() || databaseOverview?.database.engine?.toUpperCase() || "-"}
                </span>
              </div>

              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
                <div className="rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-text">SQLite</p>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${runtimeStatusTone(sqliteService.status)}`}>
                      {formatRuntimeStatusLabel(sqliteService.status)}
                    </span>
                  </div>
                  <p className="mt-2">{sqliteService.detail || "-"}</p>
                  <p className="mt-2">Location: {sqliteService.location || "-"}</p>
                  <p className="mt-1">Backup: {sqliteService.backup_strategy || "-"}</p>
                </div>

                <div className="rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-text">PostgreSQL</p>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${runtimeStatusTone(postgresService.status)}`}>
                      {formatRuntimeStatusLabel(postgresService.status)}
                    </span>
                  </div>
                  <p className="mt-2">{postgresService.detail || "-"}</p>
                  <p className="mt-2">Host: {postgresService.host || "not active"}</p>
                  <p className="mt-1">Backup: {postgresService.backup_strategy || "pg_dump -Fc"}</p>
                </div>

                <div className="rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-text">Redis</p>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${runtimeStatusTone(redisService.status)}`}>
                      {formatRuntimeStatusLabel(redisService.status)}
                    </span>
                  </div>
                  <p className="mt-2">{redisService.detail || "-"}</p>
                  <p className="mt-2">Backend: {redisService.backend || "-"}</p>
                  <p className="mt-1">Fallback: {redisService.fallback_mode || "none"}</p>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                <p><span className="font-semibold text-text">Write path:</span> {architecture?.write_path || "All canonical writes go to the active relational database."}</p>
                <p className="mt-2"><span className="font-semibold text-text">Cache path:</span> {architecture?.cache_path || "Redis only accelerates cache and shared ephemeral state."}</p>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-surface-1 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Live Summary</p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded-xl border border-border bg-background/60 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Health</p>
                  <div className="mt-2 flex items-center gap-2">
                    {databaseOverview?.status === "healthy" ? <CheckCircle2 className="w-4 h-4 text-success" /> : <AlertCircle className="w-4 h-4 text-danger" />}
                    <p className="text-sm font-semibold text-text">{databaseOverview?.status === "healthy" ? "Healthy" : databaseLoading ? "Checking" : "Unavailable"}</p>
                  </div>
                  <p className="mt-2 text-xs text-text-muted">{databaseOverview?.database.engine?.toUpperCase() || "-"} via {databaseOverview?.database.driver || "-"}</p>
                </div>
                <div className="rounded-xl border border-border bg-background/60 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Schema</p>
                  <p className="mt-2 text-sm font-semibold text-text">{databaseOverview?.totals.table_count ?? 0} tables</p>
                  <p className="mt-2 text-xs text-text-muted">Alembic {databaseOverview?.database.alembic_version || "not tracked"}</p>
                </div>
                <div className="rounded-xl border border-border bg-background/60 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Backups</p>
                  <p className="mt-2 text-sm font-semibold text-text">{databaseOverview?.backup.artifact_count ?? backups.length}</p>
                  <p className="mt-2 text-xs text-text-muted">Latest {databaseOverview?.backup.latest_filename || latestBackup?.filename || "-"}</p>
                </div>
                <div className="rounded-xl border border-border bg-background/60 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Drift</p>
                  <p className="mt-2 text-sm font-semibold text-text">{databaseOverview?.totals.missing_model_table_count ?? 0} missing</p>
                  <p className="mt-2 text-xs text-text-muted">Managed {databaseOverview?.totals.managed_table_count ?? 0}</p>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                <p><span className="font-semibold text-text">Database location:</span> {databaseOverview?.database.location || "-"}</p>
                <p className="mt-2"><span className="font-semibold text-text">Environment:</span> {databaseOverview?.database.app_env || "-"} / {databaseOverview?.database.runtime_profile || "-"}</p>
                <p className="mt-2"><span className="font-semibold text-text">Backup strategy:</span> {databaseOverview?.database.backup_strategy || "-"}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="theme-card rounded-xl border p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <FileDown className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold text-text">Database Backups</h3>
            </div>
            <p className="text-xs text-text-faint">
              Trigger a hot backup, download the latest verified artifact, and run restore drills before depending on a recovery point.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void loadBackups()}
              aria-label="Refresh backup inventory"
              disabled={backupsLoading || backupActionKey === "trigger" || backupActionKey === "drill:latest"}
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-4 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2 disabled:opacity-50"
            >
              {backupsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clock3 className="w-4 h-4" />}
              Refresh
            </button>
            <button
              type="button"
              onClick={() => void handleRestoreDrill()}
              aria-label="Run restore drill for latest backup"
              disabled={!latestBackup || backupsLoading || backupActionKey !== null}
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-4 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2 disabled:opacity-50"
            >
              {backupActionKey === "drill:latest" ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              Restore Drill
            </button>
            <button
              type="button"
              onClick={() => void handleTriggerBackup()}
              aria-label="Trigger database backup"
              disabled={backupActionKey !== null}
              className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-4 py-2 text-xs font-semibold disabled:opacity-50"
            >
              {backupActionKey === "trigger" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Trigger Backup
            </button>
          </div>
        </div>

          <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1.95fr)]">
          <div className="rounded-xl border border-border bg-surface-1 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Latest Recovery Point</p>
            {latestBackup ? (
              <div className="mt-3 space-y-2 text-xs text-text-muted">
                <p className="text-sm font-semibold text-text">{latestBackup.filename}</p>
                <p>Created: {formatBackupDate(latestBackup.created_at)}</p>
                <p>Size: {formatBackupSize(latestBackup.size_bytes)}</p>
                <p>
                  Verification: {latestBackup.verified ? "Verified" : "Pending"}
                  {latestBackup.verification_method ? ` via ${latestBackup.verification_method}` : ""}
                </p>
                <p>
                  Restore drill: {latestBackup.last_restore_drill_status ? latestBackup.last_restore_drill_status : "Not run yet"}
                </p>
                <p>
                  Cloud sync: {latestBackup.cloud_synced ? "Enabled" : "Local only"}
                </p>
              </div>
            ) : (
              <p className="mt-3 text-xs text-text-faint">No backup artifacts found yet. Trigger the first backup to establish a recovery point.</p>
            )}
          </div>

          <div className="rounded-xl border border-border bg-surface-1 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Backup Library</p>
                <p className="mt-1 text-xs text-text-muted">Newest files are listed first so the most recent recovery point stays at the top.</p>
              </div>
              <span className="rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold text-text-muted">
                {backups.length} file{backups.length === 1 ? "" : "s"}
              </span>
            </div>

            <div className="mt-4 space-y-3">
              {backupsLoading && backups.length === 0 ? (
                <div className="flex items-center gap-2 rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading backup inventory...
                </div>
              ) : backups.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">
                  No backup files are available yet.
                </div>
              ) : (
                backups.map((backup) => {
                  const downloadKey = `download:${backup.filename}`;
                  const drillKey = `drill:${backup.filename}`;
                  return (
                    <div
                      key={backup.filename}
                      data-backup-filename={backup.filename}
                      className="rounded-xl border border-border bg-background/60 p-2.5"
                    >
                      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                        <div className="min-w-0 space-y-1 text-xs text-text-muted">
                          <p className="truncate text-sm font-semibold text-text">{backup.filename}</p>
                          <p>Created: {formatBackupDate(backup.created_at)}</p>
                          <p>Size: {formatBackupSize(backup.size_bytes)}</p>
                          <p>
                            Verification: {backup.verified ? "Verified" : "Pending"}
                            {backup.verification_method ? ` via ${backup.verification_method}` : ""}
                          </p>
                          <p>
                            Last drill: {backup.last_restore_drill_status ? backup.last_restore_drill_status : "Not run"}
                            {backup.last_restore_drill_at ? ` on ${formatBackupDate(backup.last_restore_drill_at)}` : ""}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-2 md:justify-end">
                          <button
                            type="button"
                            onClick={() => void handleRestoreDrill(backup.filename)}
                            aria-label={`Run restore drill for ${backup.filename}`}
                            disabled={backupActionKey !== null}
                            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2 disabled:opacity-50"
                          >
                            {backupActionKey === drillKey ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                            Drill
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleDownloadBackup(backup.filename)}
                            aria-label={`Download backup ${backup.filename}`}
                            disabled={backupActionKey !== null}
                            className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-2 text-xs font-semibold disabled:opacity-50"
                          >
                            {backupActionKey === downloadKey ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                            Download
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
      </div>

      <div className="theme-card rounded-xl border p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <FileDown className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold text-text">Database Tables</h3>
            </div>
            <p className="text-xs text-text-faint">
              Full table visibility for operational handling, including row counts, column lists, primary keys, indexes, and foreign-key coverage.
            </p>
          </div>

          <label className="flex min-w-60 items-center gap-2 rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs text-text-muted">
            <Search className="w-4 h-4" />
            <input
              value={tableQuery}
              onChange={(event) => setTableQuery(event.target.value)}
              aria-label="Search database tables"
              placeholder="Search tables or columns"
              className="w-full bg-transparent text-xs text-text outline-none placeholder:text-text-faint"
            />
          </label>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 xl:grid-cols-5">
          <div className="rounded-xl border border-border bg-surface-1 p-2.5 text-xs text-text-muted">
            <p className="font-semibold text-text">Visible tables</p>
            <p className="mt-1">{filteredTables.length}</p>
          </div>
          <div className="rounded-xl border border-border bg-surface-1 p-2.5 text-xs text-text-muted">
            <p className="font-semibold text-text">ORM models</p>
            <p className="mt-1">{databaseOverview?.totals.orm_model_table_count ?? 0}</p>
          </div>
          <div className="rounded-xl border border-border bg-surface-1 p-2.5 text-xs text-text-muted">
            <p className="font-semibold text-text">Managed tables</p>
            <p className="mt-1">{databaseOverview?.totals.managed_table_count ?? 0}</p>
          </div>
          <div className="rounded-xl border border-border bg-surface-1 p-2.5 text-xs text-text-muted">
            <p className="font-semibold text-text">Extra tables</p>
            <p className="mt-1">{databaseOverview?.totals.extra_table_count ?? 0}</p>
          </div>
          <div className="rounded-xl border border-border bg-surface-1 p-2.5 text-xs text-text-muted">
            <p className="font-semibold text-text">Missing ORM tables</p>
            <p className="mt-1">{databaseOverview?.totals.missing_model_table_count ?? 0}</p>
          </div>
        </div>

        {Boolean(databaseOverview?.tables_missing_from_database.length) && (
          <div className="mt-3 rounded-xl border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-text-muted">
            <span className="font-semibold text-text">Missing ORM tables:</span> {databaseOverview?.tables_missing_from_database.join(", ")}
          </div>
        )}

        <div className="mt-4 space-y-3">
          {databaseLoading && !databaseOverview ? (
            <div className="flex items-center gap-2 rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading database inventory...
            </div>
          ) : filteredTables.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">
              No tables match the current search.
            </div>
          ) : (
            filteredTables.map((table) => (
              (() => {
                const columnDetails = table.column_details ?? table.columns.map((columnName) => ({
                  name: columnName,
                  type: "type unavailable",
                  nullable: true,
                  default: null,
                  primary_key: table.primary_key.includes(columnName),
                }));
                const indexes = table.indexes ?? [];
                const foreignKeys = table.foreign_keys ?? [];

                return (
                  <details
                    key={table.name}
                    data-database-table={table.name}
                    className="rounded-xl border border-border bg-surface-1"
                  >
                    <summary className="flex cursor-pointer list-none flex-col gap-3 px-3 py-3 lg:flex-row lg:items-center lg:justify-between">
                      <div className="min-w-0 space-y-2 text-xs text-text-muted">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-sm font-semibold text-text">{table.name}</p>
                          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${table.orm_managed ? "border-success/30 text-success" : "border-border text-text-muted"}`}>
                            {table.orm_managed ? "ORM managed" : "Database only"}
                          </span>
                          {table.primary_key.length > 0 && (
                            <span className="rounded-full border border-border px-2 py-0.5 text-[10px] font-semibold text-text-muted">
                              PK {table.primary_key.join(", ")}
                            </span>
                          )}
                        </div>
                        <p className="wrap-break-word text-text-muted">{table.columns.slice(0, 6).join(", ")}{table.columns.length > 6 ? ` +${table.columns.length - 6} more` : ""}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px] text-text-muted sm:grid-cols-4 lg:min-w-110">
                        <div className="rounded-xl border border-border bg-background/60 px-2.5 py-2">
                          <p className="font-semibold text-text">Rows</p>
                          <p className="mt-1">{formatTableCount(table.row_count)}</p>
                        </div>
                        <div className="rounded-xl border border-border bg-background/60 px-2.5 py-2">
                          <p className="font-semibold text-text">Columns</p>
                          <p className="mt-1">{table.column_count}</p>
                        </div>
                        <div className="rounded-xl border border-border bg-background/60 px-2.5 py-2">
                          <p className="font-semibold text-text">Indexes</p>
                          <p className="mt-1">{table.index_count}</p>
                        </div>
                        <div className="rounded-xl border border-border bg-background/60 px-2.5 py-2">
                          <p className="font-semibold text-text">FKs</p>
                          <p className="mt-1">{table.foreign_key_count}</p>
                        </div>
                      </div>
                    </summary>

                    <div className="border-t border-border px-3 py-3">
                      <div className="grid grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,0.8fr)_minmax(0,1fr)]">
                        <div className="rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                          <p className="font-semibold text-text">Column details</p>
                          <div className="mt-3 space-y-2">
                            {columnDetails.map((column) => (
                              <div key={`${table.name}:${column.name}`} className="rounded-lg border border-border px-2.5 py-2">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="font-semibold text-text">{column.name}</span>
                                  <span className="rounded-full border border-border px-2 py-0.5 text-[10px] font-semibold text-text-muted">{column.type}</span>
                                  {column.primary_key && <span className="rounded-full border border-success/30 px-2 py-0.5 text-[10px] font-semibold text-success">PK</span>}
                                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${column.nullable ? "border-border text-text-muted" : "border-warning/30 text-warning"}`}>
                                    {column.nullable ? "Nullable" : "Required"}
                                  </span>
                                </div>
                                <p className="mt-2 wrap-break-word">Default: {column.default || "-"}</p>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                          <p className="font-semibold text-text">Indexes</p>
                          <div className="mt-3 space-y-2">
                            {indexes.length ? indexes.map((indexName) => (
                              <div key={`${table.name}:${indexName}`} className="rounded-lg border border-border px-2.5 py-2 wrap-break-word">
                                {indexName}
                              </div>
                            )) : (
                              <div className="rounded-lg border border-dashed border-border px-2.5 py-2">No secondary indexes reported.</div>
                            )}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border bg-background/60 p-3 text-xs text-text-muted">
                          <p className="font-semibold text-text">Foreign keys</p>
                          <div className="mt-3 space-y-2">
                            {foreignKeys.length ? foreignKeys.map((foreignKey, index) => (
                              <div key={`${table.name}:fk:${index}`} className="rounded-lg border border-border px-2.5 py-2">
                                <p className="font-semibold text-text">{foreignKey.constrained_columns.join(", ") || "-"}</p>
                                <p className="mt-1 wrap-break-word">References {foreignKey.referred_table || "-"} ({foreignKey.referred_columns.join(", ") || "-"})</p>
                              </div>
                            )) : (
                              <div className="rounded-lg border border-dashed border-border px-2.5 py-2">No foreign keys reported.</div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </details>
                );
              })()
            ))
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {EXPORTS.map((definition) => {
          const job = jobs[definition.type];
          const inFlight = job.status === "queued" || job.status === "running";

          return (
            <div key={definition.type} className="theme-card rounded-xl border p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="mb-1 flex items-center gap-2">
                    <FileDown className="w-4 h-4 text-primary" />
                    <h3 className="text-base font-semibold text-text">{definition.title}</h3>
                  </div>
                  <p className="text-xs text-text-faint">{definition.description}</p>
                </div>
                <button
                  onClick={() => void handleExport(definition)}
                  aria-label={`Export ${definition.title}`}
                  disabled={inFlight || (definition.type === "audit-logs" && !auditDays)}
                  className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-4 py-2 text-xs font-semibold disabled:opacity-50"
                >
                  {inFlight ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  {inFlight ? "Processing" : "Export"}
                </button>
              </div>

              <div className="mt-4 rounded-xl border border-border bg-surface-1 p-4">
                <div className="flex items-center gap-2 text-xs font-medium text-text">
                  {statusIcon(job.status)}
                  <span className={statusTone(job.status)}>{formatStatusLabel(job.status)}</span>
                </div>
                {job.jobId && <p className="mt-2 text-xs text-text-faint">Job ID: {job.jobId}</p>}
                {job.filename && <p className="mt-2 text-xs text-text-faint">Last file: {job.filename}</p>}
                {job.error && <p className="mt-2 text-xs text-danger">{job.error}</p>}
                {job.startedAt && <p className="mt-2 text-xs text-text-faint">Started: {new Date(job.startedAt).toLocaleString()}</p>}
                {job.finishedAt && <p className="mt-1 text-xs text-text-faint">Finished: {new Date(job.finishedAt).toLocaleString()}</p>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Reset Demo Data */}
      <div className="theme-card rounded-xl border border-danger/20 p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-danger" />
              <h3 className="text-base font-semibold text-text">Reset Demo Data</h3>
            </div>
            <p className="text-xs text-text-faint">
              Clear all non-essential seed data — orders, products, reviews, communications,
              coupons, and non-admin users. Admin accounts are preserved. This action is
              only available in development/test environments.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {resetState === "idle" && (
              <button
                onClick={() => setResetState("confirm")}
                className="inline-flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-2 text-xs font-semibold text-danger transition-colors hover:bg-danger/20"
              >
                <AlertCircle className="w-4 h-4" />
                Reset Demo Data
              </button>
            )}
            {resetState === "confirm" && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-danger font-medium">Are you sure?</span>
                <button
                  onClick={handleResetDemoData}
                  className="inline-flex items-center gap-2 rounded-xl bg-danger text-white px-4 py-2 text-xs font-semibold hover:bg-danger/90 transition-colors"
                >
                  Yes, Reset Everything
                </button>
                <button
                  onClick={() => setResetState("idle")}
                  className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-4 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2"
                >
                  Cancel
                </button>
              </div>
            )}
            {resetState === "running" && (
              <button disabled className="inline-flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-2 text-xs font-semibold text-danger opacity-60 cursor-not-allowed">
                <Loader2 className="w-4 h-4 animate-spin" />
                Resetting…
              </button>
            )}
            {(resetState === "done" || resetState === "error") && (
              <button
                onClick={() => { setResetState("idle"); setResetResult(null); }}
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-1 px-4 py-2 text-xs font-semibold text-text transition-colors hover:bg-surface-2"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
        {resetResult && (
          <div className={`mt-3 rounded-xl border p-3 text-xs ${
            resetState === "done"
              ? "border-success/30 bg-success/10 text-success"
              : "border-danger/30 bg-danger/10 text-danger"
          }`}>
            {resetResult}
          </div>
        )}
      </div>
    </div>
  );
}
