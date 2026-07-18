import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const mockReplace = jest.fn();
const addToast = jest.fn();

let mockIsLoggedIn = true;
let mockAuthLoading = false;

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...props }: any) => <a href={href} {...props}>{children}</a>,
}));

jest.mock("next/image", () => ({
  __esModule: true,
  default: ({ src, alt, fill, priority, ...props }: any) => <img src={src} alt={alt} {...props} />,
}));

jest.mock("framer-motion", () => ({
  motion: {
    tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

jest.mock("qrcode", () => ({
  __esModule: true,
  default: {
    toDataURL: jest.fn(async () => "data:image/png;base64,qr-preview"),
  },
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: any) => selector({ addToast }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) =>
    selector({
      currency: { code: "AED", symbol: "AED" },
      format: (value: number) => `AED ${value}`,
      convert: (value: number) => value,
      toAED: (value: number) => value,
    }),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (value: string) => value,
}));

jest.mock("@/components/SupplierLayout", () => ({
  __esModule: true,
  default: ({ children, title }: any) => (
    <div>
      <h1>{title}</h1>
      {children}
    </div>
  ),
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "normal" }),
  dc: (_density: string, _compact: string, regular: string, _expanded: string) => regular,
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoading: mockAuthLoading, isLoggedIn: mockIsLoggedIn }),
}));

import SupplierProductsPage from "@/app/supplier/products/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

const mockProducts = [
  {
    id: 20,
    name: "Prod X",
    category: "Fashion",
    subcategory: "Boots",
    brand: "Acme",
    image_url: "/uploads/prod-x.jpg",
    price: 100,
    compare_price: 150,
    stock: 10,
    is_active: true,
    is_new: true,
    sales_count: 0,
    description: "Refreshed hub product",
    color: "Black",
    tags: "neutral, suede",
    sizes: ["37", "38"],
    materials: "Suede",
    visibility_regions: ["OM", "AE"],
    weight: 1.2,
    dimensions: "10x20x30",
    video_url: "/uploads/prod-x.mp4",
    return_window_days: 14,
    additional_images: ["/uploads/prod-x-2.jpg"],
    variants: [
      {
        id: 1,
        product_id: 20,
        title: "37",
        size: "37",
        color: "Black",
        material: "Suede",
        price: 100,
        stock: 10,
        sku: "BOOT-37",
        barcode: "123",
        product_code: "PRD-FAS-PRODX-37-000020-01",
        is_active: true,
        created_at: new Date().toISOString(),
      },
    ],
  },
  {
    id: 21,
    name: "Prod Y",
    category: "Accessories",
    image_url: "/uploads/prod-y.jpg",
    price: 150,
    stock: 5,
    is_active: false,
    sales_count: 2,
  },
  {
    id: 22,
    name: "Prod Z",
    category: "Home",
    image_url: "/uploads/prod-z.jpg",
    price: 75,
    stock: 0,
    is_active: true,
    sales_count: 1,
  },
];

const mockAudit = {
  aiAudit: {
    attentionCount: 2,
    warningCount: 3,
    curatedGroupCount: 2,
    attentionGroups: [
      { id: "catalog-copy", label: "Catalog copy", status: "WARN", warnings: ["Missing richer tags"] },
      { id: "media-coverage", label: "Media coverage", status: "FAIL", warnings: ["Missing gallery coverage"] },
    ],
  },
};

describe("Supplier products page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    mockApiFetch.mockImplementation((url: string, options?: { method?: string; body?: string }) => {
      if (url === "/supplier/products") {
        return Promise.resolve(okJson(mockProducts));
      }
      if (url === "/supplier/reports?period=30d") {
        return Promise.resolve(okJson(mockAudit));
      }
      if (url === "/supplier/products/20" && options?.method === "PUT") {
        return Promise.resolve(
          okJson({
            ...mockProducts[0],
            ...(options?.body ? JSON.parse(options.body) : {}),
          }),
        );
      }
      return Promise.resolve(okJson({}));
    });
  });

  it("renders the refreshed hub toolbar, metrics, and AI audit shortcuts", async () => {
    render(<SupplierProductsPage />);

    expect(await screen.findByText("Product Management")).toBeInTheDocument();
    await screen.findAllByText("Prod X");
    expect(screen.getByRole("link", { name: /open product upload/i })).toHaveAttribute("href", "/supplier/bulk");
    expect(screen.getByPlaceholderText("Search products or categories...")).toBeInTheDocument();
    expect(screen.getByText("Low stock 1")).toBeInTheDocument();
    expect(screen.getByText("Out 1")).toBeInTheDocument();
    expect(screen.getByText(/AI audit review recommended before publishing more products/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open ai report/i })).toHaveAttribute("href", "/supplier/reports");
    expect(screen.getByRole("link", { name: /review catalog copy/i })).toHaveAttribute("href", "/supplier/reports#ai-audit-catalog-copy");
    expect(screen.getByRole("link", { name: /review media coverage/i })).toHaveAttribute("href", "/supplier/reports#ai-audit-media-coverage");
  });

  it("filters the refreshed hub by search and stock state", async () => {
    render(<SupplierProductsPage />);

    const searchInput = await screen.findByPlaceholderText("Search products or categories...");
    fireEvent.change(searchInput, { target: { value: "Prod Y" } });

    await waitFor(() => {
      expect(screen.queryAllByText("Prod X")).toHaveLength(0);
      expect(screen.queryAllByText("Prod Z")).toHaveLength(0);
      expect(screen.queryAllByText("Prod Y").length).toBeGreaterThan(0);
    });

    fireEvent.change(searchInput, { target: { value: "" } });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "out_of_stock" } });

    await waitFor(() => {
      expect(screen.queryAllByText("Prod X")).toHaveLength(0);
      expect(screen.queryAllByText("Prod Y")).toHaveLength(0);
      expect(screen.queryAllByText("Prod Z").length).toBeGreaterThan(0);
    });
  });

  it("opens the upload-aligned editor and saves the normalized supplier payload", async () => {
    render(<SupplierProductsPage />);

    const editButtons = await screen.findAllByLabelText("Edit Prod X");
    fireEvent.click(editButtons[0]);

    expect(await screen.findByText(/this popup now mirrors the upload workflow more closely/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Comma-separated tags")).toHaveValue("neutral, suede");
    expect(screen.getByPlaceholderText("S, M, L or custom sizes")).toHaveValue("37, 38");
    expect(screen.getByPlaceholderText("Cotton, leather, steel")).toHaveValue("Suede");
    expect(screen.getByPlaceholderText("OM, AE, SA")).toHaveValue("OM, AE");
    expect(screen.getByPlaceholderText("https://... or /uploads/file.mp4")).toHaveValue("/uploads/prod-x.mp4");

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/supplier/products/20",
        expect.objectContaining({ method: "PUT" }),
      ),
    );

    const request = mockApiFetch.mock.calls.find((call) => call[0] === "/supplier/products/20");
    const body = JSON.parse(request[1].body);
    expect(body).toMatchObject({
      name: "Prod X",
      price: 100,
      stock_quantity: 10,
      category: "Fashion",
      subcategory: "Boots",
      brand: "Acme",
      color: "Black",
      tags: "neutral, suede",
      sizes: "37, 38",
      materials: "Suede",
      visibility_regions: ["OM", "AE"],
      weight: 1.2,
      dimensions: "10x20x30",
      video_url: "/uploads/prod-x.mp4",
      compare_price: 150,
      return_window_days: 14,
      is_new: true,
    });
  });
});


