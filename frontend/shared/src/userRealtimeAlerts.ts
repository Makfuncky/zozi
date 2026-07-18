import type { RealtimeUserMessage } from "./notificationStore";

export type RealtimeAlertTone = "success" | "error" | "info" | "warning";

export interface RealtimeAlert {
  id: string;
  link?: string | null;
  message: string;
  tone: RealtimeAlertTone;
}

function compactText(value?: string | null): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function alertTone(payload: RealtimeUserMessage): RealtimeAlertTone {
  if (payload.level) {
    return payload.level;
  }
  if (payload.type.startsWith("admin.alert.")) {
    return "warning";
  }
  return "info";
}

function defaultAlertMessage(payload: RealtimeUserMessage): string | null {
  switch (payload.type) {
    case "notification.created":
      return "You have a new notification.";
    case "ticket.reply_created":
      return payload.is_admin ? "Support replied to your ticket." : "There is a new reply on your ticket.";
    case "admin.alert.ticket":
      return "A support ticket needs staff attention.";
    case "admin.alert.product":
      return "A product is waiting for moderation.";
    case "admin.alert.supplier":
      return "A supplier verification request needs review.";
    case "admin.alert.payout":
      return "A payout request needs review.";
    case "admin.alert.audit":
      return "A new audit event was recorded.";
    default:
      return null;
  }
}

export function buildRealtimeAlert(payload: RealtimeUserMessage | null): RealtimeAlert | null {
  if (!payload) {
    return null;
  }

  if (!["notification.created", "ticket.reply_created"].includes(payload.type) && !payload.type.startsWith("admin.alert.")) {
    return null;
  }

  const title = compactText(payload.title);
  const body = compactText(payload.message) ?? defaultAlertMessage(payload);

  if (!title && !body) {
    return null;
  }

  return {
    id: [payload.type, payload.notification_id, payload.ticket_id, payload.reply_id, payload.product_id, payload.payout_id, payload.supplier_id, payload.audit_id]
      .filter((part) => part !== undefined && part !== null)
      .join(":"),
    link: payload.link ?? null,
    message: title && body && title !== body ? `${title}: ${body}` : title ?? body ?? "",
    tone: alertTone(payload),
  };
}