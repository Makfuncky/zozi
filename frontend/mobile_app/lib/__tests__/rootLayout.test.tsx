import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
(globalThis as any).__DEV__ = true;

const mockInitialize = jest.fn().mockResolvedValue(undefined);
const mockLogout = jest.fn().mockResolvedValue(undefined);
const mockInitTheme = jest.fn();
const mockRouterReplace = jest.fn();
const mockHideSplash = jest.fn().mockResolvedValue(undefined);
const mockPreventAutoHide = jest.fn().mockResolvedValue(undefined);
const mockSetAuthExpiredCallback = jest.fn();

let capturedAuthExpiredCallback: (() => void) | null = null;

const useAuthStoreMock = Object.assign(
  jest.fn(() => ({
    initialize: mockInitialize,
    isLoading: false,
    isLoggedIn: false,
  })),
  {
    getState: () => ({ logout: mockLogout }),
  },
);

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: { OS: "web" },
    LogBox: {
      ignoreLogs: jest.fn(),
      ignoreAllLogs: jest.fn(),
    },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
  };
});

jest.mock("expo-router", () => ({
  Stack: Object.assign(
    ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Stack", props, children),
    { Screen: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("StackScreen", props, children) },
  ),
  useRouter: () => ({ replace: mockRouterReplace, push: jest.fn(), back: jest.fn() }),
}));

jest.mock("expo-status-bar", () => ({
  StatusBar: (props: Record<string, unknown>) => React.createElement("StatusBar", props),
}));

jest.mock("react-native-gesture-handler", () => ({
  GestureHandlerRootView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("GestureHandlerRootView", props, children),
}));

jest.mock("react-native-safe-area-context", () => ({
  SafeAreaProvider: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("SafeAreaProvider", props, children),
}));

jest.mock("expo-splash-screen", () => ({
  preventAutoHideAsync: (...args: unknown[]) => mockPreventAutoHide(...args),
  hideAsync: (...args: unknown[]) => mockHideSplash(...args),
}));

jest.mock("expo-constants", () => ({
  __esModule: true,
  default: {
    expoConfig: { extra: { eas: { projectId: "test-project" } } },
    easConfig: { projectId: "test-project" },
    deviceName: "Jest Device",
  },
}));

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: useAuthStoreMock,
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        surface0: "#f8fafc",
        surface1: "#ffffff",
        text: "#111111",
      },
    },
    mode: "light",
    initTheme: mockInitTheme,
    initialized: true,
  }),
}));

jest.mock("@/lib/api", () => ({
  setAuthExpiredCallback: (cb: () => void) => {
    capturedAuthExpiredCallback = cb;
    mockSetAuthExpiredCallback(cb);
  },
  apiFetch: jest.fn(),
  registerPushToken: jest.fn(),
  unregisterPushToken: jest.fn(),
}));

jest.mock("@/lib/logger", () => ({
  setLogLevel: jest.fn(),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: () => ({ setLocale: jest.fn() }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: () => ({ setCurrency: jest.fn() }),
}));

jest.mock("@/lib/countryContext", () => {
  const React = require("react");
  return {
    CountryProvider: ({ children }: { children?: React.ReactNode }) => React.createElement(React.Fragment, null, children),
    useCountry: () => ({ setCountryCode: jest.fn().mockResolvedValue(undefined) }),
  };
});

jest.mock("@/components/ToastContainer", () => ({
  ToastContainer: () => null,
}));

jest.mock("@/components/ui", () => ({
  ErrorHandlerInit: () => null,
}));

jest.mock("@/components/ui/ErrorBoundary", () => {
  const React = require("react");
  return ({ children }: { children?: React.ReactNode }) => React.createElement(React.Fragment, null, children);
});

jest.mock("@/components/MobileBackgroundEffect", () => () => null);
jest.mock("@/components/BackgroundJobCenter", () => () => null);
jest.mock("@/components/UserRealtimeBridge", () => ({ UserRealtimeBridge: () => null }));

jest.mock("@shared/localization", () => ({
  isLocale: jest.fn(() => false),
  normalizeLocale: jest.fn((value: string) => value),
}));

const RootLayout = require("../../app/_layout").default;

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("root layout auth wiring", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    capturedAuthExpiredCallback = null;
  });

  it("registers the auth-expired callback and initializes the app shell", async () => {
    await act(async () => {
      TestRenderer.create(<RootLayout />);
    });
    await flush();

    expect(mockInitTheme).toHaveBeenCalledTimes(1);
    expect(mockSetAuthExpiredCallback).toHaveBeenCalledTimes(1);
    expect(mockInitialize).toHaveBeenCalledTimes(1);
    expect(mockHideSplash).toHaveBeenCalledTimes(1);
  });

  it("logs out and redirects to login when the auth-expired callback fires", async () => {
    await act(async () => {
      TestRenderer.create(<RootLayout />);
    });
    await flush();

    expect(capturedAuthExpiredCallback).toBeTruthy();

    await act(async () => {
      capturedAuthExpiredCallback?.();
    });

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockRouterReplace).toHaveBeenCalledWith("/(auth)/login");
  });
});