"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Search, MapPin, Star, Package, Verified, ChevronRight } from "lucide-react";
import { apiFetch } from "@/lib/api";
import Breadcrumbs from "@/components/Breadcrumbs";

interface Supplier {
  id: number;
  name: string;
  slug: string;
  logo_url?: string;
  rating?: number;
  total_products?: number;
  country?: string;
  verified?: boolean;
  description?: string;
}

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiFetch("/api/v1/customer/suppliers?limit=50")
      .then((res) => (res.ok ? res.json() : { items: [] }))
      .then((data) => {
        setSuppliers(data?.items ?? data?.data ?? []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const filtered = suppliers.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <Breadcrumbs items={[{ label: "Suppliers" }]} className="mb-6" />

        <div className="text-center mb-10">
          <h1 className="text-4xl font-display font-bold text-text-primary mb-3">
            Our Suppliers
          </h1>
          <p className="text-text-secondary max-w-2xl mx-auto">
            Discover verified suppliers offering quality products with fast delivery and competitive prices.
          </p>
        </div>

        {/* Search */}
        <div className="max-w-xl mx-auto mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-faint w-5 h-5" />
            <input
              type="text"
              placeholder="Search suppliers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-surface-1 border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-text-primary"
            />
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-40 rounded-xl bg-surface-1 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <Package className="w-16 h-16 text-text-faint mx-auto mb-4" />
            <p className="text-text-secondary">No suppliers found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((supplier, idx) => (
              <motion.div
                key={supplier.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Link
                  href={`/supplier-storefront/${supplier.slug}`}
                  className="block p-6 rounded-xl border border-border bg-surface-0 hover:border-primary/30 hover:shadow-lg transition-all group"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-xl bg-surface-2 flex items-center justify-center overflow-hidden shrink-0">
                      {supplier.logo_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={supplier.logo_url} alt={supplier.name} className="w-full h-full object-cover" />
                      ) : (
                        <Package className="w-7 h-7 text-text-faint" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-text-primary truncate group-hover:text-primary transition-colors">
                          {supplier.name}
                        </h3>
                        {supplier.verified && (
                          <Verified className="w-4 h-4 text-primary shrink-0" />
                        )}
                      </div>
                      {supplier.country && (
                        <div className="flex items-center gap-1 text-xs text-text-secondary mb-2">
                          <MapPin className="w-3 h-3" />
                          {supplier.country}
                        </div>
                      )}
                      <div className="flex items-center gap-3 text-xs text-text-faint">
                        {supplier.rating && (
                          <span className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-accent fill-current" />
                            {supplier.rating.toFixed(1)}
                          </span>
                        )}
                        {supplier.total_products && (
                          <span>{supplier.total_products} products</span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-text-faint group-hover:text-primary transition-colors shrink-0" />
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
