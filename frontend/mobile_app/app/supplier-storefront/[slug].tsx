/**
 * Supplier Storefront — public shop page for a specific supplier.
 * Redirects to the supplier profile/shop page which already exists at /suppliers/[id].
 * Web app uses the same re-export pattern.
 */
import { useEffect } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";

export default function SupplierStorefrontRedirect() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const router = useRouter();
  useEffect(() => {
    if (slug) {
      router.replace(`/suppliers/${slug}`);
    }
  }, [slug, router]);
  return null;
}
