"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  useEffect,
  type ReactNode,
  type DragEvent,
} from "react";
import { type ThreadSummary } from "./CommShell";

// ── Drag payload types ────────────────────────────────────────────────────

export type DragPayload =
  | { type: "thread"; thread: ThreadSummary }
  | { type: "contact"; contactId: string; contactName: string }
  | { type: "task"; taskId: string; text: string };

export type DropZoneId = "context-panel" | "stage" | "rail";

// ── Context value ─────────────────────────────────────────────────────────

interface DragContextValue {
  /** Currently dragged item, or null */
  dragPayload: DragPayload | null;
  /** Set the dragged item (call from draggable onDragStart) */
  startDrag: (payload: DragPayload, e: DragEvent) => void;
  /** Clear the dragged item (call from draggable onDragEnd) */
  endDrag: () => void;
  /** Check if a drop target accepts the current drag payload */
  acceptsDrop: (zone: DropZoneId) => boolean;
  /** Register a drop handler for a zone. Returns an unsubscribe fn. */
  onDrop: (zone: DropZoneId, handler: (payload: DragPayload) => void) => () => void;
  /** Call from drop zone onDragOver to signal acceptance */
  isOver: string | null;
  setIsOver: (zone: string | null) => void;
}

const DragCtx = createContext<DragContextValue>(null!);

export function useDrag() {
  return useContext(DragCtx);
}

// ── Provider ──────────────────────────────────────────────────────────────

export function DragProvider({ children }: { children: ReactNode }) {
  const [dragPayload, setDragPayload] = useState<DragPayload | null>(null);
  const [isOver, setIsOver] = useState<string | null>(null);

  // Drop handler registry — zones can register handlers
  const dropHandlers = useRef<Map<DropZoneId, Array<(p: DragPayload) => void>>>(new Map());

  const startDrag = useCallback((payload: DragPayload, e: DragEvent) => {
    setDragPayload(payload);
    e.dataTransfer.effectAllowed = "move";
    // Set a custom drag image data type
    e.dataTransfer.setData("text/plain", payload.type);
  }, []);

  const endDrag = useCallback(() => {
    setDragPayload(null);
    setIsOver(null);
  }, []);

  const acceptsDrop = useCallback(
    (zone: DropZoneId): boolean => {
      if (!dragPayload) return false;
      // Threads can be dropped on the context panel → becomes a task
      if (zone === "context-panel" && dragPayload.type === "thread") return true;
      // Contacts can be dropped on the stage → starts a thread
      if (zone === "stage" && dragPayload.type === "contact") return true;
      return false;
    },
    [dragPayload]
  );

  const onDrop = useCallback(
    (zone: DropZoneId, handler: (payload: DragPayload) => void): (() => void) => {
      const existing = dropHandlers.current.get(zone) || [];
      existing.push(handler);
      dropHandlers.current.set(zone, existing);
      return () => {
        const handlers = dropHandlers.current.get(zone);
        if (handlers) {
          const filtered = handlers.filter((h) => h !== handler);
          if (filtered.length === 0) dropHandlers.current.delete(zone);
          else dropHandlers.current.set(zone, filtered);
        }
      };
    },
    []
  );

  return (
    <DragCtx.Provider
      value={{ dragPayload, startDrag, endDrag, acceptsDrop, onDrop, isOver, setIsOver }}
    >
      {children}
    </DragCtx.Provider>
  );
}

// ── Drop zone wrapper component ───────────────────────────────────────────

export function DropZone({
  zone,
  className = "",
  children,
  onDrop: onDropHandler,
}: {
  zone: DropZoneId;
  className?: string;
  children: ReactNode;
  onDrop: (payload: DragPayload) => void;
}) {
  const { dragPayload, acceptsDrop, endDrag, isOver, setIsOver, onDrop: registerDrop } = useDrag();

  const handlerRef = useRef(onDropHandler);
  handlerRef.current = onDropHandler;

  // Register handler with DragProvider on mount, unregister on unmount
  useEffect(() => {
    const handler = (p: DragPayload) => handlerRef.current(p);
    const unsub = registerDrop(zone, handler);
    return unsub;
  }, [zone, registerDrop]);

  const canDrop = acceptsDrop(zone);

  const handleDragOver = (e: React.DragEvent) => {
    if (!canDrop) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setIsOver(zone);
  };

  const handleDragLeave = () => {
    setIsOver(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsOver(null);
    // Capture payload before endDrag clears it
    const payload = dragPayload;
    endDrag();
    if (payload) handlerRef.current(payload);
  };

  const active = isOver === zone && canDrop;

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={className}
      data-drop-zone={zone}
      data-drop-active={active ? "true" : undefined}
    >
      {children}
    </div>
  );
}
