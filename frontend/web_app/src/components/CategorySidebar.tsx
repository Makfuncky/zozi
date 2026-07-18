"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Smartphone, Shirt, Home, Sparkles, Trophy,
  Watch, Baby, Car, Heart, ChevronRight
} from "lucide-react";

const CATEGORIES = [
  { label: "Electronics",   icon: Smartphone, href: "/products?cat=electronics", color: "text-info" },
  { label: "Fashion",       icon: Shirt,       href: "/products?cat=fashion",     color: "text-pink-400" },
  { label: "Home & Garden", icon: Home,         href: "/products?cat=home",        color: "text-success" },
  { label: "Beauty",        icon: Sparkles,     href: "/products?cat=beauty",      color: "text-amber-400" },
  { label: "Sports",        icon: Trophy,       href: "/products?cat=sports",      color: "text-orange-400" },
  { label: "Accessories",   icon: Watch,        href: "/products?cat=accessories", color: "text-purple-400" },
  { label: "Mother & Kids", icon: Baby,          href: "/products?cat=kids",        color: "text-rose-400" },
  { label: "Automotive",    icon: Car,           href: "/products?cat=automotive",  color: "text-sky-400" },
  { label: "Health",        icon: Heart,         href: "/products?cat=health",      color: "text-danger" },
];

export default function CategorySidebar() {
  return (
    <div className="hidden lg:block w-56 rounded-2xl overflow-hidden shadow-card shrink-0 bg-slate-800 border border-slate-700">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Marketplace</span>
        <h3 className="text-sm font-semibold text-white mt-0.5">Categories</h3>
      </div>

      {/* Nav */}
      <nav className="p-1.5">
        {CATEGORIES.map((cat, i) => (
          <motion.div key={cat.label}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03, duration: 0.25 }}
          >
            <Link
              href={cat.href}
              className="flex items-center justify-between px-3 py-2 rounded-xl group transition-all hover:bg-slate-700/50"
            >
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-slate-700/50 group-hover:bg-primary/10 transition-colors">
                  <cat.icon className={`w-3.5 h-3.5 ${cat.color}`} />
                </div>
                <span className="text-[13px] font-medium text-slate-300 group-hover:text-white transition-colors">{cat.label}</span>
              </div>
              <ChevronRight className="w-3 h-3 text-slate-600 opacity-0 group-hover:opacity-100 group-hover:text-primary transition-all" />
            </Link>
          </motion.div>
        ))}
      </nav>

      {/* Footer CTA */}
      <div className="p-3 m-1.5 rounded-xl bg-primary/5 border border-primary/15">
        <p className="text-xs text-slate-500 mb-1.5">Browse all products</p>
        <Link href="/products"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary-light transition-colors">
          View All <ChevronRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}


