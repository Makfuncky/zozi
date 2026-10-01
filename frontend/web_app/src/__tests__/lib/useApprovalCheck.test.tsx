import React from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useApprovalCheck } from "@/hooks/useApprovalCheck";

const okJson = (data: unknown) =>
  new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

const mockApiFetch = jest.fn();

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  API_URL: "http://localhost:8000",
  getAccessToken: () => "fake-token",
}));

describe("useApprovalCheck", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
  });

  it("returns eligible:true when user is null", async () => {
    const { result } = renderHook(() => useApprovalCheck(null));
    const res = await result.current.canApprove("product");
    expect(res).toEqual({ eligible: true });
  });

  it("returns eligible:true when user has no id", async () => {
    const { result } = renderHook(() => useApprovalCheck({ id: 0 } as any));
    const res = await result.current.canApprove("product");
    expect(res).toEqual({ eligible: true });
  });

  it("calls the approval-matrix API with the right payload", async () => {
    mockApiFetch.mockResolvedValue(
      okJson({ can_approve: true, authority_level: 5, min_authority_level: 3 })
    );

    const { result } = renderHook(() => useApprovalCheck({ id: 42 } as any));

    let approved: any;
    await act(async () => {
      approved = await result.current.canApprove("product", 100);
    });

    expect(approved).toEqual({
      eligible: true,
      authorityLevel: 5,
      requiredLevel: 3,
    });
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/admin/hierarchy/approval-matrix/check?user_id=42&resource_type=product&amount=100",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    );
  });

  it("returns eligible:false with reason on non-ok response", async () => {
    mockApiFetch.mockResolvedValue(
      new Response(JSON.stringify({ detail: "Insufficient authority" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      })
    );

    const { result } = renderHook(() => useApprovalCheck({ id: 1 } as any));

    let approved: any;
    await act(async () => {
      approved = await result.current.canApprove("supplier");
    });

    expect(approved).toEqual({
      eligible: false,
      reason: "Insufficient authority",
    });
  });

  it("returns eligible:true on network/parse error", async () => {
    mockApiFetch.mockRejectedValue(new Error("network boom"));

    const { result } = renderHook(() => useApprovalCheck({ id: 1 } as any));

    let approved: any;
    await act(async () => {
      approved = await result.current.canApprove("payout");
    });

    expect(approved).toEqual({ eligible: true });
  });

  it("does not fire two identical API calls within the cache TTL", async () => {
    mockApiFetch.mockResolvedValue(
      okJson({ can_approve: true })
    );

    const { result } = renderHook(() => useApprovalCheck({ id: 7 } as any));

    await act(async () => {
      await result.current.canApprove("product", 50);
    });
    await act(async () => {
      await result.current.canApprove("product", 50);
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(1);
  });

  it("invalidates cache and allows a fresh API call", async () => {
    mockApiFetch.mockResolvedValue(
      okJson({ can_approve: true })
    );

    const { result } = renderHook(() => useApprovalCheck({ id: 7 } as any));

    await act(async () => {
      await result.current.canApprove("product", 50);
    });
    act(() => result.current.invalidateCache());
    await act(async () => {
      await result.current.canApprove("product", 50);
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
  });

  it("getEligibility returns cached eligibility from state", async () => {
    mockApiFetch.mockResolvedValue(
      okJson({ can_approve: false, reason: "blocked" })
    );

    const { result } = renderHook(() => useApprovalCheck({ id: 9 } as any));

    await act(async () => {
      await result.current.canApprove("product", 200);
    });

    const fromState = result.current.getEligibility("product", 200);
    expect(fromState?.eligible).toBe(false);
    expect(fromState?.reason).toBe("blocked");
  });
});
