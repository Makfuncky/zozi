import React from "react";

const mockGetAccessToken = jest.fn(() => "user-live-token");

jest.mock("@/lib/api", () => ({
  API_URL: "http://localhost:8000",
  getAccessToken: () => mockGetAccessToken(),
}));

import {
  buildUserRealtimeSocketUrl,
  connectUserRealtimeSocket,
  isNotificationRealtimeMessage,
  isTicketRealtimeMessage,
} from "@/lib/userRealtime";

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  onopen: null | (() => void) = null;
  onmessage: null | ((event?: { data?: string }) => void) = null;
  onerror: null | (() => void) = null;
  onclose: null | (() => void) = null;
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
}

describe("userRealtime helpers", () => {
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterAll(() => {
    global.WebSocket = originalWebSocket;
  });

  it("builds an authenticated user websocket URL", () => {
    expect(buildUserRealtimeSocketUrl()).toBe("ws://localhost:8000/ws/user?token=user-live-token");
  });

  it("routes socket lifecycle and payload parsing through the shared helper", () => {
    const statusUpdates: string[] = [];
    const onMessage = jest.fn();

    const socket = connectUserRealtimeSocket(
      (status) => statusUpdates.push(status),
      onMessage,
    );

    expect(socket).not.toBeNull();
    expect(MockWebSocket.instances[0]?.url).toContain("/ws/user");
    expect(statusUpdates).toEqual(["connecting"]);

    MockWebSocket.instances[0]?.onopen?.();
    MockWebSocket.instances[0]?.onmessage?.({ data: JSON.stringify({ type: "notification.created", notification_id: 7 }) });
    MockWebSocket.instances[0]?.onclose?.();

    expect(onMessage).toHaveBeenCalledWith({ type: "notification.created", notification_id: 7 });
    expect(statusUpdates).toEqual(["connecting", "live", "offline"]);
  });

  it("classifies notification and ticket realtime payloads", () => {
    expect(isNotificationRealtimeMessage({ type: "notification.updated" })).toBe(true);
    expect(isNotificationRealtimeMessage({ type: "ticket.reply_created" })).toBe(false);
    expect(isTicketRealtimeMessage({ type: "ticket.reply_created" })).toBe(true);
    expect(isTicketRealtimeMessage({ type: "notification.created" })).toBe(false);
  });
});
