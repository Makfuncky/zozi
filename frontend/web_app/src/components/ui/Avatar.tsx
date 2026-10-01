"use client";
import { cn } from "@/lib/utils";

type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";

interface AvatarProps {
  src?: string; alt?: string; initials?: string; size?: AvatarSize;
  status?: "online" | "offline" | "away" | "busy"; className?: string;
}

const sizeClasses: Record<AvatarSize, string> = {
  xs: "h-6 w-6 text-xs", sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-12 w-12 text-base", xl: "h-16 w-16 text-lg",
};
const statusColors = { online: "bg-success", offline: "bg-text-faint", away: "bg-warning", busy: "bg-danger" };

export function Avatar({ src, alt, initials, size = "md", status, className }: AvatarProps) {
  return (
    <span className={cn("relative inline-flex", className)}>
      <span className={cn("inline-flex items-center justify-center rounded-full bg-glass-panel border border-glass-border-mid overflow-hidden", sizeClasses[size])}>
        {src ? <img src={src} alt={alt || "Avatar"} className="h-full w-full object-cover" /> : <span className="font-medium text-text-muted">{initials || "?"}</span>}
      </span>
      {status && <span className={cn("absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 ring-2 ring-surface-0", statusColors[status])} />}
    </span>
  );
}

interface AvatarGroupProps {
  children: React.ReactNode; max?: number; size?: AvatarSize; className?: string;
}

export function AvatarGroup({ children, max = 4, size = "md", className }: AvatarGroupProps) {
  const childArray = Array.isArray(children) ? children : [children];
  const visible = childArray.slice(0, max);
  const remaining = childArray.length - max;
  return (
    <div className={cn("flex -space-x-2", className)}>
      {visible.map((child, i) => <div key={i} className="ring-2 ring-surface-0 rounded-full">{child}</div>)}
      {remaining > 0 && <span className={cn("inline-flex items-center justify-center rounded-full bg-glass-panel border border-glass-border-mid font-medium text-text-muted", sizeClasses[size])}>+{remaining}</span>}
    </div>
  );
}
