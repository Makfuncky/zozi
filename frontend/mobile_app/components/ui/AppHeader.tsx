import React, { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { HeaderBar } from "@/components/ui/HeaderBar";
import ProductSearchFilterBar, { CATEGORY_VALUES } from "@/components/ui/ProductSearchFilterBar";
import { useThemeStore } from "@/lib/themeStore";
import { useAuthStore } from "@/lib/authStore";
import { useLocaleStore } from "@/lib/localeStore";
import { isRtlLocale } from "@shared/localization";
import { openLeftDrawer, openRightDrawer } from "@/lib/uiBus";

let LinearGradient: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  LinearGradient = null;
}

export interface AppHeaderProps {
  /**
   * When true (default), the branded lime HeaderBar (menu / ZOZI / account)
   * is rendered above the search+filter bar — identical to the Products screen.
   */
  showHeaderBar?: boolean;
  /**
   * When true (default), the web-style single-row Search + Filter bar is shown,
   * pulled up into the lime header exactly like the Products screen.
   */
  showSearch?: boolean;
  /**
   * Optional back handler. When provided, the left button renders a back chevron
   * (instead of opening the menu drawer) — used by standalone screens so they can
   * return to where they came from while keeping the SAME header as the Shop screen.
   */
  onBack?: () => void;
}

/**
 * Unified app header — the SAME lime HeaderBar + web-style Search/Filter bar used
 * on the Products (Shop) screen, extracted so every customer-facing screen shares
 * an identical header.
 *
 * The search + filter controls are self-contained here: committing a search or
 * changing any filter navigates to the Shop screen (`/(tabs)/products`) with the
 * matching query params, which the Shop screen reads via `resolveProductRouteFilters`.
 * This keeps the header visually and behaviourally consistent everywhere while the
 * actual product list only lives on the Shop screen.
 */
function AppHeader({
  showHeaderBar = true,
  showSearch = true,
  onBack,
}: AppHeaderProps) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const { isLoggedIn } = useAuthStore();
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);

  // Self-contained draft filter state (applied by navigating to the Shop screen).
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [newArrivals, setNewArrivals] = useState(false);
  const [trendingOnly, setTrendingOnly] = useState(false);
  const [discountPct, setDiscountPct] = useState("");

  const currentCategoryLabel =
    CATEGORY_VALUES.find((c) => c.value === category)?.label ?? "All";

  const goToShop = (overrides?: Record<string, string>) => {
    const params: Record<string, string> = {};
    if (search.trim()) params.search = search.trim();
    if (category && category !== "all") params.category = category;
    if (newArrivals) params.newArrivals = "1";
    if (trendingOnly) params.trending = "1";
    if (discountPct) params.discountPct = discountPct;
    Object.assign(params, overrides ?? {});

    const qs = new URLSearchParams(params).toString();
    router.push((qs ? `/(tabs)/products?${qs}` : "/(tabs)/products") as never);
  };

  const activeFilterCount =
    (search.trim() ? 1 : 0) +
    (category !== "all" ? 1 : 0) +
    (newArrivals ? 1 : 0) +
    (trendingOnly ? 1 : 0) +
    (discountPct ? 1 : 0);

  const resetFilters = () => {
    setSearch("");
    setCategory("all");
    setNewArrivals(false);
    setTrendingOnly(false);
    setDiscountPct("");
  };

  return (
    <View style={{ backgroundColor: "transparent" }}>
      {showHeaderBar ? (
        <HeaderBar
          onLeftPress={onBack ?? openLeftDrawer}
          onRightPress={() => {
            if (isLoggedIn) openRightDrawer();
            else router.push("/(auth)/login" as never);
          }}
        />
      ) : null}

      {showSearch ? (
        <View style={{ marginTop: showHeaderBar ? -104 : 0 }}>
          <ProductSearchFilterBar
            search={search}
            onSetSearch={setSearch}
            onCommitSearch={() => goToShop()}
            onImageSearch={() => router.push("/(tabs)/products" as never)}
            onNotificationsPress={() => router.push("/notifications" as never)}
            category={category}
            currentCategoryLabel={currentCategoryLabel}
            onCategoryPress={() => {
              // Cycle to the next category as a lightweight in-header picker,
              // then jump to the Shop screen where the full modal lives.
              goToShop();
            }}
            priceActive={false}
            onPricePress={() => goToShop()}
            ratingActive={false}
            onRatingPress={() => goToShop()}
            supplierActive={false}
            onSupplierPress={() => goToShop()}
            newArrivals={newArrivals}
            trendingOnly={trendingOnly}
            onToggleNewArrivals={() => {
              const next = !newArrivals;
              setNewArrivals(next);
              goToShop({ newArrivals: next ? "1" : "" });
            }}
            onToggleTrending={() => {
              const next = !trendingOnly;
              setTrendingOnly(next);
              goToShop({ trending: next ? "1" : "" });
            }}
            discountPct={discountPct}
            onDiscountPress={() => goToShop()}
            activeFilterCount={activeFilterCount}
            onResetFilters={resetFilters}
            isRtl={isRtl}
          />
        </View>
      ) : null}
    </View>
  );
}

export default React.memo(AppHeader);
export { AppHeader };
