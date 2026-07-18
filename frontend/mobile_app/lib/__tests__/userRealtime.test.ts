import React from "react";

const mockGetCurrentAccessToken = jest.fn(() => "mobile-user-live-token");

jest.mock("@/lib/api", () => ({
  API_BASE: "http://localhost:8000",
  getCurrentAccessToken: () => mockGetCurrentAccessToken(),
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

describe("mobile userRealtime helpers", () => {
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterAll(() => {
    global.WebSocket = originalWebSocket;
  });

  it("builds an authenticated mobile user websocket URL", () => {
    expect(buildUserRealtimeSocketUrl()).toBe("ws://localhost:8000/ws/user?token=mobile-user-live-token");
  });

  it("routes websocket lifecycle events into the shared helper", () => {
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
    MockWebSocket.instances[0]?.onmessage?.({ data: JSON.stringify({ type: "ticket.reply_created", ticket_id: 11 }) });
    MockWebSocket.instances[0]?.onclose?.();

    expect(onMessage).toHaveBeenCalledWith({ type: "ticket.reply_created", ticket_id: 11 });
    expect(statusUpdates).toEqual(["connecting", "live", "offline"]);
  });

  it("classifies notification and ticket realtime payloads", () => {
    expect(isNotificationRealtimeMessage({ type: "notification.created" })).toBe(true);
    expect(isNotificationRealtimeMessage({ type: "ticket.updated" })).toBe(false);
    expect(isTicketRealtimeMessage({ type: "ticket.updated" })).toBe(true);
    expect(isTicketRealtimeMessage({ type: "notification.updated" })).toBe(false);
  });
});