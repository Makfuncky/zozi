jest.mock("react-native", () => ({ Platform: { OS: "android" } }));

import { useBackgroundJobStore } from "@/lib/backgroundJobStore";

beforeEach(() => {
  useBackgroundJobStore.getState().reset();
});

describe("backgroundJobStore", () => {
  it("upserts jobs and keeps the latest version", () => {
    useBackgroundJobStore.getState().upsertJob({
      id: "job-1",
      kind: "email-campaign-send",
      status: "queued",
      label: "Email campaign send",
      route: "/admin/email",
      created_at: "2026-03-30T10:00:00.000Z",
    });
    useBackgroundJobStore.getState().upsertJob({
      id: "job-1",
      kind: "email-campaign-send",
      status: "completed",
      label: "Email campaign send",
      route: "/admin/email",
      finished_at: "2026-03-30T10:01:00.000Z",
    });

    const jobs = useBackgroundJobStore.getState().jobs;
    expect(jobs).toHaveLength(1);
    expect(jobs[0].status).toBe("completed");
  });

  it("clears only finished jobs", () => {
    useBackgroundJobStore.getState().upsertJob({ id: "a", kind: "export", status: "queued", label: "Users export" });
    useBackgroundJobStore.getState().upsertJob({ id: "b", kind: "export", status: "completed", label: "Orders export" });

    useBackgroundJobStore.getState().clearFinishedJobs();

    const jobs = useBackgroundJobStore.getState().jobs;
    expect(jobs).toHaveLength(1);
    expect(jobs[0].id).toBe("a");
  });
});