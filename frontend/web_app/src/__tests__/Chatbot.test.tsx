/**
 * Unit tests for web_app Chatbot component
 */
import React, { act } from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ── Mocks ──────────────────────────────────────────────────────────────────────

// Mock framer-motion (not tested here)
jest.mock("framer-motion", () => ({
  motion: {
    button: ({ children, whileHover: _whileHover, whileTap: _whileTap, ...props }: any) => <button {...props}>{children}</button>,
    div: ({ children, initial: _initial, animate: _animate, exit: _exit, transition: _transition, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock next/link and next/image
jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, onClick, ...props }: any) => (
    <a
      href={href}
      onClick={(event) => {
        event.preventDefault();
        onClick?.(event);
      }}
      {...props}
    >
      {children}
    </a>
  ),
}));
jest.mock("next/image", () => ({ __esModule: true, default: ({ src, alt }: any) => <img src={src} alt={alt} /> }));
const mockUsePathname = jest.fn(() => "/");
const mockUseSearchParams = jest.fn(() => new URLSearchParams());
jest.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
  useSearchParams: () => mockUseSearchParams(),
}));

// Mock stores
jest.mock("@/lib/localeStore", () => {
  const translate = (key: string) => {
    const map: Record<string, string> = {
      chatbotGreeting: "Hello! How can I help?",
      chatbotTitle: "ZOZI Assistant",
      chatbotOnline: "Online",
      chatbotPlaceholder: "Ask me anything…",
      chatbotToggle: "Open chatbot",
      chatbotUnknownReply: "I'm not sure about that.",
      chatbotReturnReply: "Return windows vary by product and start after delivery. Check product details or your order page for eligibility.",
      chatbotNoResults: "No results found.",
      chatbotResultsFoundOne: "Found one product.",
      chatbotResultsFoundMany: "Found {{count}} products.",
      sendMessage: "Send",
    };
    return map[key] ?? key;
  };

  const useLocaleStore: any = (selector: any) => selector({ t: translate });
  useLocaleStore.getState = () => ({ t: translate });

  return { useLocaleStore };
});

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) =>
    selector({ format: (price: number) => `AED ${price.toFixed(2)}` }),
}));

const apiFetchMock = jest.fn();
jest.mock("@/lib/api", () => ({ apiFetch: (...args: any[]) => apiFetchMock(...args) }));
jest.mock("@/lib/utils", () => ({
  PLACEHOLDER_IMAGE_PATH: "/placeholder.svg",
  resolveImage: (url?: string) => url ?? "/placeholder.svg",
}));
jest.mock("@/lib/i18n", () => ({}));
jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (text?: string | null) => text ?? "",
  useTranslateTexts: (texts: Array<string | null | undefined>) => texts.map((text) => text ?? ""),
}));

// ── Tests ────────────────────────────────────────────────────────────────────

import Chatbot from "@/components/Chatbot";

describe("Chatbot", () => {
  beforeEach(() => {
    Object.defineProperty(window.HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: jest.fn(),
    });
    apiFetchMock.mockReset();
    mockUsePathname.mockReset();
    mockUseSearchParams.mockReset();
    mockUsePathname.mockReturnValue("/");
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    apiFetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ reply: "Return windows vary by product and start after delivery. Check product details or your order page for eligibility.", intent: "return", products: [], session_id: "s2" }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders the toggle button", () => {
    render(<Chatbot />);
    expect(screen.getByLabelText("Open chatbot")).toBeTruthy();
  });

  it("opens the chat window on toggle click", () => {
    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));
    expect(screen.getByText("ZOZI Assistant")).toBeTruthy();
    expect(screen.getByText("Hello! How can I help?")).toBeTruthy();
  });

  it("closes the chat window on second toggle click", () => {
    render(<Chatbot />);
    const toggle = screen.getByLabelText("Open chatbot");
    fireEvent.click(toggle);
    fireEvent.click(toggle);
    expect(screen.queryByText("ZOZI Assistant")).toBeNull();
  });

  it("sends a user message and shows it in the chat", async () => {
    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "What is your return policy?" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("What is your return policy?")).toBeTruthy();
    });

    // Flush pending bot-reply timer (700ms) to prevent React.act() warnings
    await act(async () => {
      await new Promise((r) => setTimeout(r, 800));
    });
  });

  it("shows backend reply to non-product message", async () => {
    apiFetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        reply: "Return windows vary by product and start after delivery. Check product details or your order page for eligibility.",
        intent: "return",
        products: [],
        session_id: "s2",
      }),
    });

    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "How do I return an item?" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("Return windows vary by product and start after delivery. Check product details or your order page for eligibility.")).toBeTruthy();
    }, { timeout: 2000 });

    expect(apiFetchMock).toHaveBeenCalledWith(
      "/chatbot/message",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("falls back to local replies if the chatbot API fails", async () => {
    apiFetchMock.mockResolvedValueOnce({
      ok: false,
      json: async () => ({}),
    });

    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "How do I return an item?" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("Return windows vary by product and start after delivery. Check product details or your order page for eligibility.")).toBeTruthy();
    });
  });

  it("falls back to a greeting reply when a greeting request fails", async () => {
    apiFetchMock.mockResolvedValueOnce({
      ok: false,
      json: async () => ({}),
    });

    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "hey" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getAllByText("Hello! How can I help?").length).toBeGreaterThan(0);
    });
  });

  it("calls chatbot API for product intent messages", async () => {
    apiFetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ reply: "I found 1 in-stock phone option.", intent: "product_search", products: [], session_id: "s1" }),
    });

    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "show me phones" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/chatbot/message",
        expect.objectContaining({ method: "POST" })
      );
    });

    // Allow post-fetch state updates (addBotMessage) to complete inside act()
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });
  });

  it("passes supplier scope query to chatbot API", async () => {
    mockUsePathname.mockReturnValue("/chatbot");
    mockUseSearchParams.mockReturnValue(new URLSearchParams("supplier=14"));

    apiFetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        reply: "I found supplier-specific options.",
        intent: "product_search",
        products: [],
        session_id: "supplier-session",
      }),
    });

    render(<Chatbot />);

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "show me top products" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/chatbot/message?supplier_id=14",
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  it("renders richer product chips and records product clicks", async () => {
    apiFetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          reply: "These match your search.",
          intent: "product_search",
          session_id: "chat-session-1",
          result_mode: "exact",
          suggested_prompts: ["Only show size XL", "Show top-rated options"],
          products: [
            {
              id: 12,
              name: "Nike Performance Black T-Shirt",
              price: 79,
              rating: 4.9,
              image_url: "/img.jpg",
              category: "Fashion",
              brand: "Nike",
              color: "Black",
              sizes: ["M", "L", "XL"],
            },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          reply: "Filtering to XL.",
          intent: "product_search",
          session_id: "chat-session-1",
          result_mode: "none",
          suggested_prompts: ["Show cheaper alternatives"],
          products: [],
        }),
      });

    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "Nike black t-shirt in XL" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("Nike")).toBeTruthy();
      expect(screen.getByText("Fashion")).toBeTruthy();
      expect(screen.getByText("Black")).toBeTruthy();
      expect(screen.getByText("Sizes: M, L, XL")).toBeTruthy();
      expect(screen.getByText("4.9 star")).toBeTruthy();
      expect(screen.getByRole("button", { name: "Only show size XL" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Only show size XL" }));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenNthCalledWith(
        2,
        "/chatbot/message",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ message: "Only show size XL", session_id: "chat-session-1" }),
        })
      );
    });

    fireEvent.click(screen.getByText("Nike Performance Black T-Shirt"));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenLastCalledWith(
        "/chatbot/record-click/12",
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  it("shows a close matches label for substitute results", async () => {
    apiFetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        reply: "I found close alternatives.",
        intent: "product_search",
        session_id: "close-session-1",
        result_mode: "close",
        suggested_prompts: [],
        products: [
          {
            id: 77,
            name: "Studio Black Bralette",
            price: 119,
            rating: 4.5,
            image_url: "/img.jpg",
            category: "Fashion",
            brand: "Studio Fit",
            color: "Black",
            sizes: ["S", "M"],
          },
        ],
      }),
    });

    render(<Chatbot />);
    fireEvent.click(screen.getByLabelText("Open chatbot"));

    const input = screen.getByPlaceholderText("Ask me anything…");
    fireEvent.change(input, { target: { value: "show me black bra" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("Close matches")).toBeTruthy();
      expect(screen.getByText("Studio Black Bralette")).toBeTruthy();
    });
  });
});


