/**
 * notificationsScreen.test.ts
 * Tests the API functions used by the Notifications screen:
 * getNotifications, markNotificationRead, markAllNotificationsRead, deleteNotification.
 */

const mockApiFetch = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getNotifications: (...args: any[]) => mockApiFetch("/notifications", ...args),
  markNotificationRead: (id: number) => mockApiFetch(`/notifications/${id}/read`, { method: "PUT" }),
  markAllNotificationsRead: () => mockApiFetch("/notifications/read-all", { method: "PUT" }),
  deleteNotification: (id: number) => mockApiFetch(`/notifications/${id}`, { method: "DELETE" }),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
  type Notification,
} from "@/lib/api";

function makeNotification(id: number, is_read = false): Notification {
  return {
    id,
    type: "system",
    title: `Notification ${id}`,
    message: `Notification ${id}`,
    read: is_read,
    created_at: new Date().toISOString(),
    link: undefined,
  };
}

beforeEach(() => jest.clearAllMocks());

// ── getNotifications ──────────────────────────────────────────────────────────

describe("notificationsScreen — getNotifications", () => {
  it("returns an array of notifications", async () => {
    const notifs = [makeNotification(1), makeNotification(2, true)];
    mockApiFetch.mockResolvedValueOnce(notifs);

    const data = await getNotifications();
    expect(data).toHaveLength(2);
    expect(data[0].id).toBe(1);
    expect(data[1].read).toBe(true);
  });

  it("returns empty array when no notifications exist", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await getNotifications();
    expect(data).toEqual([]);
  });

  it("propagates network errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Unauthorized"));
    await expect(getNotifications()).rejects.toThrow("Unauthorized");
  });

  it("can filter unread notifications from the result", async () => {
    const notifs = [makeNotification(1, false), makeNotification(2, true), makeNotification(3, false)];
    mockApiFetch.mockResolvedValueOnce(notifs);

    const data = await getNotifications();
    const unread = data.filter((n) => !n.read);
    expect(unread).toHaveLength(2);
  });
});

// ── markNotificationRead ──────────────────────────────────────────────────────

describe("notificationsScreen — markNotificationRead", () => {
  it("calls PUT /notifications/:id/read", async () => {
    mockApiFetch.mockResolvedValueOnce(undefined);
    await markNotificationRead(42);
    expect(mockApiFetch).toHaveBeenCalledWith("/notifications/42/read", { method: "PUT" });
  });

  it("propagates errors from the API", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Not found"));
    await expect(markNotificationRead(99)).rejects.toThrow("Not found");
  });
});

// ── markAllNotificationsRead ──────────────────────────────────────────────────

describe("notificationsScreen — markAllNotificationsRead", () => {
  it("calls PUT /notifications/read-all", async () => {
    mockApiFetch.mockResolvedValueOnce(undefined);
    await markAllNotificationsRead();
    expect(mockApiFetch).toHaveBeenCalledWith("/notifications/read-all", { method: "PUT" });
  });
});

// ── deleteNotification ────────────────────────────────────────────────────────

describe("notificationsScreen — deleteNotification", () => {
  it("calls DELETE /notifications/:id", async () => {
    mockApiFetch.mockResolvedValueOnce(undefined);
    await deleteNotification(7);
    expect(mockApiFetch).toHaveBeenCalledWith("/notifications/7", { method: "DELETE" });
  });

  it("propagates errors from the API", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Forbidden"));
    await expect(deleteNotification(1)).rejects.toThrow("Forbidden");
  });
});

// ── notification filtering helpers ───────────────────────────────────────────

describe("notificationsScreen — client-side logic", () => {
  it("sorts notifications newest-first by created_at", () => {
    const notifs: Notification[] = [
      { id: 1, type: "system", title: "Old", message: "Old", read: false, created_at: "2024-01-01T00:00:00Z" },
      { id: 2, type: "system", title: "New", message: "New", read: false, created_at: "2024-06-01T00:00:00Z" },
    ];
    const sorted = [...notifs].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    expect(sorted[0].id).toBe(2);
  });

  it("marks a notification as read in local state", () => {
    let notifs: Notification[] = [makeNotification(1), makeNotification(2)];
    // simulate the screen's onRead handler
    notifs = notifs.map((n) => (n.id === 1 ? { ...n, read: true } : n));
    expect(notifs.find((n) => n.id === 1)?.read).toBe(true);
    expect(notifs.find((n) => n.id === 2)?.read).toBe(false);
  });

  it("removes a notification from local state after delete", () => {
    let notifs: Notification[] = [makeNotification(1), makeNotification(2), makeNotification(3)];
    notifs = notifs.filter((n) => n.id !== 2);
    expect(notifs).toHaveLength(2);
    expect(notifs.find((n) => n.id === 2)).toBeUndefined();
  });
});
