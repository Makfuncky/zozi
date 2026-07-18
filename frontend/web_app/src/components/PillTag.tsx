"use client";

import React from "react";
import clsx from "clsx";

interface PillTagProps {
  children: React.ReactNode;
  className?: string;
}

export default function PillTag({ children, className = "" }: PillTagProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 px-4 py-1 rounded-full bg-white/10 text-white/80 text-[10px] font-bold uppercase tracking-[0.2em] mb-0.5 border border-white/5",
        className
      )}
    >
      {children}
    </span>
  );
}


