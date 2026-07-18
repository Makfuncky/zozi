/**
 * Bulk Operations Integration Tests
 * Tests bulk select + action bar for all 5 pages:
 *   Admin Orders, Admin Products, Admin Suppliers, Admin Users,
 *   Supplier Products, Logistics Shipments
 */

import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

// ─── Shared mocks ─────────────────────────────────────────────────────────────

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const qrToDataURLMock = jest.fn(async () => "data:image/png;base64,qr-preview");

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

const mockUser: any = { id: 1, username: "admin", role: "admin" };
const mockIsLoggedIn = true;
const mockAuthLoading = false;

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ user: mockUser, isLoggedIn: mockIsLoggedIn, isLoading: mockAuthLoading }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  API_URL: "http://localhost:8000",
  getAccessToken: () => "fake-token",
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (sel: any) => sel({ addToast: jest.fn() }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (sel: any) =>
    sel({
      currency: { code: "AED", symbol: "AED" },
      format: (v: number) => `AED ${v}`,
      convert: (v: number) => v,
      toAED: (v: number) => v,
    }),
}));

jest.mock("@shared/adminPermissions", () => ({
  hasAdminPermission: () => true,
  canAccessAdminReturnsManagement: () => true,
  canAccessAdminProductVerification: () => true,
}));

jest.mock("@shared/realtime", () => ({
  createRealtimeRefreshScheduler: jest.fn(() => ({ trigger: jest.fn(), cancel: jest.fn() })),
  openRealtimeSocket: () => ({ close: jest.fn() }),
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: jest.fn(() => null),
  isAdminAlertRealtimeMessage: jest.fn(() => false),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (url: string) => url,
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
}));

jest.mock("next/image", () => ({
  __esModule: true,
  default: ({ src, alt, fill, priority, ...rest }: any) => <img src={src} alt={alt} {...rest} />,
}));

jest.mock("qrcode", () => ({
  __esModule: true,
  default: {
    toDataURL: (...args: any[]) => (qrToDataURLMock as any)(...args),
  },
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="admin-layout">{children}</div>,
}));

jest.mock("@/components/SupplierLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="supplier-layout">{children}</div>,
}));

jest.mock("@/components/LogisticsPartnerLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="logistics-layout">{children}</div>,
}));

jest.mock("framer-motion", () => ({
  motion: {
    tr: ({ children, ...p }: any) => <tr {...p}>{children}</tr>,
    div: ({ children, ...p }: any) => <div {...p}>{children}</div>,
    AnimatePresence: ({ children }: any) => <>{children}</>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Helper to create a Response-like object
function okJson(data: unknown) {
  return { ok: true, json: () => Promise.resolve(data) } as unknown as Response;
}

// ─── Admin Orders ──────────────────────────────────────────────────────────────

describe("Admin Orders – bulk operations", () => {
  const mockOrders = [
    { id: 1, status: "pending", total_price: 100, created_at: new Date().toISOString(), customer_name: "Alice", items: [] },
    { id: 2, status: "pending", total_price: 200, created_at: new Date().toISOString(), customer_name: "Bob", items: [] },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    // Return orders for list; 404 for per-order tracking so trackingByOrder stays empty
    mockApiFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/tracking")) {
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as unknown as Response);
      }
      return Promise.resolve(okJson(mockOrders));
    });
  });

  it("shows BulkActionBar when an order is selected", async () => {
    const { default: AdminOrdersPage } = await import("@/app/admin/orders/page");
    render(<AdminOrdersPage />);
    await waitFor(() => expect(screen.getAllByRole("row").length).toBeGreaterThan(1));

    const checkboxes = screen.getAllByRole("checkbox");
    // First checkbox is select-all; second is first row
    fireEvent.click(checkboxes[1]);

    expect(screen.getByTestId("bulk-action-bar")).toBeInTheDocument();
    expect(screen.getByText("1 selected")).toBeInTheDocument();
  });

  it("calls bulk-status API for selected orders", async () => {
    const order = { id: 1, status: "pending", total_price: 100, created_at: new Date().toISOString(), customer_name: "Alice", items: [] };
    mockApiFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/tracking")) {
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as unknown as Response);
      }
      if (url === "/admin/orders/bulk-status") return Promise.resolve(okJson({ updated: 1 }));
      return Promise.resolve(okJson([order]));
    });

    const { default: AdminOrdersPage } = await import("@/app/admin/orders/page");
    render(<AdminOrdersPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    const applyBtn = screen.getByText(/→/);
    fireEvent.click(applyBtn);

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/orders/bulk-status",
        expect.objectContaining({ method: "POST" })
      )
    );
  });

  it("calls bulk delete API for selected orders", async () => {
    const order = { id: 1, status: "pending", total_price: 100, created_at: new Date().toISOString(), customer_name: "Alice", items: [] };
    mockApiFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/tracking")) {
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as unknown as Response);
      }
      if (url === "/admin/orders/bulk") return Promise.resolve(okJson({ deleted: 1 }));
      return Promise.resolve(okJson([order]));
    });

    const { default: AdminOrdersPage } = await import("@/app/admin/orders/page");
    render(<AdminOrdersPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Delete Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/orders/bulk",
        expect.objectContaining({ method: "DELETE" })
      )
    );
  });
});

// ─── Admin Products ────────────────────────────────────────────────────────────

describe("Admin Products – bulk operations", () => {
  const mockProducts = [
    { id: 10, name: "Widget A", price: 50, stock: 5, is_approved: false, is_deleted: false, verification_status: "pending" },
    { id: 11, name: "Widget B", price: 80, stock: 3, is_approved: false, is_deleted: false, verification_status: "pending" },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockResolvedValue(okJson(mockProducts));
  });

  it("renders select-all button and shows BulkActionBar when product checked", async () => {
    const { default: AdminProductsPage } = await import("@/app/admin/products/page");
    render(<AdminProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));
    expect(screen.getByTestId("bulk-action-bar")).toBeInTheDocument();
  });

  it("calls bulk-moderate (approve) API for selected products", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockProducts))
      .mockResolvedValueOnce(okJson({ updated: 1 }))
      .mockResolvedValueOnce(okJson(mockProducts));

    const { default: AdminProductsPage } = await import("@/app/admin/products/page");
    render(<AdminProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Approve Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/products/bulk-moderate",
        expect.objectContaining({ method: "POST" })
      )
    );
    const body = JSON.parse(
      (mockApiFetch.mock.calls.find((c) => c[0] === "/admin/products/bulk-moderate") as any)[1].body
    );
    expect(body.action).toBe("approve");
  });

  it("calls bulk delete API for selected products", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockProducts))
      .mockResolvedValueOnce(okJson({ deleted: 1 }))
      .mockResolvedValueOnce(okJson(mockProducts));

    const { default: AdminProductsPage } = await import("@/app/admin/products/page");
    render(<AdminProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Archive Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/products/bulk",
        expect.objectContaining({ method: "DELETE" })
      )
    );
  });
});

describe("Admin Returns – bulk operations", () => {
  const mockReturns = [
    { id: 21, order_id: 1001, user_id: 2, reason: "Damaged", status: "pending", created_at: new Date().toISOString() },
    { id: 22, order_id: 1002, user_id: 3, reason: "Wrong size", status: "pending", created_at: new Date().toISOString() },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/returns/bulk") return Promise.resolve(okJson({ processed: 1, skipped: 0, status: "approved" }));
      return Promise.resolve(okJson(mockReturns));
    });
  });

  it("shows BulkActionBar when a return is selected", async () => {
    const { default: ReturnsPanel } = await import("@/app/admin/orders/ReturnsPanel");
    render(<ReturnsPanel />);

    await waitFor(() => expect(screen.getAllByRole("checkbox").length).toBeGreaterThan(1));
    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    expect(screen.getByTestId("bulk-action-bar")).toBeInTheDocument();
    expect(screen.getByText("1 selected")).toBeInTheDocument();
  });

  it("calls returns bulk API for selected returns", async () => {
    const { default: ReturnsPanel } = await import("@/app/admin/orders/ReturnsPanel");
    render(<ReturnsPanel />);

    await waitFor(() => expect(screen.getAllByRole("checkbox").length).toBeGreaterThan(1));
    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    fireEvent.change(screen.getByPlaceholderText("Bulk notes"), { target: { value: "Approved in bulk" } });
    fireEvent.click(screen.getByText("Approve Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/returns/bulk",
        expect.objectContaining({ method: "PUT" })
      )
    );
  });
});

describe("Admin Verification – bulk operations", () => {
  const mockVerifications = {
    items: [
      { id: 31, product_id: 201, order_id: 301, verification_type: "supplier_dispatch", result: "passed", created_at: new Date().toISOString() },
      { id: 32, product_id: 202, order_id: 302, verification_type: "customer_receipt", result: "failed", created_at: new Date().toISOString() },
    ],
    total: 2,
    page: 1,
    page_size: 100,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/product-verifications/bulk") return Promise.resolve(okJson({ processed: 2, skipped: 0, result: "partial" }));
      return Promise.resolve(okJson(mockVerifications));
    });
  });

  it("shows BulkActionBar when a verification is selected", async () => {
    const { default: VerificationPanel } = await import("@/app/admin/products/VerificationPanel");
    render(<VerificationPanel />);

    await waitFor(() => expect(screen.getAllByRole("checkbox").length).toBeGreaterThan(1));
    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    expect(screen.getByTestId("bulk-action-bar")).toBeInTheDocument();
  });

  it("calls verification bulk API for selected rows", async () => {
    const { default: VerificationPanel } = await import("@/app/admin/products/VerificationPanel");
    render(<VerificationPanel />);

    await waitFor(() => expect(screen.getAllByRole("checkbox").length).toBeGreaterThan(1));
    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    fireEvent.change(screen.getByPlaceholderText("Bulk notes"), { target: { value: "Follow-up required" } });
    fireEvent.click(screen.getByText("Mark Partial"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/product-verifications/bulk",
        expect.objectContaining({ method: "PUT" })
      )
    );
  });
});

// ─── Admin Suppliers ───────────────────────────────────────────────────────────

describe("Admin Suppliers – bulk operations", () => {
  const mockSuppliers = [
    {
      id: 5,
      username: "SupA",
      email: "a@sup.com",
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
      product_count: 4,
      order_count: 8,
      revenue: 1200,
      avg_price: 150,
      top_product_name: "Laptop Stand",
      profile: { business_name: "Supplier A", verification_status: "pending", badge_level: "none", credibility_score: 44 },
    },
    {
      id: 6,
      username: "SupB",
      email: "b@sup.com",
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
      product_count: 3,
      order_count: 5,
      revenue: 820,
      avg_price: 164,
      top_product_name: "Desk Lamp",
      profile: { business_name: "Supplier B", verification_status: "pending", badge_level: "bronze", credibility_score: 57 },
    },
  ];

  const supplierListPayload = {
    items: mockSuppliers,
    total: mockSuppliers.length,
    page: 1,
    page_size: 25,
    total_pages: 1,
    summary: {
      pending_suppliers: 2,
      active_suppliers: 2,
      suspended_suppliers: 0,
      total_revenue: 2020,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/admin/suppliers/bulk") return Promise.resolve(okJson({ processed: 1, action: "verify" }));
      if (url.startsWith("/admin/suppliers/") && url.endsWith("/refresh-badge")) return Promise.resolve(okJson({ badge_level: "gold" }));
      if (url.startsWith("/admin/suppliers/all")) return Promise.resolve(okJson(supplierListPayload));
      return Promise.resolve(okJson({ items: [] }));
    });
  });

  it("shows BulkActionBar when a supplier is selected", async () => {
    const { default: AdminSuppliersPage } = await import("@/app/admin/suppliers/page");
    render(<AdminSuppliersPage />);
    await waitFor(() => expect(screen.getAllByRole("checkbox").length).toBeGreaterThan(2));

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));
    expect(screen.getByTestId("bulk-action-bar")).toBeInTheDocument();
  });

  it("calls supplier bulk lifecycle API when 'Approve Selected' clicked", async () => {
    const { default: AdminSuppliersPage } = await import("@/app/admin/suppliers/page");
    render(<AdminSuppliersPage />);
    await waitFor(() => expect(screen.getByText("Pending approvals")).toBeInTheDocument());

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Approve Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/suppliers/bulk",
        expect.objectContaining({ method: "POST" })
      )
    );
    const body = JSON.parse(
      (mockApiFetch.mock.calls.find((c) => c[0] === "/admin/suppliers/bulk") as any)[1].body
    );
    expect(body.action).toBe("verify");
    expect(body.supplier_ids).toContain(5);
  });

  it("submits a bulk badge assignment with the selected badge level", async () => {
    const { default: AdminSuppliersPage } = await import("@/app/admin/suppliers/page");
    render(<AdminSuppliersPage />);

    await waitFor(() => expect(screen.getByText("Pending approvals")).toBeInTheDocument());

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    const bulkBar = screen.getByTestId("bulk-action-bar");
    const selects = bulkBar.querySelectorAll("select");
    fireEvent.change(selects[0], { target: { value: "gold" } });
    fireEvent.click(screen.getByText("Assign Badge"));

    await waitFor(() => {
      const bulkCall = mockApiFetch.mock.calls.find((call) => call[0] === "/admin/suppliers/bulk");
      expect(bulkCall).toBeTruthy();
      expect(JSON.parse(bulkCall[1].body)).toEqual(expect.objectContaining({ action: "badge", badge_level: "gold", supplier_ids: [5] }));
    });
  });
});

// ─── Admin Users ───────────────────────────────────────────────────────────────

describe("Admin Users – bulk operations", () => {
  const mockUsers = [
    { id: 100, username: "userA", email: "a@user.com", role: "customer", is_active: true, is_verified: true, created_at: new Date().toISOString() },
    { id: 101, username: "userB", email: "b@user.com", role: "customer", is_active: false, is_verified: false, created_at: new Date().toISOString() },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockResolvedValue(okJson(mockUsers));
  });

  it("shows BulkActionBar when a user is selected", async () => {
    const { default: AdminUsersPage } = await import("@/app/admin/users/page");
    render(<AdminUsersPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    // First checkbox is select-all header; second is first data row
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));
    expect(within(screen.getByTestId("bulk-action-bar")).getByText("1 selected")).toBeInTheDocument();
  });

  it("calls bulk-toggle-active API with selected user ids and explicit status", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockUsers))
      .mockResolvedValueOnce(okJson({ updated: 1 }))
      .mockResolvedValueOnce(okJson(mockUsers));

    const { default: AdminUsersPage } = await import("@/app/admin/users/page");
    render(<AdminUsersPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Suspend Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/users/bulk-toggle-active",
        expect.objectContaining({ method: "POST" })
      )
    );
    const body = JSON.parse(
      (mockApiFetch.mock.calls.find((c) => c[0] === "/admin/users/bulk-toggle-active") as any)[1].body
    );
    expect(body.user_ids).toContain(100);
    expect(body.is_active).toBe(false);
  });

  it("calls bulk role update API with selected user ids", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockUsers))
      .mockResolvedValueOnce(okJson({ updated: 1 }))
      .mockResolvedValueOnce(okJson(mockUsers));

    const { default: AdminUsersPage } = await import("@/app/admin/users/page");
    render(<AdminUsersPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.change(screen.getByLabelText("Bulk role target"), {
      target: { value: "supplier" },
    });
    fireEvent.click(screen.getByText("Assign Role"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/users/bulk-role",
        expect.objectContaining({ method: "POST" })
      )
    );
    const body = JSON.parse(
      (mockApiFetch.mock.calls.find((c) => c[0] === "/admin/users/bulk-role") as any)[1].body
    );
    expect(body.user_ids).toContain(100);
    expect(body.role).toBe("supplier");
  });

  it("selects / deselects all via header checkbox", async () => {
    const { default: AdminUsersPage } = await import("@/app/admin/users/page");
    render(<AdminUsersPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    const [selectAllCb] = screen.getAllByRole("checkbox");
    fireEvent.click(selectAllCb);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));
    expect(within(screen.getByTestId("bulk-action-bar")).getByText("2 selected")).toBeInTheDocument();

    // Deselect all
    fireEvent.click(selectAllCb);
    await waitFor(() => expect(screen.queryByTestId("bulk-action-bar")).not.toBeInTheDocument());
  });
});

// ─── Supplier Products ─────────────────────────────────────────────────────────

describe("Supplier Products – bulk operations", () => {
  const mockProducts = [
    { id: 20, name: "Prod X", category: "Fashion", image_url: "/uploads/prod-x.jpg", price: 100, stock: 10, is_active: true, sales_count: 0, tags: "neutral, suede", materials: "Suede", variants: [{ id: 1, product_id: 20, title: "37", size: "37", color: "Beige", material: "Suede", price: 100, stock: 10, sku: "BOOT-37", barcode: "123", product_code: "PRD-FAS-PRODX-37-000020-01", is_active: true, created_at: new Date().toISOString() }] },
    { id: 21, name: "Prod Y", category: "Accessories", image_url: "/uploads/prod-y.jpg", price: 150, stock: 5, is_active: false, sales_count: 2 },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockResolvedValue(okJson(mockProducts));
  });

  it("shows BulkActionBar when a product is selected (desktop table)", async () => {
    const { default: SupplierProductsPage } = await import("@/app/supplier/products/page");
    render(<SupplierProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    const checkboxes = screen.getAllByRole("checkbox");
    // First may be the select-all; click a row checkbox
    fireEvent.click(checkboxes[0]);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));
  });

  it("calls POST /supplier/products/bulk with camelCase body to activate", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockProducts))
      .mockResolvedValueOnce(okJson({ updated: 1 }));

    const { default: SupplierProductsPage } = await import("@/app/supplier/products/page");
    render(<SupplierProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Activate Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/supplier/products/bulk",
        expect.objectContaining({ method: "POST" })
      )
    );
    const body = JSON.parse(
      (mockApiFetch.mock.calls.find((c) => c[0] === "/supplier/products/bulk") as any)[1].body
    );
    expect(body.productIds).toBeDefined(); // camelCase!
    expect(body.type).toBe("status_change");
    expect(body.value).toBe("active");
  });

  it("calls POST /supplier/products/bulk with value=inactive to deactivate", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockProducts))
      .mockResolvedValueOnce(okJson({ updated: 1 }));

    const { default: SupplierProductsPage } = await import("@/app/supplier/products/page");
    render(<SupplierProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    fireEvent.click(screen.getByText("Deactivate Selected"));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/supplier/products/bulk",
        expect.objectContaining({ method: "POST" })
      )
    );
    const body = JSON.parse(
      (mockApiFetch.mock.calls.find((c) => c[0] === "/supplier/products/bulk") as any)[1].body
    );
    expect(body.value).toBe("inactive");
  });

  it("opens a reusable QR bundle modal for a saved supplier product", async () => {
    const { default: SupplierProductsPage } = await import("@/app/supplier/products/page");
    render(<SupplierProductsPage />);
    await waitFor(() => screen.getAllByRole("checkbox"));

    fireEvent.click(screen.getAllByLabelText("QR bundle Prod X")[0]);

    expect(await screen.findByText("Reusable QR Bundle")).toBeInTheDocument();
    expect(await screen.findByAltText(/qr bundle for prod x/i)).toBeInTheDocument();
    expect(screen.getByText(/same supplier QR payload as Product Upload/i)).toBeInTheDocument();
    expect(qrToDataURLMock).toHaveBeenCalled();
  });
});

// ─── Logistics Shipments ───────────────────────────────────────────────────────

describe("Logistics Shipments – bulk operations", () => {
  const mockShipmentData = {
    total: 2,
    page: 1,
    page_size: 30,
    total_pages: 1,
    items: [
      {
        id: 200,
        order_id: 1001,
        status: "prepared",
        carrier_name: "FastShip",
        tracking_number: "TRK001",
        scan_code: "SC001",
      },
      {
        id: 201,
        order_id: 1002,
        status: "shipped",
        carrier_name: "FastShip",
        tracking_number: "TRK002",
        scan_code: "SC002",
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiFetch.mockReset();
    mockApiFetch.mockResolvedValue(okJson(mockShipmentData));
  });

  it("shows BulkActionBar when a shipment is checked", async () => {
    const { default: LogisticsShipmentsPage } = await import(
      "@/app/logistics-partner/shipments/page"
    );
    render(<LogisticsShipmentsPage />);
    await waitFor(() => screen.getAllByRole("checkbox", { name: "Select row" }));

    fireEvent.click(screen.getAllByRole("checkbox", { name: "Select row" })[0]);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));
    expect(screen.getByText("1 selected")).toBeInTheDocument();
  });

  it("calls PUT /logistics-partner/shipments/bulk-status", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson(mockShipmentData))
      .mockResolvedValueOnce(okJson({ updated: 1 }))
      .mockResolvedValueOnce(okJson(mockShipmentData));

    const { default: LogisticsShipmentsPage } = await import(
      "@/app/logistics-partner/shipments/page"
    );
    render(<LogisticsShipmentsPage />);
    await waitFor(() => screen.getAllByRole("checkbox", { name: "Select row" }));

    fireEvent.click(screen.getAllByRole("checkbox", { name: "Select row" })[0]);

    await waitFor(() => screen.getByTestId("bulk-action-bar"));

    // Click the apply-status button (label: "Set to <status>")
    const applyBtn = screen.getByRole("button", { name: /set to/i });
    fireEvent.click(applyBtn);

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partner/shipments/bulk-status",
        expect.objectContaining({ method: "PUT" })
      )
    );
    const body = JSON.parse(
      (
        mockApiFetch.mock.calls.find(
          (c) => c[0] === "/logistics-partner/shipments/bulk-status"
        ) as any
      )[1].body
    );
    expect(body.shipment_ids).toContain(200);
    expect(body.status).toBeTruthy();
  });
});


