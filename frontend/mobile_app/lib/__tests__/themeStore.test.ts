/**
 * Tests for mobile_app/lib/themeStore.ts
 */

const mockGetItemAsync = jest.fn();
const mockSetItemAsync = jest.fn();

jest.mock("react-native", () => ({
  Platform: { OS: "android" },
  Appearance: { getColorScheme: jest.fn(() => "light") },
}));

jest.mock("expo-secure-store", () => ({
  getItemAsync: (...args: any[]) => mockGetItemAsync(...args),
  setItemAsync: (...args: any[]) => mockSetItemAsync(...args),
  deleteItemAsync: jest.fn(),
}));

jest.mock("@/lib/api", () => ({ apiFetch: jest.fn() }));

import { useThemeStore } from "@/lib/themeStore";

beforeEach(() => {
  useThemeStore.setState({ mode: "dark", initialized: false } as any);
  jest.clearAllMocks();
});

describe("themeStore — initTheme", () => {
  it("uses stored theme when available", async () => {
    mockGetItemAsync.mockResolvedValueOnce("light");

    await useThemeStore.getState().initTheme();

    expect(useThemeStore.getState().mode).toBe("light");
    expect(useThemeStore.getState().initialized).toBe(true);
  });

  it("falls back to system preference when no stored theme", async () => {
    mockGetItemAsync.mockResolvedValueOnce(null);
    // Appearance.getColorScheme() is mocked to return "light"

    await useThemeStore.getState().initTheme();

    expect(useThemeStore.getState().mode).toBe("light");
    expect(mockSetItemAsync).toHaveBeenCalledWith("zozi-theme", "light");
  });

  it("defaults to dark when system returns null", async () => {
    const { Appearance } = require("react-native");
    Appearance.getColorScheme.mockReturnValueOnce(null);
    mockGetItemAsync.mockResolvedValueOnce(null);

    await useThemeStore.getState().initTheme();

    expect(useThemeStore.getState().mode).toBe("dark");
  });
});

describe("themeStore — setMode", () => {
  it("setMode('light') switches to light and persists", async () => {
    mockSetItemAsync.mockResolvedValueOnce(undefined);

    await useThemeStore.getState().setMode("light");

    expect(useThemeStore.getState().mode).toBe("light");
    expect(mockSetItemAsync).toHaveBeenCalledWith("zozi-theme", "light");
  });

  it("setMode('dark') switches to dark theme", async () => {
    mockSetItemAsync.mockResolvedValueOnce(undefined);
    await useThemeStore.getState().setMode("light");

    mockSetItemAsync.mockResolvedValueOnce(undefined);
    await useThemeStore.getState().setMode("dark");

    expect(useThemeStore.getState().mode).toBe("dark");
  });
});

describe("themeStore — toggle", () => {
  it("toggles from dark to light", async () => {
    useThemeStore.setState({ mode: "dark" } as any);
    mockSetItemAsync.mockResolvedValue(undefined);

    await (useThemeStore.getState().toggle as any)();

    expect(useThemeStore.getState().mode).toBe("light");
  });

  it("toggles from light to dark", async () => {
    useThemeStore.setState({ mode: "light" } as any);
    mockSetItemAsync.mockResolvedValue(undefined);

    await (useThemeStore.getState().toggle as any)();

    expect(useThemeStore.getState().mode).toBe("dark");
  });
});
