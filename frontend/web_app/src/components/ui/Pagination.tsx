"use client";
import { cn } from "@/lib/utils";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({ currentPage, totalPages, onPageChange, className }: PaginationProps) {
  const pages = getPageNumbers(currentPage, totalPages);

  return (
    <nav className={cn("flex items-center gap-1", className)} aria-label="Pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="flex items-center justify-center w-8 h-8 rounded-lg text-text-muted hover:text-text hover:bg-glass-panel disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Previous page"
      >
        ←
      </button>
      {pages.map((page, i) => (
        <button
          key={i}
          onClick={() => typeof page === "number" && onPageChange(page)}
          disabled={page === "..."}
          className={cn("flex items-center justify-center w-8 h-8 rounded-lg text-sm font-medium transition-colors", page === currentPage ? "bg-brand text-on-brand" : "text-text-muted hover:text-text hover:bg-glass-panel", page === "..." && "cursor-default")}
          aria-current={page === currentPage ? "page" : undefined}
        >
          {page}
        </button>
      ))}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="flex items-center justify-center w-8 h-8 rounded-lg text-text-muted hover:text-text hover:bg-glass-panel disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Next page"
      >
        →
      </button>
    </nav>
  );
}

function getPageNumbers(current: number, total: number): (number | string)[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (current <= 3) return [1, 2, 3, 4, "...", total];
  if (current >= total - 2) return [1, "...", total - 3, total - 2, total - 1, total];
  return [1, "...", current - 1, current, current + 1, "...", total];
}
