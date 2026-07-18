"use client";

import { memo } from "react";
import ProductCard from "./ProductCard";
import { Product } from "@/lib/types";

interface ProductGridProps {
  products: Product[];
}

const ProductGrid = memo(function ProductGrid({
  products,
}: ProductGridProps) {
  if (products.length === 0) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      {products.map((p, index) => (
        <ProductCard key={p.id} product={p} variant={index === 0 ? "featured" : "default"} />
      ))}
    </div>
  );
});

export default ProductGrid;


