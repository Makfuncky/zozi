import React from "react";
import { View, StyleSheet } from "react-native";
import type { Product } from "@shared/types";
import { ProductCard } from "./ProductCard";

interface ProductGridProps {
	products: Product[];
}

export default function ProductGrid({ products }: ProductGridProps) {
	if (products.length === 0) return null;

	return (
		<View style={styles.grid}>
			{products.map((product, index) => (
				<ProductCard
					key={product.id}
					product={product}
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
