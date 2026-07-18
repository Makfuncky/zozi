/**
 * Supplier Upload — redirects to the existing bulk operations page.
 * Web app uses the same redirect pattern (supplier/upload → supplier/bulk).
 */
import { useEffect } from "react";
import { useRouter } from "expo-router";

export default function SupplierUploadRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/supplier/bulk");
  }, [router]);
  return null;
}
