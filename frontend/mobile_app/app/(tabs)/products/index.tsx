import React, { useState, useEffect, useCallback, useRef } from "react";
import ErrorBoundary from "@/components/ui/ErrorBoundary";
import { View, Text, FlatList, Modal, TouchableOpacity, TextInput, StyleSheet, RefreshControl, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { apiFetch, API_BASE } from "@/lib/api";
import { useCartStore } from "@/lib/cartStore";
import { useThemeStore } from "@/lib/themeStore";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useAuthStore } from "@/lib/authStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { resolveProductRouteFilters } from "@/lib/productRouteFilters";
import { makeStyles, AppTheme } from "@/theme";
import { ProductCard } from "@/components/ProductCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { GradientButton } from "@/components/ui/GradientButton";
import { HeaderBar } from "@/components/ui/HeaderBar";
import { Footer } from "@/components/ui/Footer";
import ProductSearchFilterBar from "@/components/ui/ProductSearchFilterBar";
import { Product } from "@shared/types";
import { buildProductQueryParams } from "@shared/productQuery";
import MobileSeasonalBanner from "@/components/MobileSeasonalBanner";
import { openLeftDrawer, openRightDrawer } from "@/lib/uiBus";

function renderStars(value: string, max = 5) {
  const parsed = Number(value);
  const filled = Number.isFinite(parsed) ? Math.max(0, Math.min(max, Math.round(parsed))) : 0;
  const empty = Math.max(0, max - filled);
  return `${"★".repeat(filled)}${"☆".repeat(empty)}`;
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  dropdownPill: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface1,
    minWidth: 90,
    alignItems: "center",
    justifyContent: "center",
  },
  searchEngineCard: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  filterStrip: {
    gap: 8,
    paddingRight: theme.spacing.sm,
  },
  searchControls: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  cameraButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface2,
    alignItems: "center",
    justifyContent: "center",
  },
  searchButton: {
    borderRadius: 12,
    overflow: "hidden",
  },
  searchButtonInner: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  searchButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 12,
  },
  quickPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface1,
  },
quickPillActive: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: theme.colors.pillActive,
      backgroundColor: theme.colors.pillActiveBg,
    },
  activeChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
  },
  clearAllBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    backgroundColor: theme.colors.dangerBg,
    borderColor: theme.colors.danger,
  },
  grid: {
    paddingHorizontal: 10,
    paddingBottom: theme.spacing.xl,
    gap: 10,
    paddingTop: 10,
  },
  row: {
    gap: 10,
  },
  cardWrapper: {
    flex: 1,
    alignItems: "stretch",
  },
  sectionGap: {
    marginBottom: theme.spacing.sm,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "flex-end",
  },
  modalCard: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    borderWidth: 1,
    maxHeight: "70%",
  },
  modalItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.06)",
  },
  priceInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
  },
  presetBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
  },
  modalActionBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
  },
  applyBtn: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    borderRadius: 12,
  },
  quickActionsRow: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 4,
  },
  quickActionChip: {
    flex: 1,
    alignItems: "center",
    gap: 4,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface1,
    minWidth: 0,
  },
  flashSaleCard: {
    width: 150,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface1,
    overflow: "hidden",
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 8,
  },
});

const CATEGORY_LABELS: Record<string, string> = {
  all: "All",
  electronics: "Electronics",
  fashion: "Fashion",
  accessories: "Accessories",
  furniture: "Furniture",
  beauty: "Beauty",
  sports: "Sports",
  home: "Home & Living",
  books: "Books",
  grocery: "Grocery",
  baby: "Baby & Kids",
  automotive: "Automotive",
  crafts: "Crafts",
};


export default function ProductsScreen() {
  return (
    <ErrorBoundary>
      <ProductsScreenInner />
    </ErrorBoundary>
  );
}

function ProductsScreenInner() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { width: screenWidth } = useWindowDimensions();
  const params = useLocalSearchParams();
  const routeFilters = resolveProductRouteFilters(params as Record<string, string | string[] | undefined>);
  const { isLoggedIn } = useAuthStore();
  const fetchWishlist = useWishlistStore((st) => st.fetch);
  const router = useRouter();
  const hasDiscoveryOverrides = Boolean(
    routeFilters.search ||
    routeFilters.supplier ||
    routeFilters.brand ||
    routeFilters.color ||
    routeFilters.trendingOnly ||
    routeFilters.newArrivals ||
    routeFilters.discountPct ||
    (routeFilters.category && routeFilters.category !== "all")
  );

  useEffect(() => {
    // The Products tab always renders the catalog; deep-link filters
    // merely pre-apply, they no longer force a redirect to Home.
  }, [hasDiscoveryOverrides]);

  // Core state
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState(routeFilters.search);
  const [category, setCategory] = useState(routeFilters.category);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Extended filter state (matching web)
  const [newArrivals, setNewArrivals] = useState(routeFilters.newArrivals);
  const [trendingOnly, setTrendingOnly] = useState(routeFilters.trendingOnly);
  const [discountPct, setDiscountPct] = useState(routeFilters.discountPct);
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [priceSort, setPriceSort] = useState<"" | "price:asc" | "price:desc">("");
  const [minRating, setMinRating] = useState("");
  const [supplier, setSupplier] = useState(routeFilters.supplier);
  const [brand, setBrand] = useState(routeFilters.brand);
  const [color, setColor] = useState(routeFilters.color);
  const [inStockOnly, setInStockOnly] = useState(false);

  // Result count
  const [totalCount, setTotalCount] = useState<number | null>(null);

  // Load More pagination
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const LIMIT = 40;

  // Modal visibility
  const [catModalOpen, setCatModalOpen] = useState(false);
  const [priceModalOpen, setPriceModalOpen] = useState(false);
  const [ratingModalOpen, setRatingModalOpen] = useState(false);
  const [discountModalOpen, setDiscountModalOpen] = useState(false);
  const [supplierModalOpen, setSupplierModalOpen] = useState(false);
  const [supplierInput, setSupplierInput] = useState("");
  const [brandModalOpen, setBrandModalOpen] = useState(false);
  const [brandInput, setBrandInput] = useState("");
  const [colorModalOpen, setColorModalOpen] = useState(false);

  // Back-to-top
  const flatListRef = useRef<FlatList>(null);
  const [showBackToTop, setShowBackToTop] = useState(false);

  // View mode: grid (3-col) or list
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Debounced search — auto-trigger 400ms after user stops typing
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  function handleSearchChange(v: string) {
    setSearch(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setOffset(0);
    }, 400);
  }

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  useEffect(() => {
    if (isLoggedIn) fetchWishlist();
  }, [isLoggedIn, fetchWishlist]);

  useEffect(() => {
    const next = resolveProductRouteFilters(params);
    setSearch(next.search);
    setCategory(next.category);
    setSupplier(next.supplier);
    setBrand(next.brand);
    setColor(next.color);
    setTrendingOnly(next.trendingOnly);
    setNewArrivals(next.newArrivals);
    setDiscountPct(next.discountPct);
    setOffset(0);
  }, [params]);

  const loadProducts = useCallback(async (reset = true) => {
    const currentOffset = reset ? 0 : offset;
    try {
      const qs = buildProductQueryParams({
        search: search.trim() || undefined,
        category: category !== "all" ? category : undefined,
        sort: priceSort || undefined,
        newArrivals: newArrivals || undefined,
        trending: trendingOnly || undefined,
        discountPct: discountPct || undefined,
        minPrice: minPrice || undefined,
        maxPrice: maxPrice || undefined,
        minRating: minRating || undefined,
        supplier: supplier.trim() || undefined,
        brand: brand.trim() || undefined,
        color: color || undefined,
        inStock: inStockOnly || undefined,
      });
      const data = await apiFetch<Product[] | { items: Product[]; total?: number }>(
        `/products?${qs}&limit=${LIMIT}&offset=${currentOffset}`,
        { skipAuth: true } as never
      );
      const items = Array.isArray(data) ? data : (data as any).items ?? [];
      const total: number | null = Array.isArray(data) ? null : ((data as any).total ?? null);
      setLoadError(null);
      if (reset) {
        setProducts(items);
        setOffset(items.length);
      } else {
        setProducts((prev) => [...prev, ...items]);
        setOffset(currentOffset + items.length);
      }
      setTotalCount(total ?? (reset ? items.length : null));
      setHasMore(items.length === LIMIT);
    } catch (error) {
      const message = error instanceof Error ? error.message : `Unable to reach backend at ${API_BASE}`;
      setLoadError(message);
      setHasMore(false);
      setTotalCount(0);
      if (reset) setProducts([]);
    }
  }, [search, category, priceSort, newArrivals, trendingOnly, discountPct, minPrice, maxPrice, minRating, supplier, brand, color, inStockOnly, offset, LIMIT]);

  useEffect(() => {
    setLoading(true);
    loadProducts(true).finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, category, priceSort, newArrivals, trendingOnly, discountPct, minPrice, maxPrice, minRating, supplier, brand, color, inStockOnly]);

  async function onRefresh() {
    setRefreshing(true);
    await loadProducts(true);
    setRefreshing(false);
  }

  function resetFilters() {
    setSearch(""); setCategory("all"); setLoadError(null);
    setNewArrivals(false); setTrendingOnly(false);
    setDiscountPct(""); setMinPrice(""); setMaxPrice(""); setPriceSort(""); setMinRating("");
    setSupplier(""); setSupplierInput("");
    setBrand(""); setBrandInput(""); setColor(""); setInStockOnly(false);
  }

  const currentCatLabel = CATEGORY_LABELS[category] ?? category;
  const currentCategoryButtonLabel = category === "all" ? "Categories" : currentCatLabel;

  const activeChips = React.useMemo(() => {
    const chips: { label: string; onRemove: () => void }[] = [];
    if (category !== "all") chips.push({ label: currentCatLabel, onRemove: () => setCategory("all") });
    if (priceSort) chips.push({ label: priceSort === "price:asc" ? "Price: Low→High" : "Price: High→Low", onRemove: () => setPriceSort("") });
    if (newArrivals) chips.push({ label: "✨ New Arrivals", onRemove: () => setNewArrivals(false) });
    if (trendingOnly) chips.push({ label: "📈 Trending", onRemove: () => setTrendingOnly(false) });
    if (discountPct) chips.push({ label: `🏷 ${discountPct}%+ Off`, onRemove: () => setDiscountPct("") });
    if (minPrice || maxPrice) chips.push({ label: `AED ${minPrice || "0"} – ${maxPrice || "∞"}`, onRemove: () => { setMinPrice(""); setMaxPrice(""); } });
    if (minRating) chips.push({ label: `${minRating}★+`, onRemove: () => setMinRating("") });
    if (supplier.trim()) chips.push({ label: `🏭 ${supplier}`, onRemove: () => { setSupplier(""); setSupplierInput(""); } });
    if (brand.trim()) chips.push({ label: `🏷 ${brand}`, onRemove: () => { setBrand(""); setBrandInput(""); } });
    if (color) chips.push({ label: `🎨 ${color}`, onRemove: () => setColor("") });
    if (inStockOnly) chips.push({ label: "✅ In Stock", onRemove: () => setInStockOnly(false) });
    return chips;
  }, [category, priceSort, newArrivals, trendingOnly, discountPct, minPrice, maxPrice, minRating, supplier, brand, color, inStockOnly]);

  const priceSummary =
    minPrice || maxPrice
      ? `AED ${minPrice || "0"} – ${maxPrice || "∞"}`
      : undefined;

  const activeFilterCount = activeChips.length;

  const renderProductItem = useCallback(
    ({ item }: { item: Product }) => (
      <View style={styles.cardWrapper}>
        <ProductCard product={item} />
      </View>
    ),
    []
  );

  return (
    <View testID="products-screen" style={[s.container, { flex: 1, backgroundColor: theme.colors.surface0 }]}> 
      {/* ─── Modern stacked header + search + banner ─── */}
      <View style={{ backgroundColor: 'transparent' }}>
        <HeaderBar
          onLeftPress={openLeftDrawer}
          onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
        />

        {/* Web-style Search + Filter bar (single row, top, centered) — pulled up fully into the lime header */}
        <View style={{ marginTop: -104 }}>
          <ProductSearchFilterBar
            search={search}
            onSetSearch={handleSearchChange}
            onCommitSearch={() => { setOffset(0); loadProducts(true); }}
            onImageSearch={() => router.push("/(tabs)/products" as never)}
            onNotificationsPress={() => router.push("/notifications" as never)}
            category={category}
            onCategoryPress={() => setCatModalOpen(true)}
            currentCategoryLabel={currentCategoryButtonLabel}
            priceActive={!!(minPrice || maxPrice || priceSort)}
            priceSummary={priceSummary}
            onPricePress={() => setPriceModalOpen(true)}
            ratingActive={!!minRating}
            minRating={minRating}
            onRatingPress={() => setRatingModalOpen(true)}
            supplierActive={!!supplier.trim()}
            onSupplierPress={() => { setSupplierInput(supplier); setSupplierModalOpen(true); }}
            newArrivals={newArrivals}
            trendingOnly={trendingOnly}
            onToggleNewArrivals={() => setNewArrivals((v) => !v)}
            onToggleTrending={() => setTrendingOnly((v) => !v)}
            discountPct={discountPct}
            onDiscountPress={() => setDiscountModalOpen(true)}
            activeFilterCount={activeFilterCount}
            onResetFilters={resetFilters}
          />
        </View>

      </View>

      {/* Active Filter Chips */}
      {activeChips.length > 0 && (
        <View style={{ marginTop: theme.spacing.sm, marginHorizontal: theme.spacing.md }}>
          <FlatList
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: 8, paddingRight: theme.spacing.sm }}
            data={activeChips}
            keyExtractor={(item) => item.label}
            renderItem={({ item }) => (
              <TouchableOpacity onPress={item.onRemove} style={[styles.activeChip, { backgroundColor: theme.colors.brand + "18", borderColor: theme.colors.brand + "55" }]}>
                <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>{item.label} ✕</Text>
              </TouchableOpacity>
            )}
            ListFooterComponent={
              <TouchableOpacity onPress={resetFilters} style={[styles.clearAllBtn, { borderColor: "rgba(239,68,68,0.5)", backgroundColor: "rgba(239,68,68,0.1)" }]}>
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.xs, fontWeight: "600" }}>Clear All ✕</Text>
              </TouchableOpacity>
            }
          />
        </View>
      )}

      {/* Category Modal */}
      <Modal visible={catModalOpen} transparent animationType="slide" onRequestClose={() => setCatModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setCatModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Categories</Text>
            <FlatList
              data={Object.keys(CATEGORY_LABELS)}
              keyExtractor={(c) => c}
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.modalItem} onPress={() => { setCategory(item); setCatModalOpen(false); }}>
                  <Text style={{ color: category === item ? theme.colors.brand : theme.colors.text, fontWeight: category === item ? "600" : "400" }}>
                    {CATEGORY_LABELS[item] ?? item}
                  </Text>
                  {category === item && <Text style={{ color: theme.colors.brand }}>✓</Text>}
                </TouchableOpacity>
              )}
            />
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Price Range Modal */}
      <Modal visible={priceModalOpen} transparent animationType="slide" onRequestClose={() => setPriceModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setPriceModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Price Range (AED)</Text>
            {/* Price sort direction */}
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, fontWeight: "600", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>Sort Direction</Text>
            {([{ value: "price:asc", label: "💰 Low → High" }, { value: "price:desc", label: "💰 High → Low" }] as const).map(({ value, label }) => (
              <TouchableOpacity
                key={value}
                style={styles.modalItem}
                onPress={() => setPriceSort(priceSort === value ? "" : value)}
              >
                <Text style={{ color: priceSort === value ? theme.colors.brand : theme.colors.text, fontWeight: priceSort === value ? "600" : "400" }}>
                  {label}
                </Text>
                {priceSort === value && <Text style={{ color: theme.colors.brand }}>✓</Text>}
              </TouchableOpacity>
            ))}
            <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 12 }} />
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, fontWeight: "600", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>Price Range</Text>
            <View style={{ flexDirection: "row", gap: 12, marginBottom: 14 }}>
              <TextInput
                style={[styles.priceInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                placeholder="Min" placeholderTextColor={theme.colors.textMuted}
                value={minPrice} onChangeText={setMinPrice} keyboardType="numeric"
              />
              <TextInput
                style={[styles.priceInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                placeholder="Max" placeholderTextColor={theme.colors.textMuted}
                value={maxPrice} onChangeText={setMaxPrice} keyboardType="numeric"
              />
            </View>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Products grid */}

      {/* Rating Modal */}
      <Modal visible={ratingModalOpen} transparent animationType="slide" onRequestClose={() => setRatingModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setRatingModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Minimum Rating</Text>
            {["4","3","2","1"].map((r) => (
              <TouchableOpacity key={r} style={styles.modalItem} onPress={() => { setMinRating(r); setRatingModalOpen(false); }}>
                <Text style={{ color: minRating === r ? theme.colors.brand : theme.colors.text, fontWeight: minRating === r ? "600" : "400" }}>
                  {renderStars(r)}  {r}+ Stars
                </Text>
                {minRating === r && <Text style={{ color: theme.colors.brand }}>✓</Text>}
              </TouchableOpacity>
            ))}
            <TouchableOpacity onPress={() => { setMinRating(""); setRatingModalOpen(false); }} style={{ marginTop: 8, padding: 12 }}>
              <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>Clear Rating Filter</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Discount % Modal */}
      <Modal visible={discountModalOpen} transparent animationType="slide" onRequestClose={() => setDiscountModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setDiscountModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Minimum Discount</Text>
            {["10","20","30","50"].map((pct) => (
              <TouchableOpacity key={pct} style={styles.modalItem} onPress={() => { setDiscountPct(pct); setDiscountModalOpen(false); }}>
                <Text style={{ color: discountPct === pct ? theme.colors.brand : theme.colors.text, fontWeight: discountPct === pct ? "600" : "400" }}>
                  {pct}% or more off
                </Text>
                {discountPct === pct && <Text style={{ color: theme.colors.brand }}>✓</Text>}
              </TouchableOpacity>
            ))}
            <TouchableOpacity onPress={() => { setDiscountPct(""); setDiscountModalOpen(false); }} style={{ marginTop: 8, padding: 12 }}>
              <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>Clear Discount Filter</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Supplier Modal */}
      <Modal visible={supplierModalOpen} transparent animationType="slide" onRequestClose={() => setSupplierModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setSupplierModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Filter by Supplier</Text>
            <TextInput
              style={[styles.priceInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
              placeholder="Type supplier name..." placeholderTextColor={theme.colors.textMuted}
              value={supplierInput} onChangeText={setSupplierInput}
              autoFocus autoCapitalize="none" returnKeyType="search"
              onSubmitEditing={() => { setSupplier(supplierInput.trim()); setSupplierModalOpen(false); }}
            />
            <View style={{ flexDirection: "row", gap: 12, marginTop: 14 }}>
              <TouchableOpacity onPress={() => { setSupplier(""); setSupplierInput(""); setSupplierModalOpen(false); }}
                style={[styles.modalActionBtn, { borderColor: theme.colors.border }]}>
                <Text style={{ color: theme.colors.text, fontWeight: "600" }}>Clear</Text>
              </TouchableOpacity>
              <GradientButton label="Apply" onPress={() => { setSupplier(supplierInput.trim()); setSupplierModalOpen(false); }} />
            </View>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Brand Modal */}
      <Modal visible={brandModalOpen} transparent animationType="slide" onRequestClose={() => setBrandModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setBrandModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Filter by Brand</Text>
            <TextInput
              style={[styles.priceInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
              placeholder="Type brand name..." placeholderTextColor={theme.colors.textMuted}
              value={brandInput} onChangeText={setBrandInput}
              autoFocus autoCapitalize="none" returnKeyType="search"
              onSubmitEditing={() => { setBrand(brandInput.trim()); setBrandModalOpen(false); }}
            />
            <View style={{ flexDirection: "row", gap: 12, marginTop: 14 }}>
              <TouchableOpacity onPress={() => { setBrand(""); setBrandInput(""); setBrandModalOpen(false); }}
                style={[styles.modalActionBtn, { borderColor: theme.colors.border }]}>
                <Text style={{ color: theme.colors.text, fontWeight: "600" }}>Clear</Text>
              </TouchableOpacity>
              <GradientButton label="Apply" onPress={() => { setBrand(brandInput.trim()); setBrandModalOpen(false); }} />
            </View>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Color Modal */}
      <Modal visible={colorModalOpen} transparent animationType="slide" onRequestClose={() => setColorModalOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setColorModalOpen(false)}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }}>Filter by Color</Text>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 12, marginBottom: 16 }}>
              {[
                { name: "Red", hex: theme.colors.danger },
                { name: "Blue", hex: theme.colors.quickActionOrders },
                { name: "Black", hex: theme.colors.text },
                { name: "White", hex: theme.colors.surface2 },
                { name: "Green", hex: theme.colors.success },
                { name: "Yellow", hex: theme.colors.warning },
                { name: "Purple", hex: theme.colors.quickActionCoupons },
                { name: "Pink", hex: theme.colors.quickActionWishlist },
                { name: "Gray", hex: theme.colors.textMuted },
                { name: "Brown", hex: "#92400e" },
              ].map(({ name, hex }) => (
                <TouchableOpacity
                  key={name}
                  onPress={() => { setColor(name.toLowerCase()); setColorModalOpen(false); }}
                  style={{ alignItems: "center", gap: 4 }}
                >
                  <View style={{
                    width: 40, height: 40, borderRadius: 20,
                    backgroundColor: hex,
                    borderWidth: color === name.toLowerCase() ? 3 : 1,
                    borderColor: color === name.toLowerCase() ? theme.colors.brand : theme.colors.border,
                  }} />
                  <Text style={{ color: theme.colors.text, fontSize: 10, fontWeight: color === name.toLowerCase() ? "700" : "400" }}>{name}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity onPress={() => { setColor(""); setColorModalOpen(false); }} style={{ padding: 12 }}>
              <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>Clear Color Filter</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Products grid */}
      {loading ? (
        <LoadingSpinner fullscreen />
      ) : (
        <>
          {/* Result count + view toggle */}
          {(totalCount !== null || products.length > 0) && (
            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginHorizontal: theme.spacing.md, marginTop: 8, marginBottom: 2 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>
                  {totalCount !== null
                    ? `${totalCount} product${totalCount !== 1 ? "s" : ""}${search.trim() ? ` for "${search.trim()}"` : ""}`
                    : `${products.length} product${products.length !== 1 ? "s" : ""} shown`}
                </Text>
                {activeChips.length > 0 && (
                  <View style={{ backgroundColor: theme.colors.brand, borderRadius: 8, paddingHorizontal: 5, paddingVertical: 1, minWidth: 16, alignItems: "center" }}>
                    <Text style={{ color: theme.colors.onBrand, fontSize: 9, fontWeight: "800" }}>{activeChips.length}</Text>
                  </View>
                )}
              </View>
              <View style={{ flexDirection: "row", gap: 4 }}>
                <TouchableOpacity
                  onPress={() => setViewMode("grid")}
                  style={{ padding: 6, borderRadius: 8, backgroundColor: viewMode === "grid" ? theme.colors.brand + "22" : "transparent" }}
                  accessibilityLabel="Grid view"
                >
                  <Ionicons name="grid" size={16} color={viewMode === "grid" ? theme.colors.brand : theme.colors.textMuted} />
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => setViewMode("list")}
                  style={{ padding: 6, borderRadius: 8, backgroundColor: viewMode === "list" ? theme.colors.brand + "22" : "transparent" }}
                  accessibilityLabel="List view"
                >
                  <Ionicons name="list" size={16} color={viewMode === "list" ? theme.colors.brand : theme.colors.textMuted} />
                </TouchableOpacity>
              </View>
            </View>
          )}
          <FlatList
            ref={flatListRef}
            data={products}
            keyExtractor={(p) => String(p.id)}
            key={viewMode === "grid" ? (screenWidth >= 700 ? "products-4" : "products-3") : "products-2"}
            numColumns={viewMode === "grid" ? (screenWidth >= 700 ? 4 : 3) : 2}
            columnWrapperStyle={styles.row}
            contentContainerStyle={styles.grid}
            showsVerticalScrollIndicator={false}
            initialNumToRender={12}
            maxToRenderPerBatch={9}
            windowSize={5}
            removeClippedSubviews
            ListHeaderComponent={
              <View style={{ marginTop: 10, marginBottom: 4 }}>
                <MobileSeasonalBanner
                  embedSearch={false}
                  onQuickFilter={(type) => {
                    if (type === "newArrivals") setNewArrivals(true);
                    else if (type === "deals") setDiscountPct("10");
                  }}
                  onChatPress={() => router.push("/chatbot" as never)}
                />
              </View>
            }
            onScroll={(e) => {
              const y = e.nativeEvent.contentOffset.y;
              setShowBackToTop((prev) => (prev !== y > 400 ? y > 400 : prev));
            }}
            scrollEventThrottle={200}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                tintColor={theme.colors.brand}
              />
            }
            ListEmptyComponent={
              <EmptyState
                title={loadError ? "Unable to load products" : "No products found"}
                subtitle={loadError ? `Check backend connection: ${API_BASE}` : "Try a different search or category"}
                action={{
                  label: loadError ? "Retry" : "Clear filters",
                  onPress: loadError ? () => loadProducts(true) : resetFilters,
                }}
              />
            }
            ListFooterComponent={
              <>
                {hasMore ? (
                  <GradientButton label="Load More" onPress={() => loadProducts(false)} style={{ marginHorizontal: theme.spacing.md, marginTop: 12, marginBottom: 8 }} />
                ) : null}
                <Footer
                  extraLinks={[
                    { key: "profile", label: isLoggedIn ? "Account" : "Sign In", icon: isLoggedIn ? "person-outline" : "log-in-outline", route: isLoggedIn ? "/(tabs)/profile" : "/(auth)/login" },
                    { key: "notifications", label: "Alerts", icon: "notifications-outline", route: "/notifications" },
                  ]}
                />
              </>
            }
            style={{ flex: 1 }}
            renderItem={renderProductItem}
          />
        </>
      )}

      {/* Back to top */}
      {showBackToTop && (
        <TouchableOpacity
          onPress={() => flatListRef.current?.scrollToOffset({ offset: 0, animated: true })}
          activeOpacity={0.9}
          style={{
            position: "absolute",
            right: 16,
            bottom: 64,
            width: 40,
            height: 40,
            borderRadius: 20,
            backgroundColor: theme.colors.surface1,
            borderWidth: 1,
            borderColor: theme.colors.border,
            alignItems: "center",
            justifyContent: "center",
            shadowColor: theme.colors.text,
            shadowOpacity: 0.15,
            shadowRadius: 8,
            shadowOffset: { width: 0, height: 3 },
            elevation: 5,
          }}
        >
          <Ionicons name="chevron-up" size={20} color={theme.colors.text} />
        </TouchableOpacity>
      )}

      <TouchableOpacity
        onPress={() => router.push("/chatbot" as never)}
        activeOpacity={0.9}
        style={{
          position: "absolute",
          right: 16,
          bottom: 18,
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
          paddingHorizontal: 14,
          paddingVertical: 11,
          borderRadius: 22,
          backgroundColor: theme.colors.brand,
          shadowColor: theme.colors.text,
          shadowOpacity: 0.24,
          shadowRadius: 12,
          shadowOffset: { width: 0, height: 6 },
          elevation: 8,
        }}
      >
        <Ionicons name="chatbubble-ellipses" size={18} color={theme.colors.onBrand} />
        <Text style={{ color: theme.colors.onBrand, fontSize: theme.fontSize.sm, fontWeight: "800" }}>Chat</Text>
      </TouchableOpacity>
    </View>
  );
}
