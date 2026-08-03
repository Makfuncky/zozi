import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockTrackBackgroundJob = jest.fn();
const mockDownloadBackgroundJobResult = jest.fn();
const mockAddToast = jest.fn();
let currentAuthState: Record<string, unknown>;

let currentBackups: Array<Record<string, unknown>> = [];
let currentDatabaseOverview: Record<string, unknown>;

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  parseJsonResponse: async (response: { json?: () => Promise<unknown> }) => (response.json ? response.json() : {}),
  getErrorMessage: (payload: any) => payload?.detail || payload?.message || "Request failed",
}));

jest.mock("@/lib/backgroundJobs", () => ({
  trackBackgroundJob: (...args: any[]) => mockTrackBackgroundJob(...args),
  downloadBackgroundJobResult: (...args: any[]) => mockDownloadBackgroundJobResult(...args),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: (state: { addToast: typeof mockAddToast }) => unknown) => selector({ addToast: mockAddToast }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => currentAuthState,
}));

import ExportsPanel from "@/app/admin/dashboard/_components/ExportsPanel";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Admin exports panel backup controls", () => {
  beforeAll(() => {
    Object.defineProperty(global.URL, "createObjectURL", {
      writable: true,
      value: jest.fn(() => "blob:backup"),
    });
    Object.defineProperty(global.URL, "revokeObjectURL", {
      writable: true,
      value: jest.fn(),
    });
    Object.defineProperty(HTMLAnchorElement.prototype, "click", {
      writable: true,
      value: jest.fn(),
    });
  });

  beforeEach(() => {
    jest.clearAllMocks();
    currentAuthState = { user: { id: 1, role: "admin", username: "admin" }, isLoading: false };
    currentBackups = [
      {
        filename: "backup_20260416_101500_new.sqlite",
        size_bytes: 24576,
        created_at: 1713262500,
        verified: true,
        verification_method: "sqlite_integrity_check",
        last_restore_drill_status: "passed",
        last_restore_drill_at: "2026-04-16T10:20:00Z",
        cloud_synced: false,
      },
      {
        filename: "backup_20260415_090000_old.sqlite",
        size_bytes: 12288,
        created_at: 1713168000,
        verified: true,
        verification_method: "sqlite_integrity_check",
        last_restore_drill_status: null,
        last_restore_drill_at: null,
        cloud_synced: false,
      },
    ];
    currentDatabaseOverview = {
      status: "healthy",
      inspected_at: "2026-04-16T10:32:00Z",
      refresh_interval_seconds: 20,
      database: {
        engine: "sqlite",
        driver: "pysqlite",
        location: "backend/zozi.db",
        connected: true,
        health: "ok",
        app_env: "development",
        runtime_profile: "default",
        alembic_version: "f1a2b3c4d5e6",
        backup_strategy: "sqlite online backup API",
      },
      architecture: {
        mode: "single_primary_relational_with_optional_cache",
        primary_database_engine: "sqlite",
        summary: "SQLite or PostgreSQL is the single source of truth for business data at runtime, selected by DATABASE_URL. Redis only accelerates cache and shared ephemeral state.",
        write_path: "All canonical reads and writes go to the active relational database engine.",
        cache_path: "Redis supplements the relational database for cache, token blacklist, and shared runtime state when available.",
      },
      services: {
        sqlite: {
          label: "SQLite",
          status: "active",
          active: true,
          configured: true,
          role: "Primary relational database for local file-backed runtime when DATABASE_URL uses sqlite:///.",
          detail: "This runtime is currently backed by a local SQLite database file.",
        location: "sqlite:///zozi.db",
          exists: true,
          backup_format: ".sqlite",
          backup_strategy: "sqlite online backup API",
          handles: ["canonical relational data", "schema introspection", "local file backups"],
        },
        postgresql: {
          label: "PostgreSQL",
          status: "supported",
          active: false,
          configured: false,
          role: "Server-grade relational database option for production and multi-instance deployments.",
          detail: "PostgreSQL is supported as the primary relational database when DATABASE_URL uses postgresql://.",
          host: null,
          database: null,
          driver: null,
          toolchain_ready: null,
          backup_format: ".pgdump",
          backup_strategy: "pg_dump -Fc",
          handles: ["canonical relational data", "multi-instance production persistence", "compressed logical backups"],
        },
        redis: {
          label: "Redis",
          status: "degraded",
          active: false,
          configured: true,
          available: false,
          role: "Optional cache and shared ephemeral state store; it does not replace the primary relational database.",
          detail: "Redis is not connected; the app falls back to in-memory state for cache-like behavior in this runtime.",
          backend: "memory_fallback",
          fallback_mode: "memory",
          shared_state: false,
          handles: ["token blacklist", "shared cache", "background job coordination"],
        },
      },
      backup: {
        enabled: false,
        artifact_count: 2,
        latest_filename: "backup_20260416_101500_new.sqlite",
        latest_created_at: 1713262500,
        latest_verified: true,
        latest_size_bytes: 24576,
      },
      totals: {
        table_count: 4,
        orm_model_table_count: 3,
        managed_table_count: 3,
        extra_table_count: 1,
        missing_model_table_count: 0,
      },
      tables_missing_from_database: [],
      tables: [
        {
          name: "users",
          row_count: 12,
          column_count: 8,
          columns: ["id", "email", "username", "role", "created_at"],
          column_details: [
            { name: "id", type: "INTEGER", nullable: false, default: null, primary_key: true },
            { name: "email", type: "VARCHAR", nullable: false, default: null, primary_key: false },
            { name: "username", type: "VARCHAR", nullable: false, default: null, primary_key: false },
          ],
          primary_key: ["id"],
          indexes: ["ix_users_email", "ix_users_username"],
          index_count: 2,
          foreign_keys: [],
          foreign_key_count: 0,
          orm_managed: true,
        },
        {
          name: "orders",
          row_count: 8,
          column_count: 10,
          columns: ["id", "user_id", "status", "total_amount"],
          column_details: [
            { name: "id", type: "INTEGER", nullable: false, default: null, primary_key: true },
            { name: "user_id", type: "INTEGER", nullable: false, default: null, primary_key: false },
            { name: "status", type: "VARCHAR", nullable: false, default: null, primary_key: false },
          ],
          primary_key: ["id"],
          indexes: ["ix_orders_user_id", "ix_orders_status", "ix_orders_created_at"],
          index_count: 3,
          foreign_keys: [
            { constrained_columns: ["user_id"], referred_table: "users", referred_columns: ["id"] },
          ],
          foreign_key_count: 1,
          orm_managed: true,
        },
        {
          name: "audit_logs",
          row_count: 14,
          column_count: 9,
          columns: ["id", "action", "user_id", "created_at"],
          column_details: [
            { name: "id", type: "INTEGER", nullable: false, default: null, primary_key: true },
            { name: "action", type: "VARCHAR", nullable: false, default: null, primary_key: false },
          ],
          primary_key: ["id"],
          indexes: ["ix_audit_logs_action", "ix_audit_logs_created_at"],
          index_count: 2,
          foreign_keys: [
            { constrained_columns: ["user_id"], referred_table: "users", referred_columns: ["id"] },
          ],
          foreign_key_count: 1,
          orm_managed: true,
        },
        {
          name: "alembic_version",
          row_count: 1,
          column_count: 1,
          columns: ["version_num"],
          column_details: [
            { name: "version_num", type: "VARCHAR", nullable: false, default: null, primary_key: false },
          ],
          primary_key: [],
          indexes: [],
          index_count: 0,
          foreign_keys: [],
          foreign_key_count: 0,
          orm_managed: false,
        },
      ],
    };

    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/admin/database/overview") {
        return okJson(currentDatabaseOverview);
      }

      if (path === "/admin/backup/list") {
        return okJson({ backups: currentBackups });
      }

      if (path === "/admin/backup/trigger" && options?.method === "POST") {
        currentBackups = [
          {
            filename: "backup_20260416_103000_triggered.sqlite",
            size_bytes: 32768,
            created_at: 1713263400,
            verified: true,
            verification_method: "sqlite_integrity_check",
            last_restore_drill_status: null,
            last_restore_drill_at: null,
            cloud_synced: false,
          },
          ...currentBackups,
        ];
        return okJson({ detail: "Backup created", filename: "backup_20260416_103000_triggered.sqlite" });
      }

      if (path === "/admin/backup/restore-drill" && options?.method === "POST") {
        currentBackups = currentBackups.map((backup, index) => index === 0
          ? {
              ...backup,
              last_restore_drill_status: "passed",
              last_restore_drill_at: "2026-04-16T10:31:00Z",
            }
          : backup);
        return okJson({ filename: String(currentBackups[0].filename), verified: true, source: "local" });
      }

      if (path === "/admin/backup/restore-drill?filename=backup_20260415_090000_old.sqlite" && options?.method === "POST") {
        return okJson({ filename: "backup_20260415_090000_old.sqlite", verified: true, source: "local" });
      }

      if (path === "/admin/backup/download/backup_20260415_090000_old.sqlite") {
        return {
          ok: true,
          blob: async () => new Blob(["backup-bytes"], { type: "application/octet-stream" }),
        };
      }

      throw new Error(`Unhandled request ${path}`);
    });
  });

  it("renders the database inventory, health summary, and backup library", async () => {
    const { container } = render(<ExportsPanel />);

    await screen.findByText("Database Operations");
    await screen.findAllByText("backup_20260416_101500_new.sqlite");
    await waitFor(() => {
      expect(container.querySelector("[data-database-table='users']")).not.toBeNull();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/database/overview");
    expect(mockApiFetch).toHaveBeenCalledWith("/admin/backup/list");
    expect(screen.getByText("Database Tables")).toBeInTheDocument();
    expect(screen.getByText("Runtime Topology")).toBeInTheDocument();
    expect(screen.getByText(/Auto-sync every 20s/i)).toBeInTheDocument();
    expect(screen.getByText(/Redis is not connected/i)).toBeInTheDocument();
    expect(screen.getAllByText("backup_20260416_101500_new.sqlite").length).toBeGreaterThan(0);
    expect(screen.getAllByText("backup_20260415_090000_old.sqlite").length).toBeGreaterThan(0);
    expect(screen.getByText(/Newest files are listed first/i)).toBeInTheDocument();
    expect(screen.getByText(/Restore drill: passed/i)).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "Search database tables" }), {
      target: { value: "users" },
    });

    await waitFor(() => {
      expect(container.querySelector("[data-database-table='users']")).not.toBeNull();
      expect(container.querySelector("[data-database-table='orders']")).toBeNull();
    });
  });

  it("waits for auth hydration before loading admin database data", async () => {
    currentAuthState = { user: null, isLoading: true };
    const { rerender } = render(<ExportsPanel />);

    expect(mockApiFetch).not.toHaveBeenCalled();

    currentAuthState = { user: { id: 1, role: "admin", username: "admin" }, isLoading: false };
    rerender(<ExportsPanel />);

    await screen.findByText("Database Operations");
    expect(mockApiFetch).toHaveBeenCalledWith("/admin/database/overview");
    expect(mockApiFetch).toHaveBeenCalledWith("/admin/backup/list");
  });

  it("triggers a backup and refreshes the latest recovery point", async () => {
    render(<ExportsPanel />);

    await screen.findAllByText("backup_20260416_101500_new.sqlite");

    fireEvent.click(screen.getByRole("button", { name: "Trigger database backup" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/backup/trigger", { method: "POST" });
    });

    await waitFor(() => {
      expect(screen.getAllByText("backup_20260416_103000_triggered.sqlite").length).toBeGreaterThan(0);
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/database/overview");

    expect(mockAddToast).toHaveBeenCalledWith(
      "Backup created: backup_20260416_103000_triggered.sqlite",
      "success",
    );
  });

  it("runs restore drills and downloads a named backup artifact", async () => {
    render(<ExportsPanel />);

    await screen.findAllByText("backup_20260416_101500_new.sqlite");

    fireEvent.click(screen.getByRole("button", { name: "Download latest database backup" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/backup/download/backup_20260416_101500_new.sqlite");
    });

    fireEvent.click(screen.getByRole("button", { name: "Run restore drill for latest backup" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/backup/restore-drill", { method: "POST" });
    });

    fireEvent.click(screen.getByRole("button", { name: "Run restore drill for backup_20260415_090000_old.sqlite" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/backup/restore-drill?filename=backup_20260415_090000_old.sqlite",
        { method: "POST" },
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "Download backup backup_20260415_090000_old.sqlite" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/backup/download/backup_20260415_090000_old.sqlite");
    });

    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(mockAddToast).toHaveBeenCalledWith(
      "Backup downloaded: backup_20260415_090000_old.sqlite",
      "success",
    );
  });
});


