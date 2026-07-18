import { normalizePaginatedList, type PaginatedListEnvelope } from "@shared/adminListUtils";

export interface AdminUserRecord {
  id: number;
  username: string;
  display_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  total_orders?: number;
}

export interface AdminAuditLogRecord {
  id: number;
  user_id: number | null;
  username?: string;
  user_role?: string;
  action: string;
  resource_type?: string;
  resource_id?: number | string;
  details?: Record<string, unknown> | string | null;
  ip_address?: string;
  status: string;
  created_at: string;
}

export type AdminEmailRecipientType = "all" | "newsletter" | "customers";

export function normalizeAdminUsers(payload: unknown): AdminUserRecord[] {
  if (!Array.isArray(payload)) {
    return [];
  }

  return payload.map((entry) => {
    const record = entry as Record<string, unknown>;
    const id = typeof record.id === "number" ? record.id : Number(record.id ?? 0);
    const username = typeof record.username === "string" && record.username.trim()
      ? record.username.trim()
      : typeof record.email === "string" && record.email.trim()
        ? record.email.trim()
        : `User #${id}`;
    const displayName = typeof record.full_name === "string" && record.full_name.trim()
      ? record.full_name.trim()
      : username;

    return {
      id,
      username,
      display_name: displayName,
      email: typeof record.email === "string" ? record.email : "",
      role: typeof record.role === "string" ? record.role : "customer",
      is_active: Boolean(record.is_active),
      created_at: typeof record.created_at === "string" ? record.created_at : "",
      total_orders: typeof record.total_orders === "number" ? record.total_orders : undefined,
    };
  });
}

export function buildAdminAuditLogsQuery(page: number, pageSize: number): string {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return `/admin/audit-logs?${params.toString()}`;
}

export function normalizeAdminAuditLogPage(payload: unknown): PaginatedListEnvelope<AdminAuditLogRecord> {
  return normalizePaginatedList<AdminAuditLogRecord>(payload, ["items", "logs", "results", "data"]);
}

export function buildAdminEmailCampaignPayload(
  subject: string,
  htmlContent: string,
  recipients: AdminEmailRecipientType,
) {
  const trimmedSubject = subject.trim();
  const trimmedHtml = htmlContent.trim();

  return {
    name: trimmedSubject.slice(0, 80) || "Admin Campaign",
    subject: trimmedSubject,
    html_content: trimmedHtml,
    recipients,
    status: "draft" as const,
  };
}