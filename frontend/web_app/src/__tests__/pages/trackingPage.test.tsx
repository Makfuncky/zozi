import React from "react";

const mockGetAccessToken = jest.fn(() => "customer-live-token");

jest.mock("@/lib/api", () => ({
  API_URL: "http://localhost:8000",
  getAccessToken: () => mockGetAccessToken(),
}));

import { buildTrackingSocketUrl, connectTrackingSocket } from "@/lib/trackingRealtime";

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  onopen: null | (() => void) = null;
  onmessage: null | (() => void) = null;
  onerror: null | (() => void) = null;
  onclose: null | (() => void) = null;
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
}

describe("SharedTrackingPage", () => {
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterAll(() => {
    global.WebSocket = originalWebSocket;
  });

  it("builds an authenticated order-scoped websocket URL", () => {
    expect(buildTrackingSocketUrl("42")).toBe(
      "ws://localhost:8000/ws/logistics?scope=order&order_id=42&token=customer-live-token"
    );
  });

  it("routes socket lifecycle events into tracking refresh callbacks", () => {
    const statusUpdates: string[] = [];
    const onMessage = jest.fn();

    const socket = connectTrackingSocket(
      "42",
      (status) => statusUpdates.push(status),
      onMessage,
    );

    expect(socket).not.toBeNull();
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0]?.url).toContain("scope=order");
    expect(statusUpdates).toEqual(["connecting"]);

    MockWebSocket.instances[0]?.onopen?.();
    MockWebSocket.instances[0]?.onmessage?.();
    MockWebSocket.instances[0]?.onclose?.();

    expect(onMessage).toHaveBeenCalledTimes(1);
    expect(statusUpdates).toEqual(["connecting", "live", "offline"]);
  });
});


