"use client";

import React from "react";
import { View, StyleSheet } from "react-native";
import ProductCard from "./ProductCard.native";
import { Product } from "../../types";

interface ProductGridProps {
  products: Product[];
}

export default function ProductGrid({
  products,
}: ProductGridProps) {
  if (products.length === 0) return null;

  return (
    <View style={styles.grid}>
      {products.map((p, index) => (
        <ProductCard
          key={p.id}
          product={p}
          variant={index === 0 ? "featured" : "default"}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
});