import React from "react";
import { render, screen } from "@testing-library/react";
import { usePathname } from "next/navigation";
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(() => "/products"),
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => {
    const store = { t: (key: string) => key };
    return selector ? selector(store) : store;
  },
}));

jest.mock("@/components/NewsletterSignup", () => function NewsletterSignupMock() {
  return <div data-testid="newsletter-signup" />;
});

import Footer from "@/components/Footer";

const mockUsePathname = usePathname as jest.Mock;

describe("Footer", () => {
  it("renders supplier and logistics partner entry points", () => {
    mockUsePathname.mockReturnValue("/products");
    render(<Footer />);

    expect(screen.getByRole("link", { name: /becomelogisticspartner/i })).toHaveAttribute(
      "href",
      "/logistics-partner/login"
    );
    expect(screen.getByRole("link", { name: /becomesupplier/i })).toHaveAttribute(
      "href",
      "/supplier/register"
    );
  });

  it("hides footer on supplier auth and panel routes", () => {
    mockUsePathname.mockReturnValue("/supplier/dashboard");

    const { container } = render(<Footer />);

    expect(container.firstChild).toBeNull();
  });

  it("hides footer on logistics partner routes", () => {
    mockUsePathname.mockReturnValue("/logistics-partner/login");

    const { container } = render(<Footer />);

    expect(container.firstChild).toBeNull();
  });

  it("has no obvious accessibility violations when visible", async () => {
    mockUsePathname.mockReturnValue("/products");
    const { container } = render(<Footer />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});


