import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

import Recommendations from "@/components/Recommendations";

const mockApiFetch = jest.fn();
let mockIsLoggedIn = false;
let mockRecentlyViewedProducts: Array<{ id: number; category?: string }> = [];

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getAccessToken: () => null,
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoggedIn: mockIsLoggedIn }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) => selector({ format: (value: number) => `$${value}` }),
}));

jest.mock("@/lib/recentlyViewedStore", () => ({
  useRecentlyViewedStore: (selector: any) => selector({ products: mockRecentlyViewedProducts }),
}));

jest.mock("@/components/ProductCard", () => function ProductCardMock({ product }: any) {
  return <div data-testid="recommendation-card">{product.name}</div>;
});

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

function okJson(data: any) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Recommendations", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoggedIn = false;
    mockRecentlyViewedProducts = [];
  });

  it("filters the current product and does not refetch on equivalent rerenders", async () => {
    mockApiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/search/recommendations/public?")) {
        return Promise.resolve(
          okJson({
            products: [
              {
                id: 1,
                name: "Current Product",
                price: 99,
                category: "electronics",
                stock: 10,
                supplier_id: 7,
                image_url: null,
                description: "",
              },
              {
                id: 2,
                name: "Recommended Product",
                price: 149,
                category: "electronics",
                stock: 4,
                supplier_id: 7,
                image_url: null,
                description: "",
              },
            ],
          })
        );
      }

      return Promise.resolve(okJson([]));
    });

    const { rerender } = render(
      <Recommendations currentCategory="electronics" excludeIds={[1]} />
    );

    expect(await screen.findByText("You May Also Like")).toBeInTheDocument();
    expect(screen.getByText("Recommended Product")).toBeInTheDocument();
    expect(screen.queryByText("Current Product")).not.toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledTimes(1);
    });
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/search/recommendations/public?limit=8&category=electronics"
    );

    rerender(<Recommendations currentCategory="electronics" excludeIds={[1]} />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledTimes(1);
    });
  });
});


