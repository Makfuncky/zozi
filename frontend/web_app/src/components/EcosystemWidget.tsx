"use client";

import React from "react";
import { Store, ShieldCheck, ArrowRight, ShoppingBag } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

const roles = [
  {
    title: "For Customers",
    desc: "Discover premium curated products from global vendors with white-glove delivery and authenticity guarantee.",
    icon: ShoppingBag,
    color: "text-info",
    bg: "bg-info/10",
    border: "border-info/20",
    hoverBorder: "hover:border-info/40",
    links: [
      { label: "Browse Products", href: "/products" },
      { label: "Track Orders", href: "/orders" },
    ],
  },
  {
    title: "For Suppliers",
    desc: "Scale your boutique or enterprise brand globally with our unified vendor portal and analytics suite.",
    icon: Store,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    hoverBorder: "hover:border-purple-500/40",
    links: [
      { label: "Supplier Dashboard", href: "/supplier/dashboard" },
      { label: "Register as Vendor", href: "/supplier/register" },
    ],
  },
  {
    title: "For Administrators",
    desc: "Complete control over marketplace inventory, users, and platform economics with real-time insights.",
    icon: ShieldCheck,
    color: "text-orange-400",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
    hoverBorder: "hover:border-orange-500/40",
    links: [
      { label: "Admin Login", href: "/admin/login" },
      { label: "System Health", href: "/admin/dashboard" },
    ],
  },
];

export default function EcosystemWidget() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {roles.map((role, i) => (
        <motion.div
          key={role.title}
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.1, duration: 0.5 }}
          whileHover={{ y: -6 }}
          className={`relative overflow-hidden rounded-3xl p-7 group bg-slate-800 border ${role.border} ${role.hoverBorder} transition-colors`}
        >
          {/* Icon + title */}
          <div className="flex items-center gap-4 mb-5">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${role.bg} border ${role.border}`}>
              <role.icon className={`w-6 h-6 ${role.color}`} />
            </div>
            <div>
              <p className={`text-[10px] font-bold uppercase tracking-widest mb-0.5 ${role.color}`}>Role</p>
              <h3 className="text-lg font-bold text-white tracking-tight">{role.title}</h3>
            </div>
          </div>

          <p className="text-sm leading-relaxed mb-6 text-slate-400">
            {role.desc}
          </p>

          <div className="space-y-2.5">
            {role.links.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="flex items-center justify-between px-4 py-3 rounded-xl font-semibold text-xs text-slate-400 hover:text-white group/link transition-all bg-slate-700/30 border border-slate-700/50 hover:border-slate-600"
              >
                {link.label}
                <ArrowRight className={`w-3.5 h-3.5 ${role.color} opacity-40 group-hover/link:opacity-100 group-hover/link:translate-x-0.5 transition-all`} />
              </Link>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}


