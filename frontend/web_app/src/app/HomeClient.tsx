"use client";

import { Button } from "@/components/ui/Button";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight, Zap, Star, ShoppingBag, TrendingUp, Sparkles,
  Package2, Headphones, Shirt, Sofa, Lamp, Watch, Baby, BookOpen,
} from "lucide-react";
import { Product } from "@/lib/types";
import LimitedTimeOffer from "@/components/LimitedTimeOffer";
import BannerCarousel from "@/components/BannerCarousel";
import HomeProductShowcase from "@/components/HomeProductShowcase";
import RecentlyViewed from "@/components/RecentlyViewed";
import Footer from "@/components/Footer";
import ProductCard from "@/components/ProductCard";

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  electronics: Headphones,
  fashion: Shirt,
  furniture: Sofa,
  accessories: Watch,
  home: Lamp,
  baby: Baby,
  books: BookOpen,
  sports: TrendingUp,
};

const CATEGORY_COLORS: Record<string, string> = {
  electronics: "from-info to-cyan-600",
  fashion: "from-pink-500 to-rose-600",
  furniture: "from-success to-primary",
  accessories: "from-amber-500 to-orange-600",
  home: "from-sky-500 to-info",
  baby: "from-pink-400 to-fuchsia-500",
  books: "from-warning to-amber-600",
  sports: "from-success to-primary",
  beauty: "from-accent to-primary",
  automotive: "from-slate-500 to-slate-700",
};

interface Props {
  products: Product[];
  categories: { id: number; name: string; slug: string; icon?: string }[];
  trending: Product[];
}

export default function HomeClient({ products, categories, trending }: Props) {
  const [heroEmail, setHeroEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (heroEmail.trim()) {
      setSubscribed(true);
      setHeroEmail("");
    }
  };

  const displayCategories = categories.length > 0
    ? categories.slice(0, 8)
    : [
        { id: 1, name: "Electronics", slug: "electronics" },
        { id: 2, name: "Fashion", slug: "fashion" },
        { id: 3, name: "Furniture", slug: "furniture" },
        { id: 4, name: "Accessories", slug: "accessories" },
        { id: 5, name: "Home & Living", slug: "home" },
        { id: 6, name: "Sports", slug: "sports" },
        { id: 7, name: "Beauty", slug: "beauty" },
        { id: 8, name: "Books", slug: "books" },
      ];

  return (
    <div className="min-h-screen bg-background">
      {/* Limited-time offer banner */}
      <LimitedTimeOffer />

      <main className="max-w-11xl mx-auto px-4 sm:px-6 pb-20">
        {/* ── Hero section ─────────────────────────────────────────────── */}
        <section className="py-12 md:py-16 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.3em] text-primary bg-primary/10 border border-primary/20 px-3 py-1 rounded-full mb-4">
              <Sparkles className="w-3 h-3" />
              GCC&apos;s Premier Marketplace
            </span>

            <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold text-text tracking-tight leading-[0.92] mb-5">
              THE{" "}
              <span className="italic font-heading theme-hero-gradient">MARKETPLACE.</span>
            </h1>

            <p className="text-sm md:text-base text-text-muted max-w-xl mx-auto mb-8 leading-relaxed">
              Extraordinary products from verified suppliers — delivered across the Gulf.
              Same-day dispatch from UAE, Saudi Arabia & Kuwait.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center items-center mb-4">
              <Link
                href="/products"
                className="px-6 py-3 bg-primary text-on-brand text-sm font-bold rounded-2xl hover:bg-primary-dark transition-all flex items-center gap-2 shadow-lg shadow-primary/25"
              >
                <ShoppingBag className="w-4 h-4" />
                Shop All Products
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/offers"
                className="px-6 py-3 border border-border-light text-text-muted text-sm font-bold rounded-2xl hover:border-primary hover:text-primary transition-all flex items-center gap-2"
              >
                <Zap className="w-4 h-4" />
                Flash Deals
              </Link>
            </div>

            <p className="text-[10px] text-text-faint uppercase tracking-widest">
              {products.length > 0 ? products.length.toLocaleString() : "8,000+"}+ curated products &middot; Free returns &middot; Secure checkout
            </p>
          </motion.div>
        </section>

        {/* ── Promotional banner (driven by admin banners + background effects) ── */}
        <div className="mb-10">
          <BannerCarousel position="hero" />
        </div>

        {/* ── Category grid ─────────────────────────────────────────────── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-text">Shop by Category</h2>
              <p className="text-xs text-text-faint mt-0.5">Browse our full collection</p>
            </div>
            <Link
              href="/products"
                className="text-xs text-primary hover:text-primary-light flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {displayCategories.map((cat, i) => {
              const Icon = CATEGORY_ICONS[cat.slug] || Package2;
              const gradient = CATEGORY_COLORS[cat.slug] || "from-primary to-accent";
              return (
                <motion.div
                  key={cat.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Link
                    href={`/products?category=${cat.slug}`}
                    className="flex flex-col items-center gap-2 p-4 rounded-2xl border border-border-light bg-surface hover:border-primary/50 hover:bg-surface-2 transition-all group"
                  >
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-[10px] font-semibold text-text-muted group-hover:text-text transition-colors text-center leading-tight">
                      {cat.name}
                    </span>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* ── Trending now ─────────────────────────────────────────────── */}
        {trending.length > 0 && (
          <section className="mb-12">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <div>
                  <h2 className="text-xl font-bold text-text">Trending Now</h2>
                  <p className="text-xs text-text-faint mt-0.5">Top-rated this week</p>
                </div>
              </div>
              <Link
                href="/products?sort=rating"
              className="text-xs text-primary hover:text-primary-light flex items-center gap-1 transition-colors"
              >
                See all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {trending.slice(0, 4).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </section>
        )}

        {/* ── Value props ────────────────────────────────────────────── */}
        <section className="mb-12 grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: Zap, title: "Same-day dispatch", desc: "Orders before 2PM ship today" },
            { icon: Star, title: "Verified suppliers", desc: "Every supplier is vetted" },
            { icon: ShoppingBag, title: "Free returns", desc: "30-day hassle-free returns" },
            { icon: Sparkles, title: "Authentic products", desc: "100% genuine guarantee" },
          ].map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="flex flex-col gap-2 p-4 rounded-2xl border border-border-light bg-surface"
            >
              <Icon className="w-5 h-5 text-primary" />
              <p className="text-xs font-bold text-text">{title}</p>
              <p className="text-[11px] text-text-faint">{desc}</p>
            </div>
          ))}
        </section>

        {/* ── Full product showcase ─────────────────────────────────── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-text">New Arrivals</h2>
              <p className="text-xs text-text-faint mt-0.5">Latest additions to the marketplace</p>
            </div>
          </div>
          <HomeProductShowcase products={products} />
        </section>

        {/* ── Recently viewed ───────────────────────────────────────── */}
        <RecentlyViewed />

        {/* ── Become a supplier CTA ─────────────────────────────────── */}
        <section className="mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary via-primary-dark to-accent p-8 md:p-12 text-center"
          >
            <div className="absolute -top-12 -right-12 w-40 h-40 rounded-full bg-white/5 blur-2xl" />
            <div className="absolute -bottom-12 -left-12 w-40 h-40 rounded-full bg-accent/20 blur-2xl" />
            <div className="relative">
                <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-accent bg-white/10 px-3 py-1 rounded-full mb-4">
                <Sparkles className="w-3 h-3" />
                Become a Supplier
              </span>
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
                Sell on ZOZI Marketplace
              </h2>
              <p className="text-sm text-indigo-200 mb-6 max-w-lg mx-auto">
                Join thousands of verified suppliers. Zero listing fees. Fast payouts. Full analytics dashboard.
              </p>
              <Link
                href="/supplier/register"
                className="inline-flex items-center gap-2 px-6 py-3 bg-surface-1 text-text text-sm font-bold rounded-2xl hover:bg-surface-2 transition-colors shadow-lg"
              >
                Get Started Free <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </section>

        {/* ── Newsletter ───────────────────────────────────────────────── */}
        <section className="mb-4">
          <div className="rounded-2xl border border-border-light bg-surface p-8 text-center">
            <h3 className="text-lg font-bold text-text mb-2">Stay in the loop</h3>
            <p className="text-xs text-text-muted mb-4">
              Get notified about flash deals, new arrivals, and exclusive offers.
            </p>
            {subscribed ? (
              <p className="text-success text-sm font-semibold">✓ You&apos;re subscribed!</p>
            ) : (
              <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-2 max-w-sm mx-auto">
                <input
                  type="email"
                  value={heroEmail}
                  onChange={(e) => setHeroEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  className="flex-1 px-4 py-2.5 rounded-xl text-sm bg-surface-2 border border-border-light text-text placeholder:text-text-faint focus:outline-none focus:border-primary"
                />
                <Button variant="primary" type="submit">
                  Subscribe
                </Button>
              </form>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}


