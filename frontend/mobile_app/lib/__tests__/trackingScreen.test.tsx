import React from "react";

const mockGetCurrentAccessToken = jest.fn(() => "mobile-live-token");

jest.mock("react-native", () => ({
  ActivityIndicator: () => null,
  Linking: { openURL: jest.fn() },
  ScrollView: () => null,
  StyleSheet: { create: (styles: unknown) => styles },
  Text: () => null,
  TextInput: () => null,
  TouchableOpacity: () => null,
  View: () => null,
}));

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useLocalSearchParams: () => ({ id: "42" }),
  useRouter: () => ({ back: jest.fn(), replace: jest.fn() }),
}));

jest.mock("@/lib/api", () => ({
  API_BASE: "http://localhost:8000",
  getCurrentAccessToken: () => mockGetCurrentAccessToken(),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({
    user: { id: 9, role: "customer" },
    isLoggedIn: true,
    isLoading: false,
  }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        surface1: "#ffffff",
        surface2: "#f7f7f7",
        border: "#dddddd",
        text: "#111111",
        textMuted: "#666666",
        success: "#009944",
        danger: "#cc0000",
      },
      fontSize: { xs: 12, sm: 14, md: 16 },
      spacing: { sm: 8, md: 12 },
      radius: { xl: 16 },
    },
  }),
}));

jest.mock("@/components/ui/Badge", () => ({
  Badge: () => null,
}));

jest.mock("@/components/ui/LoadingSpinner", () => ({
  LoadingSpinner: () => null,
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    textBrand: { color: "#123456" },
    input: { borderWidth: 1 },
  }),
}));

import { buildTrackingSocketUrl, connectTrackingSocket } from "@/app/tracking/[id]";

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

describe("SharedTrackingScreen", () => {
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterAll(() => {
    global.WebSocket = originalWebSocket;
  });

  it("builds an authenticated order-scoped websocket URL for mobile tracking", () => {
    expect(buildTrackingSocketUrl(42)).toBe(
      "ws://localhost:8000/ws/logistics?scope=order&order_id=42&token=mobile-live-token"
    );
  });

  it("does not build a tracking websocket URL when the session token is missing", () => {
    mockGetCurrentAccessToken.mockReturnValueOnce(null as any);

    expect(buildTrackingSocketUrl(42)).toBeNull();
  });

  it("routes socket lifecycle events into mobile tracking refresh callbacks", () => {
    const statusUpdates: string[] = [];
    const onMessage = jest.fn();

    const socket = connectTrackingSocket(
      42,
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