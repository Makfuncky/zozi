"use client";

import CategoryGrid, { Category } from "./CategoryGrid";

// keep backward compatibility by exporting a small wrapper
const categories: Category[] = [
  {
    id: "fashion",
    name: "Fashion",
    description: "Designer clothing & accessories",
    image:
      "https://via.placeholder.com/800x600?text=Fashion",
  },
  {
    id: "home",
    name: "Home & Living",
    description: "Elegant decor & furnishings",
    image:
      "https://via.placeholder.com/800x600?text=Home",
  },
  {
    id: "electronics",
    name: "Electronics",
    description: "Premium gadgets & devices",
    image:
      "https://via.placeholder.com/800x600?text=Electronics",
  },
  {
    id: "watches",
    name: "Watches",
    description: "Luxury timepieces",
    image:
      "https://via.placeholder.com/800x600?text=Watches",
  },
];

export default function DirectorySection() {
  return (
    <section className="py-32 bg-surface-0 overflow-hidden">
      <div className="container mx-auto px-4">
        <CategoryGrid categories={categories} />
      </div>
    </section>
  );
}


