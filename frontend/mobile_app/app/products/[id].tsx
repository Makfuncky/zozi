import { Redirect, useLocalSearchParams } from "expo-router";

/**
 * The canonical product detail screen lives at `app/(tabs)/products/[id].tsx`.
 * This route is kept as a thin redirect so legacy deep links / cards that push
 * to `/products/[id]` land on the same screen instead of a divergent copy
 * (which previously caused double-header / style drift issues).
 */
export default function ProductDetailRedirect() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Redirect href={`/(tabs)/products/${id}` as any} />;
}
