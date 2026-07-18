import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockRouter = { push: jest.fn(), replace: jest.fn(), back: jest.fn() };
let mockParams: { id?: string; slug?: string } = { slug: "dream-mart" };

jest.mock("next/navigation", () => ({
  useParams: () => mockParams,
  useRouter: () => mockRouter,
}));

jest.mock("next/image", () => ({
  __esModule: true,
  default: function NextImageMock({ src, alt }: any) { return <img src={src} alt={alt} />; },
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: function NextLinkMock({ href, children, ...props }: any) { return <a href={href} {...props}>{children}</a>; },
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) => selector({ format: (value: number) => `$${value}` }),
}));

jest.mock("@/components/LoadingSkeleton", () => function LoadingSkeletonMock() { return <div>Loading...</div>; });

jest.mock("@shared/productHelpers", () => ({
  getProductBadges: () => [],
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: function MotionDivMock({ children, ...props }: any) { return <div {...props}>{children}</div>; },
    button: function MotionButtonMock({ children, ...props }: any) { return <button {...props}>{children}</button>; },
  },
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
}));

import SupplierStorefrontPage from "@/app/suppliers/[id]/page";

describe("Supplier storefront page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = { slug: "dream-mart" };
    mockApiFetch.mockImplementation((path: string) => {
      if (path === "/suppliers/resolve/dream-mart") {
        return Promise.resolve({ ok: true, json: async () => ({ id: 7, slug: "dream-mart" }) });
      }
      if (path === "/suppliers/7") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: 7,
            username: "dream_mart",
            slug: "dream-mart",
            business_name: "Dream Mart",
            business_type: "company",
            country: "Oman",
            region: "Muscat",
            city: "Muscat",
            website: "https://dreammart.example",
            bio: "A trusted supplier.",
            about_us: "Dream Mart builds reliable storefront experiences.",
            logo_url: null,
            banner_url: null,
            video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            certifications: [],
            social_links: {},
            established_year: 2020,
            verification_status: "approved",
            badge_level: "silver",
            credibility_score: 72,
            member_since: "2024-01-01T00:00:00",
            is_verified: true,
            product_count: 4,
            avg_rating: 4.8,
            total_reviews: 2,
            total_sales: 25,
            recent_reviews: [
              {
                id: 1,
                rating: 5,
                comment: "Fast delivery and great packaging.",
                username: "amina",
                customer_name: "Amina",
                product_name: "Silk Dress",
                created_at: "2026-04-01T00:00:00",
                is_verified_purchase: true,
              },
            ],
          }),
        });
      }
      if (path.startsWith("/suppliers/7/products")) {
        return Promise.resolve({ ok: true, json: async () => ({ items: [], total: 0 }) });
      }
      return Promise.resolve({ ok: false, json: async () => null });
    });
  });

  it("resolves the slug and renders the customer review section", async () => {
    render(<SupplierStorefrontPage />);

    // Switch to the Reviews tab first
    fireEvent.click(await screen.findByText("Reviews"));

    expect(await screen.findByText(/What customers say about Dream Mart/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/suppliers/resolve/dream-mart");
      expect(mockApiFetch).toHaveBeenCalledWith("/suppliers/7");
    });
  });
});


