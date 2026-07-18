/**
 * Tests for web_app/src/components/Header.tsx
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { usePathname } from "next/navigation";
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

// ── Mock all external dependencies ───────────────────────────────────────────

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(() => "/"),
  useRouter: jest.fn(() => ({ push: jest.fn(), replace: jest.fn() })),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...p }: any) => <div {...p}>{children}</div>,
    span: ({ children, ...p }: any) => <span {...p}>{children}</span>,
    header: ({ children, ...p }: any) => <header {...p}>{children}</header>,
    nav: ({ children, ...p }: any) => <nav {...p}>{children}</nav>,
    button: ({ children, ...p }: any) => <button {...p}>{children}</button>,
    a: ({ children, ...p }: any) => <a {...p}>{children}</a>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));

const mockLogout = jest.fn();
let mockIsLoggedIn = false;
let mockUser: any = null;
const mockCartStore = {
  getItemCount: () => 3,
  ids: [],
  items: [],
  total: 0,
  initialize: jest.fn(),
};
const mockWishlistStore = {
  ids: ["a", "b"],
  items: [],
  initialize: jest.fn(),
};

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    logout: mockLogout,
  }),
}));

jest.mock("@/lib/cartStore", () => ({
  useCartStore: Object.assign(
    (selector: any) => (selector ? selector(mockCartStore) : mockCartStore),
    { getState: () => mockCartStore }
  ),
}));

jest.mock("@/lib/wishlistStore", () => ({
  useWishlistStore: Object.assign(
    (selector: any) => (selector ? selector(mockWishlistStore) : mockWishlistStore),
    { getState: () => mockWishlistStore }
  ),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn().mockResolvedValue({ ok: false }),
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: jest.fn(() => null),
  isNotificationRealtimeMessage: jest.fn(() => false),
}));

jest.mock("@shared/realtime", () => ({
  createRealtimeRefreshScheduler: (refresh: () => void | Promise<void>) => ({
    cancel: jest.fn(),
    trigger: () => {
      void refresh();
    },
  }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => {
    const store = { locale: "en", t: (k: string) => k, setLocale: jest.fn(), syncLocaleToServer: jest.fn() };
    return selector ? selector(store) : store;
  },
}));

jest.mock("@/lib/authModalStore", () => ({
  useAuthModalStore: (selector: any) => {
    const store = { open: jest.fn() };
    return selector ? selector(store) : store;
  },
}));

jest.mock("@/components/ThemeToggle", () => {
  function MockThemeToggle() {
    return <button aria-label="theme-toggle">T</button>;
  }

  return MockThemeToggle;
});

jest.mock("@/components/Logo", () => function LogoMock() {
  return <span data-testid="logo">ZOZI</span>;
});

// ── Tests ─────────────────────────────────────────────────────────────────────

import Header from "@/components/Header";

const mockUsePathname = usePathname as jest.Mock;

afterEach(() => {
  mockIsLoggedIn = false;
  mockUser = null;
  mockCartStore.initialize.mockClear();
  mockWishlistStore.initialize.mockClear();
  jest.clearAllMocks();
});

describe("Header — guest state", () => {
  it("renders without crashing on /", () => {
    render(<Header />);
    // header element present
    expect(document.querySelector("header")).not.toBeNull();
  });

  it("shows cart badge with item count", () => {
    render(<Header />);
    // Cart count 3 should appear somewhere in the header
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("keeps the shared header visible on supplier routes", () => {
    mockUsePathname.mockReturnValue("/supplier/dashboard");

    render(<Header />);
    expect(document.querySelector("header")).not.toBeNull();
  });
});

describe("Header — logged-in customer", () => {
  beforeEach(() => {
    mockIsLoggedIn = true;
    mockUser = { id: 1, username: "Alice", email: "alice@zozi.com", role: "customer" };
    mockUsePathname.mockReturnValue("/");
  });

  it("renders without crashing when logged in", () => {
    render(<Header />);
    expect(document.querySelector("header")).not.toBeNull();
  });

  it("has no obvious accessibility violations in logged-in state", async () => {
    const { container } = render(<Header />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});


