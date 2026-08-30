"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface AccordionContextValue {
  openItems: Set<string>;
  toggle: (id: string) => void;
}

const AccordionContext = createContext<AccordionContextValue | null>(null);

interface AccordionProps {
  children: ReactNode;
  allowMultiple?: boolean;
  className?: string;
}

export function Accordion({ children, allowMultiple = false, className }: AccordionProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); } else {
        if (!allowMultiple) next.clear();
        next.add(id);
      }
      return next;
    });
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggle }}>
      <div className={cn("divide-y divide-glass-border-mid", className)}>{children}</div>
    </AccordionContext.Provider>
  );
}

interface AccordionItemProps {
  id: string; title: string; children: ReactNode; className?: string;
}

export function AccordionItem({ id, title, children, className }: AccordionItemProps) {
  const ctx = useContext(AccordionContext);
  if (!ctx) throw new Error("AccordionItem must be used within Accordion");
  const isOpen = ctx.openItems.has(id);

  return (
    <div className={cn("py-2", className)}>
      <button className="flex items-center justify-between w-full py-2 text-left text-sm font-medium text-text hover:text-brand transition-colors" onClick={() => ctx.toggle(id)} aria-expanded={isOpen}>
        <span>{title}</span>
        <span className={cn("text-text-muted transition-transform", isOpen && "rotate-180")}>▾</span>
      </button>
      <div className={cn("overflow-hidden transition-all", isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0")}>
        <div className="py-2 text-sm text-text-muted">{children}</div>
      </div>
    </div>
  );
}
