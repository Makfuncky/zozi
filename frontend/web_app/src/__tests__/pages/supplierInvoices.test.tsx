const mockRedirect = jest.fn();

jest.mock("next/navigation", () => ({
  redirect: (...args: unknown[]) => mockRedirect(...args),
}));

import SupplierInvoicesPage from "@/app/supplier/invoices/page";

describe("SupplierInvoicesPage redirect", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("redirects the retired supplier invoice route into the payouts invoice view", () => {
    SupplierInvoicesPage();
    expect(mockRedirect).toHaveBeenCalledWith("/supplier/payouts?view=invoices");
  });
});


