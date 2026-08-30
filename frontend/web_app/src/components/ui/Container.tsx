"use client";
import { cn } from "@/lib/utils";
type ContainerWidth = "wide" | "default" | "narrow" | "full";
interface ContainerProps {
  children: React.ReactNode; width?: ContainerWidth; className?: string;
  as?: "div" | "section" | "main";
}
const widthClasses: Record<ContainerWidth, string> = {
  wide: "max-w-[1400px]", default: "max-w-[1200px]", narrow: "max-w-[880px]", full: "max-w-none",
};
export function Container({ children, width = "default", className, as = "div" }: ContainerProps) {
  const Component = as;
  return <Component className={cn("mx-auto w-full px-4 sm:px-6 lg:px-8", widthClasses[width], className)}>{children}</Component>;
}
