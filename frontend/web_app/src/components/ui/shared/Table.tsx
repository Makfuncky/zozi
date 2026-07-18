"use client";

import { cn } from "@/lib/utils";

export interface TableProps {
  className?: string;
  children: React.ReactNode;
}

export function Table({ className, children }: TableProps) {
  return (
    <div className={cn("glass-panel rounded-xl border border-glass-border-mid overflow-hidden", className)}>
      <table className="w-full text-left text-xs">
        {children}
      </table>
    </div>
  );
}

export interface TableHeaderProps {
  className?: string;
  children: React.ReactNode;
}

export function TableHeader({ className, children }: TableHeaderProps) {
  return (
    <thead className={cn("bg-glass-solid border-b border-glass-border text-text-muted", className)}>
      <tr>
        {children}
      </tr>
    </thead>
  );
}

export interface TableHeaderCellProps {
  className?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export function TableHeaderCell({ className, children, icon }: TableHeaderCellProps) {
  return (
    <th className={cn("px-3 py-2 font-semibold text-[11px] uppercase tracking-[0.1em]", className)}>
      <div className="flex items-center gap-1.5">
        {icon}
        {children}
      </div>
    </th>
  );
}

export interface TableBodyProps {
  className?: string;
  children: React.ReactNode;
}

export function TableBody({ className, children }: TableBodyProps) {
  return (
    <tbody className={cn("divide-y divide-glass-border", className)}>
      {children}
    </tbody>
  );
}

export interface TableRowProps {
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
  hover?: boolean;
}

export function TableRow({ className, children, onClick, hover = true }: TableRowProps) {
  return (
    <tr 
      className={cn(
        hover && "hover:bg-glass-panel-hover transition-colors",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

export interface TableCellProps {
  className?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  mono?: boolean;
  colSpan?: number;
}

export function TableCell({ className, children, mono, colSpan }: TableCellProps) {
  return (
    <td className={cn("px-3 py-2 text-text", mono && "font-mono text-text-muted", className)} colSpan={colSpan}>
      {children}
    </td>
  );
}