"use client";

import * as React from "react";

export type EnterpriseDensityMode = "compact" | "normal" | "expanded";

export interface EnterpriseColumn<T> {
  key: keyof T | string;
  label: string;
  width?: string;
  sortable?: boolean;
  searchable?: boolean;
  hidden?: boolean;
  align?: "left" | "center" | "right";
  sortValue?: (row: T) => string | number | boolean | null | undefined;
  searchValue?: (row: T) => string | number | boolean | null | undefined;
  render?: (row: T) => React.ReactNode;
}

export interface EnterpriseBulkAction<T> {
  label: string;
  onClick: (rows: T[]) => void;
  variant?: "default" | "primary" | "danger";
  disabled?: boolean;
}

export interface EnterpriseDataTableProps<T> {
  columns: Array<EnterpriseColumn<T>>;
  rows: T[];
  rowKey: (row: T) => string | number;
  densityMode?: EnterpriseDensityMode;
  rowsPerPageOptions?: number[];
  initialRowsPerPage?: number;
  title?: string;
  description?: string;
  enableBulkActions?: boolean;
  enableExport?: boolean;
  enableGlobalSearch?: boolean;
  searchPlaceholder?: string;
  rowActions?: (row: T) => React.ReactNode;
  mobileCardRenderer?: (row: T) => React.ReactNode;
  emptyState?: React.ReactNode;
  toolbarSlot?: React.ReactNode;
  onRowClick?: (row: T) => void;
  selectedRowKeys?: Array<string | number>;
  onSelectedRowKeysChange?: (keys: Array<string | number>, rows: T[]) => void;
  virtualizeRows?: boolean;
  virtualWindowHeight?: number;
  virtualOverscan?: number;
  showSelectionSummary?: boolean;
  showPagination?: boolean;
  expandedRowKey?: string | number;
  expandedRowRenderer?: (row: T) => React.ReactNode;
}

const ROW_HEIGHT: Record<EnterpriseDensityMode, number> = {
  compact: 32,
  normal: 38,
  expanded: 48,
};

const PAGE_SIZES = [10, 25, 50, 100];

function toneClass(variant: EnterpriseBulkAction<unknown>["variant"]): string {
  switch (variant) {
    case "primary":
      return "bg-primary text-on-brand hover:bg-primary/90";
    case "danger":
      return "bg-danger text-on-brand hover:bg-danger/85";
    default:
      return "bg-surface-2 text-text hover:bg-surface-1";
  }
}

function cellAlign(align: EnterpriseColumn<unknown>["align"]): string {
  if (align === "center") return "text-center";
  if (align === "right") return "text-right";
  return "text-left";
}

function normalize(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value.toLowerCase();
  if (typeof value === "number" || typeof value === "boolean") return String(value).toLowerCase();
  return "";
}

function stringify(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

export function EnterpriseDataTable<T>({
  columns,
  rows,
  rowKey,
  densityMode = "normal",
  rowsPerPageOptions = PAGE_SIZES,
  initialRowsPerPage = 25,
  title,
  description,
  enableBulkActions = false,
  enableExport = false,
  enableGlobalSearch = true,
  searchPlaceholder = "Search visible columns...",
  rowActions,
  mobileCardRenderer,
  emptyState,
  toolbarSlot,
  onRowClick,
  selectedRowKeys,
  onSelectedRowKeysChange,
  virtualizeRows = false,
  virtualWindowHeight = 560,
  virtualOverscan = 6,
  showSelectionSummary = true,
  showPagination = true,
  expandedRowKey,
  expandedRowRenderer,
}: EnterpriseDataTableProps<T>) {
  const [search, setSearch] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [rowsPerPage, setRowsPerPage] = React.useState(initialRowsPerPage);
  const [sortKey, setSortKey] = React.useState<string | null>(null);
  const [sortDir, setSortDir] = React.useState<"asc" | "desc">("asc");
  const [internalSelectedKeys, setInternalSelectedKeys] = React.useState<Set<string | number>>(new Set());
  const [scrollTop, setScrollTop] = React.useState(0);

  const selectedKeySet = React.useMemo(
    () => new Set(selectedRowKeys ?? Array.from(internalSelectedKeys)),
    [internalSelectedKeys, selectedRowKeys]
  );

  const syncSelectedKeys = React.useCallback((nextKeys: Set<string | number>) => {
    if (selectedRowKeys === undefined) {
      setInternalSelectedKeys(new Set(nextKeys));
    }
    onSelectedRowKeysChange?.(
      Array.from(nextKeys),
      rows.filter((row) => nextKeys.has(rowKey(row)))
    );
  }, [onSelectedRowKeysChange, rowKey, rows, selectedRowKeys]);

  const visibleColumns = React.useMemo(
    () => columns.filter((column) => !column.hidden),
    [columns]
  );

  const filteredRows = React.useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return rows;
    return rows.filter((row) =>
      visibleColumns.some((column) => {
        if (column.searchable === false) return false;
        const rawValue = column.searchValue
          ? column.searchValue(row)
          : column.render
            ? ""
            : (row as Record<string, unknown>)[String(column.key)];
        return normalize(rawValue).includes(query);
      })
    );
  }, [rows, search, visibleColumns]);

  const sortedRows = React.useMemo(() => {
    if (!sortKey) return filteredRows;
    const sortColumn = visibleColumns.find((column) => String(column.key) === sortKey);
    const next = [...filteredRows];
    next.sort((left, right) => {
      const leftRaw = sortColumn?.sortValue
        ? sortColumn.sortValue(left)
        : (left as Record<string, unknown>)[sortKey];
      const rightRaw = sortColumn?.sortValue
        ? sortColumn.sortValue(right)
        : (right as Record<string, unknown>)[sortKey];

      if (typeof leftRaw === "number" && typeof rightRaw === "number") {
        if (leftRaw === rightRaw) return 0;
        const result = leftRaw > rightRaw ? 1 : -1;
        return sortDir === "asc" ? result : -result;
      }

      const leftValue = normalize(leftRaw);
      const rightValue = normalize(rightRaw);
      if (leftValue === rightValue) return 0;
      const result = leftValue > rightValue ? 1 : -1;
      return sortDir === "asc" ? result : -result;
    });
    return next;
  }, [filteredRows, sortDir, sortKey, visibleColumns]);

  const totalPages = showPagination ? Math.max(1, Math.ceil(sortedRows.length / rowsPerPage)) : 1;
  const pageRows = React.useMemo(
    () => showPagination ? sortedRows.slice((page - 1) * rowsPerPage, page * rowsPerPage) : sortedRows,
    [page, rowsPerPage, showPagination, sortedRows]
  );
  const shouldVirtualizeDesktop = virtualizeRows && pageRows.length > 12;
  const desktopWindow = React.useMemo(() => {
    if (!shouldVirtualizeDesktop) {
      return {
        rows: pageRows,
        topSpacerHeight: 0,
        bottomSpacerHeight: 0,
      };
    }
    const rowHeight = ROW_HEIGHT[densityMode];
    const visibleCount = Math.max(1, Math.ceil(virtualWindowHeight / rowHeight));
    const startIndex = Math.max(0, Math.floor(scrollTop / rowHeight) - virtualOverscan);
    const endIndex = Math.min(pageRows.length, startIndex + visibleCount + virtualOverscan * 2);
    return {
      rows: pageRows.slice(startIndex, endIndex),
      topSpacerHeight: startIndex * rowHeight,
      bottomSpacerHeight: Math.max(0, (pageRows.length - endIndex) * rowHeight),
    };
  }, [densityMode, pageRows, scrollTop, shouldVirtualizeDesktop, virtualOverscan, virtualWindowHeight]);

  const selectedRows = React.useMemo(
    () => rows.filter((row) => selectedKeySet.has(rowKey(row))),
    [rowKey, rows, selectedKeySet]
  );

  React.useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  React.useEffect(() => {
    setScrollTop(0);
  }, [page, rowsPerPage, search, sortDir, sortKey]);

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((value) => (value === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDir("asc");
  };

  const toggleRow = (key: string | number) => {
    const next = new Set(selectedKeySet);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    syncSelectedKeys(next);
  };

  const togglePageSelection = () => {
    const pageKeys = pageRows.map((row) => rowKey(row));
    const allSelected = pageKeys.length > 0 && pageKeys.every((key) => selectedKeySet.has(key));
    const next = new Set(selectedKeySet);
    if (allSelected) pageKeys.forEach((key) => next.delete(key));
    else pageKeys.forEach((key) => next.add(key));
    syncSelectedKeys(next);
  };

  const exportCsv = () => {
    const header = visibleColumns.map((column) => column.label);
    const lines = sortedRows.map((row) =>
      visibleColumns.map((column) => {
        const raw = column.searchValue
          ? column.searchValue(row)
          : column.sortValue
            ? column.sortValue(row)
            : (row as Record<string, unknown>)[String(column.key)];
        return `"${stringify(raw).replace(/"/g, '""')}"`;
      }).join(",")
    );
    const blob = new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "enterprise-data-export.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const densityPadding = densityMode === "compact" ? "px-2.5 py-1.5" : densityMode === "expanded" ? "px-3.5 py-3" : "px-2.5 py-2";
  const densityText = densityMode === "compact" ? "text-[12px]" : densityMode === "expanded" ? "text-sm" : "text-[13px]";
  const rangeStart = sortedRows.length === 0 ? 0 : (page - 1) * rowsPerPage + 1;
  const rangeEnd = Math.min(page * rowsPerPage, sortedRows.length);

  return (
    <section className="space-y-2.5">
      {(title || description || enableGlobalSearch || enableExport || toolbarSlot) ? (
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div className="min-w-0">
            {title ? <h2 className="text-base font-semibold text-text">{title}</h2> : null}
            {description ? <p className="mt-1 text-[13px] text-text-muted">{description}</p> : null}
          </div>
          <div className="flex w-full flex-wrap items-center gap-2 xl:w-auto xl:justify-end">
            {enableGlobalSearch ? (
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={searchPlaceholder}
                className="h-9 min-w-[15rem] flex-1 rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none xl:flex-none"
              />
            ) : null}
            {toolbarSlot}
            {enableExport ? (
              <button
                type="button"
                onClick={exportCsv}
                className="h-9 rounded-xl border border-border bg-surface-1 px-3 text-xs font-medium text-text transition-colors hover:bg-surface-2"
              >
                Export CSV
              </button>
            ) : null}
          </div>
        </div>
      ) : null}

      {enableBulkActions && showSelectionSummary && selectedRows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-surface-1 px-3 py-2">
          <span className="text-xs font-medium text-text">{selectedRows.length} selected</span>
          <button
            type="button"
            onClick={() => syncSelectedKeys(new Set<string | number>())}
            className="rounded-lg px-2 py-1 text-xs text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
          >
            Clear
          </button>
        </div>
      ) : null}

      <div className="hidden overflow-hidden rounded-xl border border-border bg-surface lg:block">
        <div
          className="overflow-x-auto"
          style={shouldVirtualizeDesktop ? { maxHeight: virtualWindowHeight, overflowY: "auto" } : undefined}
          onScroll={shouldVirtualizeDesktop ? (event) => setScrollTop(event.currentTarget.scrollTop) : undefined}
        >
          <table className="min-w-full table-fixed border-collapse">
            <thead className="bg-surface-2/70">
              <tr>
                {enableBulkActions ? (
                  <th className={`${densityPadding} w-12 text-left`}>
                    <input
                      type="checkbox"
                      checked={pageRows.length > 0 && pageRows.every((row) => selectedKeySet.has(rowKey(row)))}
                      onChange={togglePageSelection}
                      aria-label="Select current page"
                      className="h-3.5 w-3.5 rounded accent-primary"
                    />
                  </th>
                ) : null}
                {visibleColumns.map((column) => (
                  <th
                    key={String(column.key)}
                    style={column.width ? { width: column.width } : undefined}
                    className={`${densityPadding} ${densityText} ${cellAlign(column.align)} text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint`}
                  >
                    {column.sortable ? (
                      <button
                        type="button"
                        onClick={() => toggleSort(String(column.key))}
                        className="inline-flex items-center gap-1 hover:text-text"
                      >
                        {column.label}
                        <span className="text-[10px] text-text-faint">{sortKey === String(column.key) ? (sortDir === "asc" ? "↑" : "↓") : "↕"}</span>
                      </button>
                    ) : column.label}
                  </th>
                ))}
                {rowActions ? <th className={`${densityPadding} text-right text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint`}>Actions</th> : null}
              </tr>
            </thead>
<tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td colSpan={visibleColumns.length + (enableBulkActions ? 1 : 0) + (rowActions ? 1 : 0)} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-2 mb-3">
                        <svg className="h-6 w-6 text-text-faint" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.25 16.5h-16l-.25-16.5m16.5 0l-1.344-7.716A2.25 2.25 0 0016.5 4.5h-9a2.25 2.25 0 00-2.25 2.25V12m16.5 0v6.75m0 0l-1.344 7.716A2.25 2.25 0 0116.5 21h-9a2.25 2.25 0 01-2.25-2.25v-6.75m16.5 0V12" />
                        </svg>
                      </div>
                      <p className="text-sm font-medium text-text">{emptyState ?? "No data found."}</p>
                      <p className="mt-1 text-xs text-text-faint">Try adjusting your search or filters</p>
                    </div>
                  </td>
                </tr>
              ) : (
                <>
                  {shouldVirtualizeDesktop && desktopWindow.topSpacerHeight > 0 ? (
                    <tr>
                      <td
                        colSpan={visibleColumns.length + (enableBulkActions ? 1 : 0) + (rowActions ? 1 : 0)}
                        style={{ height: desktopWindow.topSpacerHeight, padding: 0 }}
                      />
                    </tr>
                  ) : null}
                  {desktopWindow.rows.map((row) => (
                    <React.Fragment key={String(rowKey(row))}>
                      <tr
                        className="border-t border-border/60 transition-colors hover:bg-surface-2/40"
                      >
                        {enableBulkActions ? (
                          <td className={densityPadding}>
                            <input
                              type="checkbox"
                              checked={selectedKeySet.has(rowKey(row))}
                              onChange={() => toggleRow(rowKey(row))}
                              aria-label={`Select row ${rowKey(row)}`}
                              className="h-3.5 w-3.5 rounded accent-primary"
                            />
                          </td>
                        ) : null}
                        {visibleColumns.map((column) => (
                          <td
                            key={String(column.key)}
                            className={`${densityPadding} ${densityText} ${cellAlign(column.align)} text-text`}
                            style={{ height: ROW_HEIGHT[densityMode] }}
                            onClick={onRowClick ? () => onRowClick(row) : undefined}
                          >
                            {column.render ? column.render(row) : String((row as Record<string, unknown>)[String(column.key)] ?? "—")}
                          </td>
                        ))}
                        {rowActions ? <td className={`${densityPadding} text-right`}>{rowActions(row)}</td> : null}
                      </tr>
                      {expandedRowKey !== undefined && rowKey(row) === expandedRowKey && expandedRowRenderer ? (
                        <tr key={`${String(rowKey(row))}-expanded`} className="border-t border-border/60">
                          <td colSpan={visibleColumns.length + (enableBulkActions ? 1 : 0) + (rowActions ? 1 : 0)} className="p-0">
                            {expandedRowRenderer(row)}
                          </td>
                        </tr>
                      ) : null}
                    </React.Fragment>
                  ))}
                  {shouldVirtualizeDesktop && desktopWindow.bottomSpacerHeight > 0 ? (
                    <tr>
                      <td
                        colSpan={visibleColumns.length + (enableBulkActions ? 1 : 0) + (rowActions ? 1 : 0)}
                        style={{ height: desktopWindow.bottomSpacerHeight, padding: 0 }}
                      />
                    </tr>
                  ) : null}
                </>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-3 lg:hidden">
        {pageRows.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-surface-1 px-4 py-12 text-center">
            <div className="flex flex-col items-center justify-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-2 mb-3">
                <svg className="h-6 w-6 text-text-faint" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.25 16.5h-16l-.25-16.5m16.5 0l-1.344-7.716A2.25 2.25 0 0016.5 4.5h-9a2.25 2.25 0 00-2.25 2.25V12m16.5 0v6.75m0 0l-1.344 7.716A2.25 2.25 0 0116.5 21h-9a2.25 2.25 0 01-2.25-2.25v-6.75m16.5 0V12" />
                </svg>
              </div>
              <p className="text-sm font-medium text-text">{emptyState ?? "No data found."}</p>
              <p className="mt-1 text-xs text-text-faint">Try adjusting your search or filters</p>
            </div>
          </div>
        ) : (
          pageRows.map((row) => (
            <React.Fragment key={String(rowKey(row))}>
              <div className="rounded-xl border border-border bg-surface-1 p-3 shadow-sm">
                {mobileCardRenderer ? mobileCardRenderer(row) : (
                  <div className="space-y-2">
                    {enableBulkActions ? (
                      <label className="flex items-center gap-2 text-xs text-text-muted">
                        <input
                          type="checkbox"
                          checked={selectedKeySet.has(rowKey(row))}
                          onChange={() => toggleRow(rowKey(row))}
                          className="h-3.5 w-3.5 rounded accent-primary"
                        />
                        Select row
                      </label>
                    ) : null}
                    {visibleColumns.map((column) => (
                      <div key={String(column.key)} className="flex items-start justify-between gap-3 text-xs">
                        <span className="font-semibold uppercase tracking-[0.16em] text-text-faint">{column.label}</span>
                        <span className="text-right text-text">{column.render ? column.render(row) : String((row as Record<string, unknown>)[String(column.key)] ?? "—")}</span>
                      </div>
                    ))}
                    {rowActions ? <div className="pt-2">{rowActions(row)}</div> : null}
                  </div>
                )}
              </div>
              {expandedRowKey !== undefined && rowKey(row) === expandedRowKey && expandedRowRenderer ? (
                <div className="rounded-xl border border-border bg-surface-2/60">
                  {expandedRowRenderer(row)}
                </div>
              ) : null}
            </React.Fragment>
          ))
        )}
      </div>

      {showPagination ? (
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-text-muted">
          <div className="flex items-center gap-2">
            <span>{rangeStart}-{rangeEnd} of {sortedRows.length}</span>
            <select
              value={rowsPerPage}
              onChange={(event) => {
                setRowsPerPage(Number(event.target.value));
                setPage(1);
              }}
              className="h-8 rounded-lg border border-border bg-surface-1 px-2 text-xs text-text focus:border-primary focus:outline-none"
              aria-label="Rows per page"
            >
              {rowsPerPageOptions.map((size) => <option key={size} value={size}>{size} / page</option>)}
            </select>
          </div>
          <div className="flex items-center gap-1">
            <button type="button" onClick={() => setPage(1)} disabled={page === 1} className="rounded-lg bg-surface-1 px-2 py-1 transition-colors hover:bg-surface-2 disabled:opacity-40">«</button>
            <button type="button" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={page === 1} className="rounded-lg bg-surface-1 px-2 py-1 transition-colors hover:bg-surface-2 disabled:opacity-40">‹</button>
            <span className="px-2">{page} / {totalPages}</span>
            <button type="button" onClick={() => setPage((value) => Math.min(totalPages, value + 1))} disabled={page === totalPages} className="rounded-lg bg-surface-1 px-2 py-1 transition-colors hover:bg-surface-2 disabled:opacity-40">›</button>
            <button type="button" onClick={() => setPage(totalPages)} disabled={page === totalPages} className="rounded-lg bg-surface-1 px-2 py-1 transition-colors hover:bg-surface-2 disabled:opacity-40">»</button>
          </div>
        </div>
      ) : null}
    </section>
  );
}