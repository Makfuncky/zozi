export type RealtimeStatus = "idle" | "connecting" | "live" | "offline";

export interface RealtimeRefreshScheduler {
  cancel: () => void;
  trigger: () => void;
}

interface RealtimeSocketOptions<TPayload> {
  onStatusChange?: (status: RealtimeStatus) => void;
  onMessage?: (payload: TPayload | null) => void;
  /** Enable auto-reconnect with exponential backoff (default: true) */
  autoReconnect?: boolean;
  /** Max reconnect attempts before giving up (default: 10) */
  maxReconnectAttempts?: number;
}

export interface RealtimeSocketHandle {
  socket: WebSocket | null;
  close: () => void;
}

const RECONNECT_BASE_DELAY = 1000;
const RECONNECT_MAX_DELAY = 30000;

export function openRealtimeSocket<TPayload = unknown>(
  socketUrl: string | null,
  options: RealtimeSocketOptions<TPayload>,
): RealtimeSocketHandle {
  const {
    onStatusChange,
    onMessage,
    autoReconnect = true,
    maxReconnectAttempts = 10,
  } = options;

  let attempt = 0;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let disposed = false;
  let currentSocket: WebSocket | null = null;

  function connect(): WebSocket | null {
    if (disposed) return null;
    if (!socketUrl) {
      onStatusChange?.("offline");
      return null;
    }

    onStatusChange?.("connecting");
    const socket = new WebSocket(socketUrl);
    currentSocket = socket;

    socket.onopen = () => {
      attempt = 0;
      onStatusChange?.("live");
    };

    socket.onmessage = (event?: MessageEvent) => {
      const raw = typeof event?.data === "string" ? event.data : null;
      if (!raw) {
        onMessage?.(null);
        return;
      }

      try {
        onMessage?.(JSON.parse(raw) as TPayload);
      } catch {
        onMessage?.(null);
      }
    };

    socket.onerror = () => {
      onStatusChange?.("offline");
    };

    socket.onclose = () => {
      onStatusChange?.("offline");
      if (!disposed && autoReconnect && attempt < maxReconnectAttempts) {
        const delay = Math.min(
          RECONNECT_BASE_DELAY * Math.pow(2, attempt) + Math.random() * 500,
          RECONNECT_MAX_DELAY,
        );
        attempt++;
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          connect();
        }, delay);
      }
    };

    return socket;
  }

  const socket = connect();

  return {
    socket,
    close() {
      disposed = true;
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (currentSocket && currentSocket.readyState <= WebSocket.OPEN) {
        currentSocket.close();
      }
    },
  };
}

export function createRealtimeRefreshScheduler(
  refresh: () => void | Promise<void>,
  delayMs = 200,
): RealtimeRefreshScheduler {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let inFlight = false;
  let pendingTrigger = false;

  const runRefresh = () => {
    if (typeof document !== "undefined" && document.visibilityState === "hidden") {
      pendingTrigger = true;
      return;
    }

    if (inFlight) {
      pendingTrigger = true;
      return;
    }

    inFlight = true;
    void Promise.resolve(refresh())
      .catch(() => undefined)
      .finally(() => {
        inFlight = false;
        if (pendingTrigger) {
          pendingTrigger = false;
          timeoutId = setTimeout(() => {
            timeoutId = null;
            runRefresh();
          }, delayMs);
        }
      });
  };

  return {
    cancel() {
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      pendingTrigger = false;
    },
    trigger() {
      if (timeoutId !== null) {
        pendingTrigger = true;
        return;
      }

      timeoutId = setTimeout(() => {
        timeoutId = null;
        runRefresh();
      }, delayMs);
    },
  };
}