/**
 * Shared helpers for support tickets — used by both web_app and mobile_app.
 */

export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";

export interface SupportTicket {
  id: number;
  subject: string;
  message: string;
  status: TicketStatus;
  priority: TicketPriority;
  user_id?: number;
  created_at: string;
  updated_at?: string;
  replies?: TicketReply[];
}

export interface TicketReply {
  id: number;
  ticket_id: number;
  user_id: number;
  message: string;
  is_admin: boolean;
  created_at: string;
}

export const TICKET_STATUS_LABEL: Record<TicketStatus, string> = {
  open: "Open",
  in_progress: "In Progress",
  resolved: "Resolved",
  closed: "Closed",
};

export const TICKET_STATUS_COLOR: Record<TicketStatus, string> = {
  open: "#3b82f6",       // blue
  in_progress: "#f59e0b", // amber
  resolved: "#22c55e",   // green
  closed: "#6b7280",     // gray
};

export const TICKET_PRIORITY_LABEL: Record<TicketPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  urgent: "Urgent",
};

export const TICKET_PRIORITY_COLOR: Record<TicketPriority, string> = {
  low: "#6b7280",
  medium: "#3b82f6",
  high: "#f59e0b",
  urgent: "#ef4444",
};

export function normalizeTicketStatus(status?: string): TicketStatus {
  const valid: TicketStatus[] = ["open", "in_progress", "resolved", "closed"];
  const key = (status ?? "open").toLowerCase() as TicketStatus;
  return valid.includes(key) ? key : "open";
}

export function normalizeTicketPriority(priority?: string): TicketPriority {
  const valid: TicketPriority[] = ["low", "medium", "high", "urgent"];
  const key = (priority ?? "medium").toLowerCase() as TicketPriority;
  return valid.includes(key) ? key : "medium";
}

export function getTicketSummary(ticket: SupportTicket): string {
  return ticket.subject.length > 60
    ? ticket.subject.substring(0, 57) + "..."
    : ticket.subject;
}
