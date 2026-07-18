"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  TrendingUp,
  BarChart3,
  Shield,
  Truck,
  ArrowRight,
  Sparkles,
  Users,
  DollarSign,
} from "@/lib/icons";

const BENEFITS = [
  {
    icon: TrendingUp,
    title: "Grow Revenue",
    desc: "Reach thousands of buyers on ZOZI with built-in marketing tools.",
  },
  {
    icon: BarChart3,
    title: "Real-time Analytics",
    desc: "Track sales, inventory, and customer trends with our powerful dashboard.",
  },
  {
    icon: Shield,
    title: "Secure Payments",
    desc: "Get paid reliably with automated payouts and transparent fee structures.",
  },
  {
    icon: Truck,
    title: "Fulfillment Support",
    desc: "Integrated shipping management with discounted carrier rates.",
  },
  {
    icon: Users,
    title: "Dedicated Support",
    desc: "Our supplier success team is available 24/7 to help you succeed.",
  },
  {
    icon: DollarSign,
    title: "Low Fees",
    desc: "Competitive commission rates that scale with your business growth.",
  },
];

const STATS = [
  { value: "500+", label: "Active Suppliers" },
  { value: "$2M+", label: "Monthly GMV" },
  { value: "50K+", label: "Monthly Buyers" },
  { value: "4.8?", label: "Supplier Rating" },
];

export default function SupplierLandingPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="relative py-24 px-4 overflow-hidden">
        <div className="absolute inset-0 theme-bg-brand-to-warning-soft-br" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-3xl mx-auto text-center relative z-10"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-2 border border-border text-xs font-semibold text-primary mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            SUPPLIER PROGRAM
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-text mb-4">
            Sell on{" "}
            <span className="theme-gradient-brand-text">
              ZOZI
            </span>
          </h1>
          <p className="text-text-muted max-w-lg mx-auto mb-8">
            Join hundreds of suppliers already growing their business with
            ZOZI. List products, manage orders, and scale effortlessly.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/supplier/register"
              className="px-8 py-3.5 rounded-xl theme-btn-primary text-sm font-bold flex items-center gap-2"
            >
              Get Started
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/supplier/login"
              className="px-8 py-3.5 rounded-xl border border-border text-text text-sm font-semibold hover:border-border-light hover:bg-surface-2 transition-colors"
            >
              Supplier Login
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="max-w-300 mx-auto px-4 sm:px-6 mb-16">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {STATS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="p-5 rounded-2xl theme-card border text-center"
            >
              <p className="text-2xl font-bold text-text">{s.value}</p>
              <p className="text-xs text-text-faint mt-1">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Benefits */}
      <section className="max-w-300 mx-auto px-4 sm:px-6 mb-16">
        <h2 className="text-2xl font-bold text-text text-center mb-8">
          Why Suppliers Love ZOZI
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {BENEFITS.map((b, i) => (
            <motion.div
              key={b.title}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              className="p-5 rounded-2xl theme-card border"
            >
              <b.icon className="w-8 h-8 text-primary mb-3" />
              <h3 className="text-sm font-bold text-text mb-1">{b.title}</h3>
              <p className="text-xs text-text-muted leading-relaxed">
                {b.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-200 mx-auto px-4 sm:px-6 mb-16">
          <div className="p-8 rounded-2xl theme-bg-brand-to-warning-soft border border-primary/20 text-center">
          <h3 className="text-xl font-bold text-text mb-2">
            Ready to Start Selling?
          </h3>
          <p className="text-sm text-text-muted mb-6">
            Create your supplier account in minutes. No setup fees.
          </p>
          <Link
            href="/supplier/register"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl theme-btn-primary text-sm font-bold"
          >
            Register Now
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

    </main>
  );
}


