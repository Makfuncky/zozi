"use client";

import type React from "react";
import type { Icon as LucideIcon } from "lucide-react";

interface StatItem {
  value: string;
  label: string;
  // use a generic component type to sidestep iconNode requirement
  icon?: React.ComponentType<any>;
}

interface StatsGridProps {
  items: StatItem[];
}

export default function StatsGrid({ items }: StatsGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 py-16">
      {items.map((stat, idx) => (
        <div key={idx} className="flex items-center gap-4">
          {stat.icon && (
            <stat.icon className="w-6 h-6 text-primary" aria-hidden />
          )}
          <div>
            <p className="text-2xl font-black leading-tight">{stat.value}</p>
            <p className="text-sm uppercase tracking-wide text-text-muted">
              {stat.label}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}


