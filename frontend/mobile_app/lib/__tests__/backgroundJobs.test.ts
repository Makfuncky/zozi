jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-file-system/legacy", () => ({
  cacheDirectory: "file:///cache/",
  documentDirectory: "file:///documents/",
  downloadAsync: jest.fn(),
}));
jest.mock("expo-sharing", () => ({
  isAvailableAsync: jest.fn().mockResolvedValue(true),
  shareAsync: jest.fn().mockResolvedValue(undefined),
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  API_BASE: "http://localhost:8000",
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getCurrentAccessToken: () => "token-123",
}));

import { trackBackgroundJob } from "@/lib/backgroundJobs";
import { useBackgroundJobStore } from "@/lib/backgroundJobStore";
import { useToastStore } from "@/lib/toastStore";

beforeEach(() => {
  jest.useFakeTimers();
  mockApiFetch.mockReset();
  useBackgroundJobStore.getState().reset();
  useToastStore.setState({ toasts: [] });
});

afterEach(() => {
  jest.useRealTimers();
});

describe("trackBackgroundJob", () => {
  it("polls until completion and stores the final job", async () => {
    mockApiFetch
      .mockResolvedValueOnce({ id: "job-1", kind: "email-campaign-send", status: "running" })
      .mockResolvedValueOnce({ id: "job-1", kind: "email-campaign-send", status: "completed", result: { recipient_count: 12 } });

    const promise = trackBackgroundJob(
      { id: "job-1", kind: "email-campaign-send", status: "queued" },
      { label: "Email campaign send", queuedToast: false },
    );

    await jest.advanceTimersByTimeAsync(2400);
    const finalJob = await promise;

    expect(finalJob.status).toBe("completed");
    expect(useBackgroundJobStore.getState().jobs[0].status).toBe("completed");
  });

  it("marks the tracked job as failed when polling throws", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Network down"));

    const promise = trackBackgroundJob(
      { id: "job-2", kind: "export", status: "queued" },
      { label: "Orders export", queuedToast: false, errorToast: false },
    );
    const rejection = expect(promise).rejects.toThrow("Network down");

    await jest.advanceTimersByTimeAsync(1200);
    await rejection;

    expect(useBackgroundJobStore.getState().jobs[0].status).toBe("failed");
  });
});