import { normalizePaginatedList } from "@shared/adminListUtils";

describe("admin list normalization helpers", () => {
  it("preserves paginated envelopes returned by backend list routes", () => {
    const payload = normalizePaginatedList<{ id: number }>(
      {
        total: 3,
        page: 2,
        page_size: 2,
        total_pages: 2,
        items: [{ id: 3 }],
      },
      ["items", "results", "data", "verifications", "invoices"],
    );

    expect(payload).toEqual({
      total: 3,
      page: 2,
      page_size: 2,
      total_pages: 2,
      items: [{ id: 3 }],
    });
  });

  it("falls back to array payloads without losing records", () => {
    const payload = normalizePaginatedList<{ id: number }>([{ id: 8 }, { id: 9 }]);

    expect(payload.items).toEqual([{ id: 8 }, { id: 9 }]);
    expect(payload.total).toBe(2);
    expect(payload.total_pages).toBe(1);
  });
});