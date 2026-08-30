"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

interface TabsProps {
  children: ReactNode;
  defaultTab: string;
  className?: string;
}

export function Tabs({ children, defaultTab, className }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabList({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("flex border-b border-glass-border-mid", className)} role="tablist">{children}</div>;
}

export function Tab({ id, children, className }: { id: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("Tab must be used within Tabs");
  const isActive = ctx.activeTab === id;
  return (
    <button
      role="tab"
      aria-selected={isActive}
      className={cn("px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px", isActive ? "text-brand border-brand" : "text-text-muted border-transparent hover:text-text", className)}
      onClick={() => ctx.setActiveTab(id)}
    >
      {children}
    </button>
  );
}

export function TabPanel({ id, children, className }: { id: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("TabPanel must be used within Tabs");
  if (ctx.activeTab !== id) return null;
  return <div className={cn("py-4", className)} role="tabpanel">{children}</div>;
}
