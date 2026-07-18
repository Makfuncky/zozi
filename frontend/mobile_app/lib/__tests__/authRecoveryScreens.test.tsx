import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockForgotPassword = jest.fn();
const mockResetPassword = jest.fn();

let currentLocalSearchParams: Record<string, string | undefined> = {};

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: {
      OS: "android",
      select: (obj: Record<string, unknown>) => obj["android"] ?? obj["default"] ?? null,
    },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    KeyboardAvoidingView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("KeyboardAvoidingView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    StyleSheet: {
      create: (styles: unknown) => styles,
      flatten: (style: unknown) => style,
    },
  };
});

jest.mock("expo-router", () => {
  const stableRouter = { push: jest.fn(), replace: jest.fn(), back: jest.fn() };
  return {
    Stack: { Screen: () => null },
    useRouter: () => stableRouter,
    useLocalSearchParams: () => currentLocalSearchParams,
  };
});

jest.mock("@/lib/api", () => ({
  forgotPassword: (...args: unknown[]) => mockForgotPassword(...args),
  resetPassword: (...args: unknown[]) => mockResetPassword(...args),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        danger: "#dc2626",
        border: "#d4d4d8",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
      },
      spacing: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24 },
      radius: { sm: 8, md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, md: 16, base: 16, lg: 20, xl: 24, "2xl": 28, "3xl": 32 },
    },
    mode: "light",
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    title: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

const ForgotPasswordScreen = require("../../app/(auth)/forgot-password").default;
const ResetPasswordScreen = require("../../app/(auth)/reset-password").default;

function flattenText(value: unknown): string {
  if (Array.isArray(value)) return value.map(flattenText).join(" ");
  if (value == null || typeof value === "boolean") return "";
  return String(value);
}

function getRenderedText(renderer: TestRenderer.ReactTestRenderer): string {
  return renderer.root
    .findAll((node) => String(node.type) === "Text")
    .map((node) => flattenText(node.props.children))
    .join(" ");
}

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("auth recovery screens", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    currentLocalSearchParams = {};
  });

  it("renders forgot-password screen with deterministic test hooks", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ForgotPasswordScreen />);
    });

    expect(renderer.root.findByProps({ testID: "auth-forgot-password-screen" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "auth-forgot-password-email" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "auth-forgot-password-submit" })).toBeTruthy();
  });

  it("submits forgot-password email and shows success state", async () => {
    mockForgotPassword.mockResolvedValueOnce(undefined);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ForgotPasswordScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "auth-forgot-password-email" }).props.onChangeText("customer@zozi.com");
    });
    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-forgot-password-submit" }).props.onPress();
    });
    await flush();

    expect(mockForgotPassword).toHaveBeenCalledWith("customer@zozi.com");
    expect(renderer.root.findByProps({ testID: "auth-forgot-password-success" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("We sent a password reset link to");
    expect(getRenderedText(renderer)).toContain("customer@zozi.com");
  });

  it("shows validation and API errors on forgot-password screen", async () => {
    mockForgotPassword.mockRejectedValueOnce(new Error("Mailbox unavailable"));

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ForgotPasswordScreen />);
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-forgot-password-submit" }).props.onPress();
    });
    expect(getRenderedText(renderer)).toContain("Email is required");

    await act(async () => {
      renderer.root.findByProps({ testID: "auth-forgot-password-email" }).props.onChangeText("customer@zozi.com");
    });
    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-forgot-password-submit" }).props.onPress();
    });
    await flush();

    expect(renderer.root.findByProps({ testID: "auth-forgot-password-error" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Mailbox unavailable");
  });

  it("renders reset-password screen with deterministic test hooks", async () => {
    currentLocalSearchParams = { token: "reset-token" };

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ResetPasswordScreen />);
    });

    expect(renderer.root.findByProps({ testID: "auth-reset-password-screen" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "auth-reset-password-password" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "auth-reset-password-confirm" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "auth-reset-password-submit" })).toBeTruthy();
  });

  it("submits reset-password form and shows success state", async () => {
    currentLocalSearchParams = { token: "reset-token" };
    mockResetPassword.mockResolvedValueOnce(undefined);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ResetPasswordScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "auth-reset-password-password" }).props.onChangeText("new-password-123");
      renderer.root.findByProps({ testID: "auth-reset-password-confirm" }).props.onChangeText("new-password-123");
    });
    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-reset-password-submit" }).props.onPress();
    });
    await flush();

    expect(mockResetPassword).toHaveBeenCalledWith("reset-token", "new-password-123");
    expect(renderer.root.findByProps({ testID: "auth-reset-password-success" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Your password has been updated");
  });

  it("shows validation errors on reset-password screen", async () => {
    currentLocalSearchParams = { token: "reset-token" };

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ResetPasswordScreen />);
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-reset-password-submit" }).props.onPress();
    });
    expect(getRenderedText(renderer)).toContain("Password is required");

    await act(async () => {
      renderer.root.findByProps({ testID: "auth-reset-password-password" }).props.onChangeText("short");
      renderer.root.findByProps({ testID: "auth-reset-password-confirm" }).props.onChangeText("short");
    });
    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-reset-password-submit" }).props.onPress();
    });
    expect(getRenderedText(renderer)).toContain("Password must be at least 8 characters");
  });

  it("shows token and mismatch errors on reset-password screen", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ResetPasswordScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "auth-reset-password-password" }).props.onChangeText("valid-password");
      renderer.root.findByProps({ testID: "auth-reset-password-confirm" }).props.onChangeText("different-password");
    });
    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-reset-password-submit" }).props.onPress();
    });
    expect(getRenderedText(renderer)).toContain("Passwords do not match");

    await act(async () => {
      renderer.root.findByProps({ testID: "auth-reset-password-confirm" }).props.onChangeText("valid-password");
    });
    await act(async () => {
      await renderer.root.findByProps({ testID: "auth-reset-password-submit" }).props.onPress();
    });
    expect(renderer.root.findByProps({ testID: "auth-reset-password-error" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Invalid or missing reset token");
  });
});