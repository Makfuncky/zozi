/**
 * toastStore.test.ts
 * Tests the Zustand toast store — show, dismiss, and auto-dismiss timing.
 */

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

import { useToastStore, toast } from "@/lib/toastStore";

beforeEach(() => {
  jest.useFakeTimers();
  useToastStore.setState({ toasts: [] });
});

afterEach(() => {
  jest.useRealTimers();
});

describe("toastStore — show & dismiss", () => {
  it("show() adds a toast with the correct type and message", () => {
    useToastStore.getState().show("success", "Saved!");
    const { toasts } = useToastStore.getState();
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe("success");
    expect(toasts[0].message).toBe("Saved!");
  });

  it("show() assigns a unique string id", () => {
    useToastStore.getState().show("info", "First");
    useToastStore.getState().show("info", "Second");
    const { toasts } = useToastStore.getState();
    expect(toasts[0].id).not.toBe(toasts[1].id);
  });

  it("dismiss() removes only the targeted toast", () => {
    useToastStore.getState().show("error", "Error one");
    useToastStore.getState().show("warning", "Warning two");
    const id = useToastStore.getState().toasts[0].id;
    useToastStore.getState().dismiss(id);
    const { toasts } = useToastStore.getState();
    expect(toasts).toHaveLength(1);
    expect(toasts[0].message).toBe("Warning two");
  });

  it("auto-dismisses after the default 3500ms", () => {
    useToastStore.getState().show("info", "Auto-dismiss me");
    expect(useToastStore.getState().toasts).toHaveLength(1);
    jest.advanceTimersByTime(3500);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("auto-dismisses after a custom duration", () => {
    useToastStore.getState().show("success", "Quick", 1000);
    jest.advanceTimersByTime(999);
    expect(useToastStore.getState().toasts).toHaveLength(1);
    jest.advanceTimersByTime(1);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("supports multiple simultaneous toasts", () => {
    useToastStore.getState().show("success", "A");
    useToastStore.getState().show("error", "B");
    useToastStore.getState().show("info", "C");
    expect(useToastStore.getState().toasts).toHaveLength(3);
  });
});

describe("toastStore — convenience helpers", () => {
  it("toast.success() shows a success toast", () => {
    toast.success("Great!");
    const { toasts } = useToastStore.getState();
    expect(toasts[0].type).toBe("success");
    expect(toasts[0].message).toBe("Great!");
  });

  it("toast.error() shows an error toast", () => {
    toast.error("Oops");
    expect(useToastStore.getState().toasts[0].type).toBe("error");
  });

  it("toast.info() shows an info toast", () => {
    toast.info("FYI");
    expect(useToastStore.getState().toasts[0].type).toBe("info");
  });

  it("toast.warning() shows a warning toast", () => {
    toast.warning("Heads up");
    expect(useToastStore.getState().toasts[0].type).toBe("warning");
  });
});
