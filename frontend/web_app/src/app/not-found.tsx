"use client";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Home, Search, ArrowLeft } from "lucide-react";

export default function NotFound() {
  const router = useRouter();

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-surface-base px-4 overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-accent/10 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 max-w-lg w-full text-center"
      >
        <div className="theme-card rounded-2xl border p-8 sm:p-10">
          {/* 404 visual */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="mb-6"
          >
            <span className="text-7xl sm:text-8xl font-bold text-primary/20 select-none">404</span>
          </motion.div>

          <h1 className="text-xl sm:text-2xl font-bold text-text mb-2">Page Not Found</h1>
          <p className="text-sm text-text-muted mb-8">
            The page you are looking for does not exist, has been moved, or is temporarily unavailable.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => router.back()}
              className="theme-btn-secondary rounded-xl px-5 py-2.5 text-xs font-semibold flex items-center gap-2 w-full sm:w-auto justify-center"
            >
              <ArrowLeft className="h-4 w-4" />
              Go Back
            </button>
            <button
              onClick={() => router.push("/products")}
              className="theme-btn-primary rounded-xl px-5 py-2.5 text-xs font-semibold flex items-center gap-2 w-full sm:w-auto justify-center"
            >
              <Home className="h-4 w-4" />
              Browse Products
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-border">
            <p className="text-[11px] text-text-faint mb-3">Popular destinations</p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {[
                { label: "Products", href: "/products" },
                { label: "Cart", href: "/cart" },
                { label: "Orders", href: "/orders" },
                { label: "Help", href: "/help" },
                { label: "Admin", href: "/admin/dashboard" },
              ].map((item) => (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className="text-[11px] px-3 py-1.5 rounded-lg border border-border text-text-muted hover:text-primary hover:border-primary/40 transition-colors"
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}


