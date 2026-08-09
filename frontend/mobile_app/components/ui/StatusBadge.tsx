import { useThemeStore } from "@/lib/themeStore";
import { Badge, type BadgeVariant } from "./Badge";

/**
 * Centralized status → semantic variant mapping.
 * Replaces the dozens of duplicated hardcoded hex status pills
 * found across admin/supplier/logistics screens.
 */
const STATUS_VARIANT_MAP: Record<string, BadgeVariant> = {
	// Orders
	pending: "warning",
	processing: "info",
	shipped: "info",
	delivered: "success",
	completed: "success",
	cancelled: "danger",
	canceled: "danger",
	returned: "default",
	replacement: "default",
	refunded: "default",
	paid: "success",
	unpaid: "warning",
	failed: "danger",
	// Generic
	active: "success",
	inactive: "default",
	suspended: "danger",
	approved: "success",
	rejected: "danger",
	rejected_reason: "danger",
	verified: "success",
	unverified: "warning",
	open: "info",
	closed: "default",
	resolved: "success",
	escalated: "danger",
	// Shipments
	picked_up: "info",
	in_transit: "info",
	out_for_delivery: "warning",
	delivered_to_customer: "success",
	attempted: "warning",
	exception: "danger",
	// Verification
	approved_status: "success",
	rejected_status: "danger",
	pending_review: "warning",
};

export function statusVariant(status: string | null | undefined): BadgeVariant {
	if (!status) return "default";
	const key = String(status).toLowerCase().replace(/\s+/g, "_");
	return STATUS_VARIANT_MAP[key] ?? "default";
}

/** Human-friendly label (Title Case). */
export function statusLabel(status: string | null | undefined): string {
	if (!status) return "—";
	return String(status)
		.replace(/_/g, " ")
		.replace(/\b\w/g, (c) => c.toUpperCase());
}

export function StatusBadge({ status, label }: { status: string | null | undefined; label?: string }) {
	return <Badge label={label ?? statusLabel(status)} variant={statusVariant(status)} />;
}

export default StatusBadge;
