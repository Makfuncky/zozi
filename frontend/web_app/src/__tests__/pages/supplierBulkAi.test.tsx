import React from "react";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

const apiFetchMock = jest.fn();
const addToastMock = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
}));

jest.mock("framer-motion", () => ({
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
  motion: {
    div: ({ children, layout, initial, animate, exit, transition, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

jest.mock("@/components/SupplierLayout", () => function SupplierLayoutMock({ children }: any) {
  return <div data-testid="supplier-layout">{children}</div>;
});

jest.mock("@/components/PanelPage", () => ({
  PanelContent: function PanelContentMock({ children }: any) { return <div>{children}</div>; },
  PanelHero: function PanelHeroMock({ children }: any) { return <div>{children}</div>; },
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => apiFetchMock(...args),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) => selector({ currency: { code: "AED" } }),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: any) => selector({ addToast: addToastMock }),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (value: string) => value,
}));

jest.mock("@shared/supplierProductOptions", () => ({
  getSupplierVariantTemplate: () => ({ options: [] }),
  suggestSupplierVariantTemplate: () => "universal",
  SUPPLIER_VARIANT_TEMPLATES: [],
}));

import SupplierBulkUploadPage from "@/app/supplier/bulk/page";

async function renderPage() {
  let view!: ReturnType<typeof render>;
  await act(async () => {
    view = render(<SupplierBulkUploadPage />);
    await Promise.resolve();
  });
  return view;
}

function attachFiles(input: HTMLInputElement, files: File[]) {
  Object.defineProperty(input, "files", {
    configurable: true,
    value: files,
  });
  fireEvent.change(input);
}

describe("Supplier bulk upload", () => {
  beforeAll(() => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: jest.fn(() => "blob:preview"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: jest.fn(),
    });
  });

  beforeEach(() => {
    jest.clearAllMocks();
    apiFetchMock.mockImplementation(async (path: string) => {
      if (path === "/supplier/regions") {
        return {
          ok: true,
          json: async () => ({ operating_regions: ["United Arab Emirates", "Saudi Arabia"] }),
        };
      }
      if (path === "/ai/suggest") {
        return {
          ok: true,
          json: async () => ({
            name: "AI Lounge Chair",
            category: "Furniture",
            color: "Gray",
            color_candidates: ["Gray", "Ivory"],
            tags_string: "lounge chair, reading nook",
            material_suggestions: ["Ash wood", "Linen blend"],
            variant_template: "home-furniture",
            variant_options: ["Small", "Large"],
            description: "Comfortable lounge chair for reading corners and living rooms.",
            ai_powered: false,
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          created_count: 1,
          error_count: 0,
          errors: [],
          ai_used: false,
          products: [],
        }),
      };
    });
  });

  it("includes pricing, currency, return policy, and listing controls in the bulk upload payload", async () => {
    await renderPage();

    fireEvent.change(screen.getByPlaceholderText(/wireless bluetooth earphones/i), { target: { value: "Upload Policy Product" } });
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "89.99" } });
    fireEvent.change(screen.getByLabelText(/^Currency$/i), { target: { value: "USD" } });
    fireEvent.click(screen.getByRole("combobox", { name: /^category$/i }));
    fireEvent.change(screen.getByPlaceholderText(/search categories/i), { target: { value: "furn" } });
    fireEvent.click(screen.getByRole("option", { name: "Furniture" }));
    fireEvent.click(screen.getByRole("combobox", { name: /^sub-category$/i }));
    fireEvent.change(screen.getByPlaceholderText(/search sub-categories/i), { target: { value: "chair" } });
    fireEvent.click(screen.getByRole("option", { name: "Chairs" }));
    const showAdvancedButton = screen.queryByRole("button", { name: /^show advanced$/i });
    if (showAdvancedButton) {
      fireEvent.click(showAdvancedButton);
    }
    fireEvent.change(screen.getAllByLabelText(/material/i)[0], { target: { value: "Ash wood and linen" } });
    fireEvent.change(screen.getAllByLabelText(/weight/i)[0], { target: { value: "18.5" } });
    fireEvent.change(screen.getAllByLabelText(/dimensions/i)[0], { target: { value: "92 x 84 x 88 cm" } });
    fireEvent.change(screen.getByLabelText(/return window/i), { target: { value: "21" } });
    fireEvent.click(screen.getByRole("button", { name: /live on storefront/i }));
    fireEvent.click(screen.getByRole("button", { name: /upload 1 product/i }));

    await waitFor(() => expect(apiFetchMock).toHaveBeenCalledWith("/supplier/products/bulk-upload", expect.anything()));

    const uploadCall = apiFetchMock.mock.calls.find(([path]) => path === "/supplier/products/bulk-upload");
    expect(uploadCall).toBeDefined();
    const [, requestInit] = uploadCall!;
    expect(requestInit?.method).toBe("POST");

    const formData = requestInit?.body as FormData;
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get("use_ai")).toBeNull();

    const productsPayload = JSON.parse(String(formData.get("products_json")));
    expect(productsPayload).toHaveLength(1);
    expect(productsPayload[0]).toMatchObject({
      name: "Upload Policy Product",
      price: 89.99,
      currency: "USD",
      category: "Furniture",
      subcategory: "Chairs",
      visibility_regions: ["United Arab Emirates", "Saudi Arabia"],
      return_window_days: 21,
      is_active: false,
    });
    expect(productsPayload[0].compare_price).toBeUndefined();

    await waitFor(() => expect(addToastMock).toHaveBeenCalledWith("1 product uploaded successfully", "success"));
  });

  it("duplicates a prepared draft so suppliers can reuse repeated catalog data", async () => {
    await renderPage();

    fireEvent.change(screen.getByPlaceholderText(/wireless bluetooth earphones/i), { target: { value: "Copy Source Product" } });
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "79.99" } });
    fireEvent.change(screen.getByLabelText(/^Currency$/i), { target: { value: "SAR" } });
    fireEvent.change(screen.getByLabelText(/^Category$/i), { target: { value: "Electronics" } });
    fireEvent.change(screen.getByPlaceholderText(/brand name/i), { target: { value: "Studio Brand" } });

    fireEvent.click(screen.getByRole("button", { name: /duplicate draft/i }));

    const nameInputs = screen.getAllByPlaceholderText(/wireless bluetooth earphones/i) as HTMLInputElement[];
    const priceInputs = screen.getAllByPlaceholderText("0.00") as HTMLInputElement[];
    const brandInputs = screen.getAllByPlaceholderText(/brand name/i) as HTMLInputElement[];
    const currencyInputs = screen.getAllByLabelText(/^Currency$/i) as HTMLSelectElement[];

    expect(nameInputs).toHaveLength(2);
    expect(nameInputs[1]).toHaveValue("Copy Source Product");
    expect(priceInputs[1]).toHaveValue(79.99);
    expect(brandInputs[1]).toHaveValue("Studio Brand");
    expect(currencyInputs[1]).toHaveValue("SAR");
    expect(addToastMock).toHaveBeenCalledWith("Draft duplicated. Reuse the copied details and adjust only what changed.", "success");
  });

  it("applies AI suggestions and normalizes searchable category values", async () => {
    await renderPage();

    fireEvent.change(screen.getByPlaceholderText(/wireless bluetooth earphones/i), { target: { value: "Reading Chair" } });
    fireEvent.click(screen.getByRole("button", { name: /use ai from photo/i }));

    await waitFor(() => expect(apiFetchMock).toHaveBeenCalledWith("/ai/suggest", expect.anything()));
    await waitFor(() => expect(screen.getByPlaceholderText(/wireless bluetooth earphones/i)).toHaveValue("AI Lounge Chair"));
    expect(screen.getByRole("combobox", { name: /^category$/i })).toHaveTextContent("Furniture");
    expect(screen.getByRole("combobox", { name: /^sub-category$/i })).toHaveTextContent("Chairs");
    expect(screen.getByLabelText(/^Color$/i)).toHaveValue("Grey");
    expect(screen.getByDisplayValue(/lounge chair, reading nook/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue(/comfortable lounge chair/i)).toBeInTheDocument();
    expect(addToastMock).toHaveBeenCalledWith("Smart suggestions applied using fallback rules", "success");
  });

  it("uses searchable combo boxes for category and sub-category selection", async () => {
    await renderPage();

    fireEvent.click(screen.getByRole("combobox", { name: /^category$/i }));
    fireEvent.change(screen.getByPlaceholderText(/search categories/i), { target: { value: "furn" } });
    fireEvent.click(screen.getByRole("option", { name: "Furniture" }));

    fireEvent.click(screen.getByRole("combobox", { name: /^sub-category$/i }));
    fireEvent.change(screen.getByPlaceholderText(/search sub-categories/i), { target: { value: "chair" } });
    fireEvent.click(screen.getByRole("option", { name: "Chairs" }));

    expect(screen.getByRole("combobox", { name: /^category$/i })).toHaveTextContent("Furniture");
    expect(screen.getByRole("combobox", { name: /^sub-category$/i })).toHaveTextContent("Chairs");
  });

  it("includes product video and explicit variant inventory in the bulk upload payload", async () => {
    const { container } = await renderPage();

    fireEvent.change(screen.getByPlaceholderText(/wireless bluetooth earphones/i), { target: { value: "Variant Video Product" } });
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "149.99" } });
    fireEvent.change(screen.getByLabelText(/^Stock$/i), { target: { value: "8" } });
    // Select "Black" from the color chip picker
    fireEvent.click(screen.getByRole("button", { name: /^Black$/i }));
    const productVideoInput = container.querySelector('input[accept="video/mp4,video/webm"]') as HTMLInputElement | null;
    expect(productVideoInput).not.toBeNull();
    attachFiles(productVideoInput!, [new File(["video"], "demo.mp4", { type: "video/mp4" })]);

    fireEvent.change(screen.getByLabelText(/custom size \/ option values/i), { target: { value: "128 GB" } });
    // Expand shapes section (collapsed by default) then click Slim
    fireEvent.click(screen.getByRole("button", { name: /add shape variants/i }));
    fireEvent.click(screen.getByRole("button", { name: /^slim$/i }));

    fireEvent.click(screen.getByRole("button", { name: /upload 1 product/i }));

    await waitFor(() => expect(apiFetchMock).toHaveBeenCalledWith("/supplier/products/bulk-upload", expect.anything()));

    const uploadCall = apiFetchMock.mock.calls.find(([path]) => path === "/supplier/products/bulk-upload");
    expect(uploadCall).toBeDefined();
    const [, requestInit] = uploadCall!;
    const formData = requestInit?.body as FormData;
    const productsPayload = JSON.parse(String(formData.get("products_json")));
    const uploadedFiles = formData.getAll("images") as File[];

    expect(productsPayload[0]).toMatchObject({
      name: "Variant Video Product",
      price: 149.99,
      currency: "AED",
    });
    expect(productsPayload[0].variants).toEqual([
      expect.objectContaining({
        title: "Black / 128 GB / Slim",
        size: "128 GB",
        color: "Black",
        attributes_json: { shape: "Slim" },
        product_code: expect.stringMatching(/^PRD-GEN-VARIA-128G-[A-Z0-9]{6}-01$/),
        price: 149.99,
        stock: 8,
      }),
    ]);
    expect(productsPayload[0].variants[0].sku).toBeUndefined();
    expect(productsPayload[0].variants[0].barcode).toBeUndefined();
    expect(uploadedFiles.map((file) => file.name)).toContain("p0_video.mp4");
  });

  it("blocks apparel uploads until category-specific requirements are present", async () => {
    await renderPage();

    fireEvent.change(screen.getByPlaceholderText(/wireless bluetooth earphones/i), { target: { value: "Fashion Upload" } });
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "59.99" } });
    fireEvent.click(screen.getByRole("combobox", { name: /^category$/i }));
    fireEvent.change(screen.getByPlaceholderText(/search categories/i), { target: { value: "fashion" } });
    fireEvent.click(screen.getByRole("option", { name: "Fashion" }));
    fireEvent.click(screen.getByRole("button", { name: /upload 1 product/i }));

    await waitFor(() => expect(addToastMock).toHaveBeenCalledWith("Fashion Upload: Apparel products require material composition", "error"));
    expect(screen.getByText(/fix before upload: apparel products require material composition/i)).toBeInTheDocument();
    expect(screen.getByText(/draft 1 needs attention: apparel products require material composition/i)).toBeInTheDocument();
    expect(screen.queryAllByLabelText(/material/i)).toHaveLength(0);
    expect(apiFetchMock).not.toHaveBeenCalledWith("/supplier/products/bulk-upload", expect.anything());
  });
});


