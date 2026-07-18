import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockGetAuthCapabilities = jest.fn();
const mockStoreLogin = jest.fn();
const mockRouterReplace = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: {
      OS: "android",
      select: (obj: Record<string, unknown>) => obj.android ?? obj.default ?? null,
    },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    KeyboardAvoidingView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("KeyboardAvoidingView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    StyleSheet: {
      create: (styles: unknown) => styles,
      flatten: (style: unknown) => style,
    },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ replace: mockRouterReplace, push: jest.fn(), back: jest.fn() }),
}));

jest.mock("@expo/vector-icons", () => {
  const React = require("react");
  return {
    Ionicons: ({ name, ...props }: { name: string }) => React.createElement("Ionicons", { name, ...props }),
  };
});

jest.mock("expo-linear-gradient", () => {
  const React = require("react");
  return {
    LinearGradient: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("LinearGradient", props, children),
  };
});

jest.mock("@/lib/api", () => ({
  getAuthCapabilities: (...args: unknown[]) => mockGetAuthCapabilities(...args),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({
    login: (...args: unknown[]) => mockStoreLogin(...args),
  }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        border: "#d4d4d8",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
        danger: "#dc2626",
        success: "#16a34a",
      },
      spacing: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24 },
      radius: { sm: 8, md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, md: 16, base: 16, lg: 20, xl: 24, "2xl": 28 },
      shadow: { card: {} },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    title: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/components/Logo", () => {
  const React = require("react");
  return () => React.createElement("Logo");
});

jest.mock("@/components/ui/Button", () => {
  const React = require("react");
  return {
    Button: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
  };
});

jest.mock("@/components/ui/Input", () => {
  const React = require("react");
  return {
    Input: (props: unknown) => React.createElement("TextInput", props),
  };
});

const LoginScreen = require("../../app/(auth)/login").default;

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

async function submitLogin(role: "customer" | "supplier" | "logistics_partner" | "admin" | "sub_admin") {
  mockStoreLogin.mockResolvedValueOnce({
    id: 1,
    email: `${role}@zozi.com`,
    username: role,
    role,
  });

  let renderer!: TestRenderer.ReactTestRenderer;
  await act(async () => {
    renderer = TestRenderer.create(<LoginScreen />);
  });
  await flush();

  await act(async () => {
    renderer.root.findByProps({ testID: "auth-login-identifier" }).props.onChangeText("user@zozi.com");
    renderer.root.findByProps({ testID: "auth-login-password" }).props.onChangeText("Password123!");
  });

  await act(async () => {
    await renderer.root.findByProps({ testID: "auth-login-submit" }).props.onPress();
  });
  await flush();
}

describe("login screen routing", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAuthCapabilities.mockResolvedValue({
      google: false,
      facebook: false,
      customer_email_verification_required: false,
    });
  });

  it("routes supplier users to the supplier dashboard", async () => {
    await submitLogin("supplier");

    expect(mockRouterReplace).toHaveBeenCalledWith("/supplier/dashboard");
  });

  it("routes logistics users to the logistics dashboard", async () => {
    await submitLogin("logistics_partner");

    expect(mockRouterReplace).toHaveBeenCalledWith("/logistics-partner/dashboard");
  });

  it("routes admin and sub-admin users to the admin dashboard", async () => {
    await submitLogin("sub_admin");

    expect(mockRouterReplace).toHaveBeenCalledWith("/admin/dashboard");
  });

  it("routes customer users to the product feed", async () => {
    await submitLogin("customer");

    expect(mockRouterReplace).toHaveBeenCalledWith("/products");
  });
});