"use client";
import { cn } from "@/lib/utils";
type HeadingLevel = 1 | 2 | 3 | 4;
const levelClasses: Record<HeadingLevel, string> = {
  1: "text-4xl font-extrabold tracking-tight text-text",
  2: "text-2xl font-bold text-text",
  3: "text-xl font-semibold text-text",
  4: "text-lg font-medium text-text",
};
interface HeadingProps { level: HeadingLevel; children: React.ReactNode; className?: string; id?: string; }
export function Heading({ level, children, className, id }: HeadingProps) {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
  return <Tag className={cn(levelClasses[level], className)} id={id}>{children}</Tag>;
}
