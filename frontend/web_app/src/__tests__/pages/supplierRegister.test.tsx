import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: function NextLinkMock({ children, href }: any) { return <a href={href}>{children}</a>; },
}));

jest.mock("@/components/Logo", () => function LogoMock() { return <div data-testid="logo" />; });

jest.mock("@/lib/api", () => ({
  getErrorMessage: jest.fn((data) => data?.detail || ""),
}));

jest.mock("framer-motion", () => ({
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

import SupplierRegisterPage from "@/app/supplier/register/page";

describe("SupplierRegisterPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("preserves typed account data and disables browser text correction on structured fields", () => {
    render(<SupplierRegisterPage />);

    const username = screen.getByPlaceholderText(/choose a username/i);
    const email = screen.getByPlaceholderText(/you@yourbusiness.com/i);
    const [password, confirm] = screen.getAllByPlaceholderText(/••••••••/i);

    fireEvent.change(username, { target: { value: "supplier_name" } });
    fireEvent.change(email, { target: { value: "seller@example.com" } });
    fireEvent.change(password, { target: { value: "SellerPass123!" } });
    fireEvent.change(confirm, { target: { value: "SellerPass123!" } });

    expect(username).toHaveValue("supplier_name");
    expect(email).toHaveValue("seller@example.com");
    expect(username).toHaveAttribute("autocapitalize", "none");
    expect(username).toHaveAttribute("autocorrect", "off");
    expect(email).toHaveAttribute("autocapitalize", "none");

    fireEvent.click(screen.getByRole("button", { name: /^next/i }));

    expect(screen.getByPlaceholderText(/your business or brand name/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /back/i }));

    expect(screen.getByPlaceholderText(/choose a username/i)).toHaveValue("supplier_name");
    expect(screen.getByPlaceholderText(/you@yourbusiness.com/i)).toHaveValue("seller@example.com");
  });
});


