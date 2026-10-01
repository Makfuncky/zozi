/**
 * Lightweight cross-component UI bus.
 * Lets screens (e.g. a custom HeaderBar) trigger the tab-layout drawers
 * without prop-drilling. The (tabs)/_layout subscribes and opens/closes
 * its AppDrawer instances.
 *
 * Uses a tiny hand-rolled emitter instead of Node's `events` so it works
 * identically on native and in the Expo web bundle (Node's `events` module
 * is not reliably polyfilled for web and throws "EventEmitter is not a
 * constructor" at runtime).
 */

export type UiBusEvent = "open-left-drawer" | "open-right-drawer" | "close-drawers";

type Handler = () => void;

const listeners: Record<string, Set<Handler>> = {};

function on(event: UiBusEvent, handler: Handler) {
  if (!listeners[event]) listeners[event] = new Set();
  listeners[event].add(handler);
  return () => off(event, handler);
}

function off(event: UiBusEvent, handler: Handler) {
  listeners[event]?.delete(handler);
}

function emit(event: UiBusEvent) {
  listeners[event]?.forEach((handler) => {
    try {
      handler();
    } catch {
      /* swallow listener errors so one bad subscriber can't break the bus */
    }
  });
}

export const uiBus = { on, off, emit };

export function openLeftDrawer() {
  emit("open-left-drawer");
}

export function openRightDrawer() {
  emit("open-right-drawer");
}

export function closeDrawers() {
  emit("close-drawers");
}
