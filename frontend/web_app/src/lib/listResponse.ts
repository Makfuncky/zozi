export interface ListPage<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}

export function normalizeListPage<T>(payload: unknown): ListPage<T> {
  if (Array.isArray(payload)) {
    return {
      data: payload as T[],
      total: payload.length,
      page: 1,
      pageSize: payload.length,
    };
  }

  if (!payload || typeof payload !== "object") {
    return { data: [], total: 0, page: 1, pageSize: 0 };
  }

  const envelope = payload as Record<string, unknown>;
  const data = Array.isArray(envelope.data)
    ? (envelope.data as T[])
    : Array.isArray(envelope.items)
      ? (envelope.items as T[])
      : [];
  const total = typeof envelope.total === "number" ? envelope.total : data.length;
  const page = typeof envelope.page === "number" && envelope.page > 0 ? envelope.page : 1;
  const pageSize = typeof envelope.pageSize === "number"
    ? envelope.pageSize
    : typeof envelope.page_size === "number"
      ? envelope.page_size
      : data.length;

  return { data, total, page, pageSize };
}
