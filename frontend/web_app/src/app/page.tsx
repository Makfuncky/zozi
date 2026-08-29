import HomeClient from "./HomeClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function getHomeData() {
  try {
    const [productsRes, categoriesRes] = await Promise.all([
      fetch(`${API_URL}/api/v1/customer/catalog/products?page_size=12&sort=bestseller`, {
        next: { revalidate: 60 },
      }).catch(() => null),
      fetch(`${API_URL}/api/v1/customer/catalog/categories?page_size=50`, {
        next: { revalidate: 300 },
      }).catch(() => null),
    ]);

    const productsData = productsRes?.ok ? await productsRes.json().catch(() => null) : null;
    const categoriesData = categoriesRes?.ok ? await categoriesRes.json().catch(() => null) : null;

    // Normalize products: API returns { items: [...] }, HomeClient expects Product[]
    const rawProducts = productsData?.items ?? [];
    const products = rawProducts.map((p: any) => ({
      id: p.id,
      name: p.name,
      price: p.price,
      compare_price: p.compare_price,
      image_url: p.image_url ?? p.images?.[0]?.url,
      rating: p.rating ?? p.avg_rating,
      stock_quantity: p.stock_quantity ?? p.stock,
      category: p.category?.name ?? p.category_name,
      slug: p.slug,
      offer_discount_pct: p.offer_discount_pct ?? p.discount_percent,
      offer_type: p.offer_type,
      offer_ends_at: p.offer_ends_at,
      return_window_days: p.return_window_days,
      ai_description: p.ai_description,
      materials: p.materials,
      supplier: p.supplier,
      variants: p.variants,
      description: p.description,
      product_code: p.product_code ?? p.sku,
      barcode: p.barcode,
    }));

    // Normalize categories: API returns { items: [...] }
    const categories = (categoriesData?.items ?? []).map((c: any) => ({
      id: c.id,
      name: c.name,
      slug: c.slug,
      icon: c.icon,
      parent_id: c.parent_id,
    }));

    const trending = products.slice(0, 8);

    return { products, categories, trending };
  } catch {
    return { products: [], categories: [], trending: [] };
  }
}

export default async function HomePage() {
  const { products, categories, trending } = await getHomeData();
  return <HomeClient products={products} categories={categories} trending={trending} />;
}
