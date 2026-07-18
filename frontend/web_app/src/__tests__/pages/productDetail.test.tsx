import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

import ProductDetailPage from "@/app/products/[id]/page";
import type { Product } from "@/lib/types";

const mockApiFetch = jest.fn();
const mockAddItem = jest.fn();
const mockAddToast = jest.fn();
const mockPush = jest.fn();
const mockBack = jest.fn();
const mockTrackRecent = jest.fn();

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "101" }),
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

jest.mock("next/image", () => function NextImageMock(props: any) {
  const { alt, src, fill, priority, ...rest } = props;
  return <img alt={alt} src={typeof src === "string" ? src : ""} {...rest} />;
});

jest.mock("next/link", () =>
  function NextLinkMock({ children, href, ...rest }: any) {
    return <a href={href} {...rest}>{children}</a>;
  }
);

jest.mock("framer-motion", () => ({
  motion: new Proxy({}, {
    get: () => ({ children, ...props }: any) => <div {...props}>{children}</div>,
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (value: string | null | undefined) => value || "/placeholder.svg",
  parseProductId: (value: string) => Number.parseInt(value, 10),
  supplierStorefrontPath: () => "/suppliers/test-supplier",
}));

jest.mock("@/lib/cartStore", () => ({
  useCartStore: (selector: any) => selector({ addItem: mockAddItem }),
}));

jest.mock("@/lib/useRequireAuthAction", () => ({
  useRequireAuthAction: () => (action: () => void) => action(),
}));

jest.mock("@/lib/wishlistStore", () => ({
  useWishlistStore: (selector: any) => selector({ ids: [], add: jest.fn(), remove: jest.fn() }),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: any) => selector({ addToast: mockAddToast }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoggedIn: true }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) => selector({ format: (value: number) => `$${value}` }),
}));

jest.mock("@/lib/recentlyViewedStore", () => ({
  useRecentlyViewedStore: (selector: any) => selector({ track: mockTrackRecent }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => selector({ locale: "en", t: (value: string) => value }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (value: string) => value,
  useTranslateTexts: (values: string[]) => values,
}));

jest.mock("@/components/LoadingSkeleton", () => function LoadingSkeletonMock() {
  return <div>Loading...</div>;
});

jest.mock("@/components/Recommendations", () => function RecommendationsMock() {
  return <div data-testid="recommendations" />;
});

jest.mock("@/components/RecentlyViewed", () => function RecentlyViewedMock() {
  return <div data-testid="recently-viewed" />;
});

jest.mock("@/components/TranslatedText", () => function TranslatedTextMock({ text }: any) {
  return <>{text}</>;
});

jest.mock("@shared/localization", () => ({
  formatLocalizedDate: () => "Apr 7, 2026",
  isRtlLocale: () => false,
}));

jest.mock("@shared/statusColors", () => ({
  getPartnerBadgeStyle: () => "theme-chip-brand",
}));

const variantProduct: Product = {
  id: 101,
  name: "Variant Tested Product",
  description: "Variant-aware product page coverage.",
  price: 149,
  category: "Electronics",
  image_url: "/uploads/base-product.jpg",
  stock: 20,
  color: "Black, White",
  sizes: JSON.stringify(["128 GB", "256 GB"]),
  additional_images: JSON.stringify(["/uploads/gallery.jpg"]),
  video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  variants: [
    {
      id: 1,
      product_id: 101,
      title: "Black / 128 GB",
      size: "128 GB",
      color: "Black",
      sku: "ELEC-TEST-BLK-128",
      barcode: "9000000000001",
      product_code: "P-TEST-BLK-128",
      price: 129,
      stock: 4,
      media_url: "/uploads/variant-black-128.jpg",
      material: "Aluminium",
      attributes: {},
      is_active: true,
      sort_order: 0,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
    {
      id: 2,
      product_id: 101,
      title: "White / 256 GB",
      size: "256 GB",
      color: "White",
      sku: "ELEC-TEST-WHT-256",
      barcode: "9000000000002",
      product_code: "P-TEST-WHT-256",
      price: 169,
      stock: 6,
      media_url: "/uploads/variant-white-256.jpg",
      material: "Aluminium",
      attributes: {},
      is_active: true,
      sort_order: 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ],
};

describe("ProductDetailPage", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/products/101") {
        return { ok: true, json: async () => variantProduct };
      }
      if (path === "/reviews/products/101") {
        return { ok: true, json: async () => [] };
      }
      return { ok: false, json: async () => ({}) };
    });
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
  });

  it("renders product video and switches variant price, media, and add-to-cart payload", async () => {
    await act(async () => {
      render(<ProductDetailPage />);
    });

    expect(await screen.findByText("Variant Tested Product")).toBeInTheDocument();
    expect(screen.getByTitle("Variant Tested Product video")).toBeInTheDocument();
    expect(screen.getByText("$149")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "128 GB" }));
    fireEvent.click(screen.getByTitle("Black"));

    expect(screen.getByText("$129")).toBeInTheDocument();
    expect(screen.getAllByText("ELEC-TEST-BLK-128").length).toBeGreaterThan(0);
    expect(screen.getByText("P-TEST-BLK-128")).toBeInTheDocument();
    expect(screen.getByText("9000000000001")).toBeInTheDocument();
    expect(screen.getByAltText("Variant Tested Product")).toHaveAttribute("src", "/uploads/variant-black-128.jpg");

    fireEvent.click(screen.getByRole("button", { name: "256 GB" }));
    fireEvent.click(screen.getByTitle("White"));

    expect(screen.getByText("$169")).toBeInTheDocument();
    expect(screen.getAllByText("ELEC-TEST-WHT-256").length).toBeGreaterThan(0);
    expect(screen.getByAltText("Variant Tested Product")).toHaveAttribute("src", "/uploads/variant-white-256.jpg");

    fireEvent.click(screen.getByRole("button", { name: /addToCart/i }));

    expect(mockAddItem).toHaveBeenCalledWith(
      expect.objectContaining({
        price: 169,
        stock: 6,
        image_url: "/uploads/variant-white-256.jpg",
      }),
      expect.objectContaining({
        quantity: 1,
        selectedSize: "256 GB",
        selectedColor: "White",
      })
    );
    expect(mockAddToast).toHaveBeenCalledWith("Added to cart", "success");
    expect(mockTrackRecent).toHaveBeenCalledWith(expect.objectContaining({ id: 101, name: "Variant Tested Product" }));
  });
});


