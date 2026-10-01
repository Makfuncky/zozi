"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Package, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { Product } from "@/lib/types";
import ProductCard from "@/components/ProductCard";
import Breadcrumbs from "@/components/Breadcrumbs";

const CATEGORIES = [
  { slug: "electronics", name: "Electronics", icon: "🎧" },
  { slug: "fashion", name: "Fashion", icon: "👗" },
  { slug: "furniture", name: "Furniture", icon: "🛋️" },
  { slug: "accessories", name: "Accessories", icon: "⌚" },
  { slug: "home", name: "Home & Living", icon: "🏠" },
  { slug: "sports", name: "Sports", icon: "⚽" },
  { slug: "beauty", name: "Beauty", icon: "💄" },
  { slug: "books", name: "Books", icon: "📚" },
];

function CategoryPageContent() {
  const searchParams = useSearchParams();
  const categorySlug = searchParams.get("category");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const category = CATEGORIES.find((c) => c.slug === categorySlug);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    params.set("page_size", "48");
    if (categorySlug) params.set("category", categorySlug);

    apiFetch(`/api/v1/customer/catalog/products?${params.toString()}`)
      .then((res) => (res.ok ? res.json() : { items: [] }))
      .then((data) => {
        const items = data?.items ?? [];
        setProducts(items);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [categorySlug]);

  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <Breadcrumbs
          items={[
            { label: "Products", href: "/products" },
            ...(category ? [{ label: category.name }] : []),
          ]}
          className="mb-6"
        />

        <div className="text-center mb-10">
          <h1 className="text-4xl font-display font-bold text-text-primary mb-3">
            {category ? category.name : "All Products"}
          </h1>
          <p className="text-text-secondary">
            {category
              ? `Browse our ${category.name.toLowerCase()} collection`
              : "Discover amazing products from verified suppliers"}
          </p>
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          <a
            href="/products"
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              !categorySlug
                ? "bg-primary text-white"
                : "bg-surface-1 text-text-secondary hover:bg-surface-2"
            }`}
          >
            All
          </a>
          {CATEGORIES.map((cat) => (
            <a
              key={cat.slug}
              href={`/products?category=${cat.slug}`}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-1.5 ${
                categorySlug === cat.slug
                  ? "bg-primary text-white"
                  : "bg-surface-1 text-text-secondary hover:bg-surface-2"
              }`}
            >
              <span>{cat.icon}</span>
              {cat.name}
            </a>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20">
            <Package className="w-16 h-16 text-text-faint mx-auto mb-4" />
            <p className="text-text-secondary text-lg">No products found in this category.</p>
            <a href="/products" className="inline-block mt-4 text-primary hover:underline">
              Browse all products
            </a>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3"
          >
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function ProductsCategoryPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-surface-0 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    }>
      <CategoryPageContent />
    </Suspense>
  );
}
