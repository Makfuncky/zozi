"use client";

import React from "react";
import { Sparkles, Zap, ShieldCheck, Globe, Tag, Truck } from "lucide-react";

const TICKER_ITEMS = [
  { text: "Free Global Shipping on orders over $500", icon: Globe, color: "text-info" },
  { text: "Join the Supplier Alliance \u2014 Register Now", icon: Zap, color: "text-accent" },
  { text: "100% Authenticity Guaranteed", icon: ShieldCheck, color: "text-success" },
  { text: "New Curated Drops Every Monday 10 AM", icon: Sparkles, color: "text-purple-400" },
  { text: "Flash Sale \u2014 Up to 70% Off Today Only", icon: Tag, color: "text-accent-light" },
  { text: "Express Delivery Available Nationwide", icon: Truck, color: "text-amber-400" },
];

export default function TickerBar() {
  return (
    <div className="w-full overflow-hidden relative z-40 py-2 bg-slate-800/50 border-b border-slate-700/50">
      {/* Edge fades */}
      <div className="absolute left-0 top-0 bottom-0 w-16 z-10 pointer-events-none bg-gradient-to-r from-slate-900 to-transparent" />
      <div className="absolute right-0 top-0 bottom-0 w-16 z-10 pointer-events-none bg-gradient-to-l from-slate-900 to-transparent" />

      <div className="flex whitespace-nowrap animate-marquee">
        {[...Array(4)].map((_, rep) => (
          <div key={rep} className="flex items-center shrink-0">
            {TICKER_ITEMS.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 px-6">
                <item.icon className={`w-3 h-3 shrink-0 ${item.color}`} />
                <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  {item.text}
                </span>
                <span className="ml-4 text-slate-600">&bull;</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      <style jsx>{`
        .animate-marquee {
          animation: marquee 50s linear infinite;
        }
        @keyframes marquee {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}


