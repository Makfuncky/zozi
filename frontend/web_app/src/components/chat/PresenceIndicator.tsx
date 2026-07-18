"use client";

import type { WsRoomUser } from "@/hooks/useChatWebSocket";

interface PresenceIndicatorProps {
  users: WsRoomUser[];
  currentUserId?: number | null;
  showList?: boolean;
}

export function PresenceIndicator({ users, currentUserId, showList = false }: PresenceIndicatorProps) {
  const onlineUsers = users.filter((u) => u.status === "online");
  const awayUsers = users.filter((u) => u.status === "away");
  const busyUsers = users.filter((u) => u.status === "busy");

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1">
        <div className="flex -space-x-1">
          {onlineUsers.slice(0, 3).map((u) => (
            <div
              key={u.user_id}
              className="relative h-5 w-5 rounded-full border border-surface-1"
              title={`${u.name} (online)`}
            >
              <div className="h-full w-full rounded-full bg-primary/20 flex items-center justify-center text-[8px] font-bold text-primary">
                {u.name?.charAt(0)?.toUpperCase() ?? "?"}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full bg-success border border-surface-1" />
            </div>
          ))}
          {onlineUsers.length > 3 && (
            <div className="h-5 w-5 rounded-full bg-surface-3 flex items-center justify-center text-[8px] font-bold text-text-muted border border-surface-1">
              +{onlineUsers.length - 3}
            </div>
          )}
        </div>
      </div>

      {showList && users.length > 0 && (
        <div className="group relative">
          <span className="text-[10px] text-text-muted cursor-help">
            {onlineUsers.length} online
            {awayUsers.length > 0 ? `, ${awayUsers.length} away` : ""}
          </span>
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
            <div className="bg-surface-2 border border-border rounded-lg p-2 shadow-xl min-w-[160px]">
              <p className="text-[9px] font-semibold text-text-muted uppercase tracking-wider mb-1.5">Room Members</p>
              {users.map((u) => (
                <div key={u.user_id} className="flex items-center gap-2 py-1">
                  <div className="relative">
                    <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center text-[8px] font-bold text-primary">
                      {u.name?.charAt(0)?.toUpperCase() ?? "?"}
                    </div>
                    <span
                      className={`absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full border border-surface-1 ${
                        u.status === "online"
                          ? "bg-success"
                          : u.status === "away"
                            ? "bg-amber-500"
                            : u.status === "busy"
                              ? "bg-danger"
                              : "bg-gray-400"
                      }`}
                    />
                  </div>
                  <span className="text-xs text-text flex-1 truncate">
                    {u.name}
                    {u.user_id === currentUserId ? " (you)" : ""}
                  </span>
                  <span className={`text-[9px] ${u.status === "online" ? "text-success" : u.status === "away" ? "text-amber-500" : u.status === "busy" ? "text-danger" : "text-gray-400"}`}>
                    {u.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function PresenceDot({ status }: { status: WsRoomUser["status"] }) {
  const colorMap = {
    online: "bg-success",
    away: "bg-amber-500",
    busy: "bg-danger",
    offline: "bg-gray-400",
  };

  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${colorMap[status] ?? "bg-gray-400"}`}
      title={status}
    />
  );
}
