"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Laptop, Home, Shirt, Sparkles, Watch, Heart, Dumbbell, Coffee, ChevronRight } from "lucide-react";
import { Carousel } from "@/components/Carousel";

const categories = [
  { name: "Electronics",   icon: Laptop,   color: "text-info",    bg: "bg-info/10",    border: "border-info/20"  },
  { name: "Home & Garden", icon: Home,      color: "text-success", bg: "bg-success/10", border: "border-success/20" },
  { name: "Fashion",       icon: Shirt,     color: "text-pink-400",    bg: "bg-pink-500/10",    border: "border-pink-500/20"  },
  { name: "Accessories",   icon: Watch,     color: "text-purple-400",  bg: "bg-purple-500/10",  border: "border-purple-500/20" },
  { name: "Beauty",        icon: Sparkles,  color: "text-amber-400",   bg: "bg-amber-500/10",   border: "border-amber-500/20" },
  { name: "Health",        icon: Heart,     color: "text-danger",     bg: "bg-danger/10",     border: "border-danger/20"   },
  { name: "Sports",        icon: Dumbbell,  color: "text-orange-400",  bg: "bg-orange-500/10",  border: "border-orange-500/20" },
  { name: "Kitchen",       icon: Coffee,    color: "text-teal-400",    bg: "bg-teal-500/10",    border: "border-teal-500/20"  },
];

export default function TopCategoriesWidget() {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-2.5">
          <div className="w-1 h-5 rounded-full bg-gradient-to-b from-primary to-accent" />
          <h3 className="text-sm font-bold uppercase tracking-widest text-text">Top Categories</h3>
        </div>
        <Link
          href="/products"
          className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-primary-light hover:text-text transition-colors"
        >
          See All <ChevronRight className="w-3 h-3" />
        </Link>
      </div>

      <Carousel ariaLabel="Top categories" itemClassName="snap-start">
        {categories.map((c, i) => (
          <motion.div key={c.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.35 }}
          >
            <Link
              href={`/products?category=${c.name.toLowerCase()}`}
              className="flex flex-col items-center gap-2.5 min-w-[76px] group"
            >
              <div className={`w-[60px] h-[60px] rounded-2xl flex items-center justify-center ${c.bg} border ${c.border} transition-all duration-300 group-hover:scale-110 group-hover:-translate-y-1`}>
                <c.icon className={`w-6 h-6 ${c.color}`} />
              </div>
              <span className="text-[11px] font-medium text-text-muted group-hover:text-text transition-colors text-center leading-tight whitespace-nowrap">
                {c.name}
              </span>
            </Link>
          </motion.div>
        ))}
      </Carousel>
    </div>
  );
}


