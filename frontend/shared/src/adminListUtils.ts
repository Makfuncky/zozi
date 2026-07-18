export interface PaginatedListEnvelope<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

function toFiniteNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function getArrayFromRecord<T>(
  record: Record<string, unknown>,
  keys: readonly string[],
): T[] {
  for (const key of keys) {
    const value = record[key];
    if (Array.isArray(value)) {
      return value as T[];
    }
  }
  return [];
}

export function normalizePaginatedList<T>(
  payload: unknown,
  keys: readonly string[] = ["items", "results", "data"],
): PaginatedListEnvelope<T> {
  if (Array.isArray(payload)) {
    return {
      items: payload as T[],
      total: payload.length,
      page: 1,
      page_size: payload.length,
      total_pages: 1,
    };
  }

  if (!payload || typeof payload !== "object") {
    return {
      items: [],
      total: 0,
      page: 1,
      page_size: 0,
      total_pages: 1,
    };
  }

  const record = payload as Record<string, unknown>;
  const items = getArrayFromRecord<T>(record, keys);
  const page = toFiniteNumber(record.page, 1);
  const total = toFiniteNumber(record.total, items.length);
  const pageSize = toFiniteNumber(record.page_size, items.length);
  const totalPages = toFiniteNumber(
    record.total_pages,
    Math.max(1, pageSize > 0 ? Math.ceil(total / pageSize) : 1),
  );

  return {
    items,
    total,
    page,
    page_size: pageSize,
    total_pages: totalPages,
  };
}