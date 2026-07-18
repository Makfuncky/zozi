/**
 * Shared returns API helpers.
 * These work with a standard fetch wrapper — provide `apiFetch` compatible with
 * your platform (web or mobile).
 */

export interface ReturnItem {
  product_id: number;
  product_name?: string;
  quantity: number;
  price?: number;
}

export interface ReturnRequestPayload {
  order_id: number;
  reason: string;
  items?: ReturnItem[];
}

export interface ReturnRequestData {
  id: number;
  order_id: number;
  user_id?: number;
  reason: string;
  status: "pending" | "approved" | "rejected" | "completed" | "refunded";
  refund_amount?: number;
  notes?: string;
  items?: ReturnItem[];
  created_at: string;
  updated_at?: string;
}

interface ErrorDetailResponse {
  detail?: string;
}

type FetchFn = (path: string, init?: RequestInit) => Promise<Response>;

export function createReturnsApi(apiFetch: FetchFn) {
  return {
    async listReturns(): Promise<ReturnRequestData[]> {
      const res = await apiFetch("/returns");
      if (!res.ok) throw new Error("Failed to fetch returns");
      return res.json();
    },

    async getReturn(id: number): Promise<ReturnRequestData> {
      const res = await apiFetch(`/returns/${id}`);
      if (!res.ok) throw new Error("Return not found");
      return res.json();
    },

    async createReturn(data: ReturnRequestPayload): Promise<ReturnRequestData> {
      const res = await apiFetch("/returns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as ErrorDetailResponse;
        throw new Error(err.detail ?? "Failed to create return request");
      }
      return res.json();
    },

    async updateReturnStatus(
      id: number,
      status: ReturnRequestData["status"],
      notes?: string,
      refund_amount?: number,
    ): Promise<ReturnRequestData> {
      const res = await apiFetch(`/returns/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, notes, refund_amount }),
      });
      if (!res.ok) throw new Error("Failed to update return status");
      return res.json();
    },
  };
}
