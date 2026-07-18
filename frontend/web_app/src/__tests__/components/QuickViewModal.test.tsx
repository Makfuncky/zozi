import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import QuickViewModal from "@/components/QuickViewModal";
import type { Product } from "@/lib/types";

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
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const addItemMock = jest.fn();
const addToastMock = jest.fn();

jest.mock("@/lib/cartStore", () => ({
  useCartStore: (selector: any) => selector({ addItem: addItemMock }),
}));

jest.mock("@/lib/useRequireAuthAction", () => ({
  useRequireAuthAction: () => (action: () => void) => action(),
}));

jest.mock("@/lib/wishlistStore", () => ({
  useWishlistStore: (selector: any) =>
    selector({ ids: [], add: jest.fn(), remove: jest.fn() }),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: any) => selector({ addToast: addToastMock }),
}));

jest.mock("@/lib/utils", () => ({
  PLACEHOLDER_IMAGE_PATH: "/placeholder.svg",
  resolveImage: (value: string | null | undefined) => value || "/placeholder.svg",
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => selector({ locale: "en", t: (value: string) => value }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) => selector({ format: (value: number) => `$${value}` }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (value: string) => value,
  useTranslateTexts: (values: string[]) => values,
}));

jest.mock("@shared/localization", () => ({
  formatLocalizedDateTime: () => "Apr 1, 10:00",
  isRtlLocale: () => false,
}));

const sampleProduct: Product = {
  id: 101,
  name: "Hook Safe Product",
  description: "A product used for hook-order regression coverage.",
  price: 99,
  category: "Shoes",
  image_url: "/uploads/sample.jpg",
  stock: 12,
  color: "Red, Blue",
  sizes: JSON.stringify(["M", "L"]),
  additional_images: JSON.stringify(["/uploads/extra.jpg"]),
};

describe("QuickViewModal", () => {
  beforeEach(() => {
    addItemMock.mockReset();
    addToastMock.mockReset();
  });

  it("rerenders from null product to a real product without changing hook order", async () => {
    const onClose = jest.fn();
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    const { rerender } = render(<QuickViewModal product={null} onClose={onClose} />);

    rerender(<QuickViewModal product={sampleProduct} onClose={onClose} />);

    await waitFor(() => {
      expect(screen.getByText("Hook Safe Product")).toBeInTheDocument();
    });

    expect(consoleErrorSpy).not.toHaveBeenCalledWith(
      expect.stringContaining("Rendered more hooks than during the previous render")
    );

    consoleErrorSpy.mockRestore();
  });

  it("uses selected variant price, inventory metadata, and product video in quick view", async () => {
    const productWithVariants: Product = {
      ...sampleProduct,
      video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      variants: [
        {
          id: 1,
          product_id: sampleProduct.id,
          title: "Red / M",
          size: "M",
          color: "Red",
          sku: "HOOK-RED-M",
          barcode: "1111111111111",
          product_code: "P-HOOK-RED-M",
          price: 129,
          stock: 4,
          media_url: "/uploads/red-m.jpg",
          material: "Mesh",
          attributes: {},
          is_active: true,
          sort_order: 0,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
    };

    render(<QuickViewModal product={productWithVariants} onClose={jest.fn()} />);

    expect(screen.getByTitle("Hook Safe Product video")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Red" }));
    fireEvent.click(screen.getByRole("button", { name: "M" }));

    expect(screen.getByText("$129")).toBeInTheDocument();
    expect(screen.getByText("HOOK-RED-M")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /addToCart/i }));

    expect(addItemMock).toHaveBeenCalledWith(
      expect.objectContaining({
        price: 129,
        stock: 4,
        image_url: "/uploads/red-m.jpg",
      }),
      expect.objectContaining({
        selectedSize: "M",
        selectedColor: "Red",
      })
    );
    expect(addToastMock).toHaveBeenCalledWith("Added to cart", "success");
  });
});


