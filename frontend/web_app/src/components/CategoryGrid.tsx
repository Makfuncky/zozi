"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import React, { memo } from "react";

export interface Category {
  id: string;
  name: string;
  description?: string;
  image: string;
  spanClasses?: string;
  aspectRatio?: string;
}

interface CategoryGridProps {
  categories: Category[];
}

function CategoryGrid({ categories }: CategoryGridProps) {
  return (
    <div className="grid grid-cols-12 gap-6 items-start">
      {categories.map((cat, idx) => (
        <motion.div
          key={cat.id}
          className={
            `group cursor-pointer relative ${cat.spanClasses ?? "col-span-12 md:col-span-6"}`
          }
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.5 }}
        >
          <div
            className={
               `relative ${cat.aspectRatio ?? "aspect-[16/10]"} overflow-hidden rounded-3xl bg-surface-2`
            }
          >
            <Image
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-1000"
              src={cat.image}
              alt={cat.name}
              fill
              sizes="(max-width: 768px) 100vw, 50vw"
            />
            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/40 transition-colors" />
            <div className="absolute bottom-10 left-10">
              <h4 className="text-3xl font-bold text-white mb-2">
                {cat.name}
              </h4>
              {cat.description && (
                <p className="text-white/70 text-sm font-medium">
                  {cat.description}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export default memo(CategoryGrid);


