import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();

jest.mock("@/lib/api", () => ({
  API_URL: "http://localhost:8000",
  getAccessToken: jest.fn(() => null),
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/logger", () => ({
  logger: {
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() }),
  useParams: () => ({ id: "9" }),
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: { id: 1, username: "amina", email: "amina@zozi.test", role: "customer" },
    isLoggedIn: true,
    isLoading: false,
    logout: jest.fn(),
  }),
}));

import LogisticsPartnerDetailPage from "@/app/logistics-partners/[id]/page";
import { logger } from "@/lib/logger";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Logistics partner detail page failure logging (Law 59)", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
    mockPush.mockReset();
    (logger.debug as jest.Mock).mockReset();
    (logger.info as jest.Mock).mockReset();
    (logger.warn as jest.Mock).mockReset();
    (logger.error as jest.Mock).mockReset();
    window.history.pushState({}, "", "/");
  });

  it("still renders the partner detail after a successful load", async () => {
    mockApiFetch.mockResolvedValueOnce(okJson({
      id: 9,
      name: "FastShip Logistics",
      code: "FASTSHIP",
      verification_status: "approved",
      bio: "City-wide deliveries.",
      service_areas: [],
    }));

    render(<LogisticsPartnerDetailPage />);

    expect(await screen.findByRole("heading", { name: "FastShip Logistics" })).toBeInTheDocument();
    expect(logger.error).not.toHaveBeenCalled();
    expect(logger.warn).not.toHaveBeenCalled();
  });

  it("logs a rejected partner detail fetch and still shows the error state", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("network down"));

    render(<LogisticsPartnerDetailPage />);

    expect(await screen.findByText("Logistics partner unavailable")).toBeInTheDocument();
    expect(screen.getByText("network down")).toBeInTheDocument();

    await waitFor(() => {
      expect(logger.error).toHaveBeenCalledTimes(1);
    });
    expect(logger.error).toHaveBeenCalledWith(
      expect.stringContaining("[logistics-partner-detail]"),
      expect.any(Error),
    );
    expect(logger.error.mock.calls[0][1].message).toBe("network down");
  });

  it("logs a non-JSON error body instead of swallowing the parse failure", async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.reject(new SyntaxError("Unexpected token < in JSON")),
    });

    render(<LogisticsPartnerDetailPage />);

    expect(await screen.findByText("Logistics partner unavailable")).toBeInTheDocument();
    expect(screen.getByText("Could not load this logistics partner.")).toBeInTheDocument();

    await waitFor(() => {
      expect(logger.warn).toHaveBeenCalledTimes(1);
    });
    expect(logger.warn).toHaveBeenCalledWith(
      expect.stringContaining("[logistics-partner-detail]"),
      expect.any(SyntaxError),
    );

    expect(logger.error).toHaveBeenCalledTimes(1);
    expect(logger.error).toHaveBeenCalledWith(
      expect.stringContaining("[logistics-partner-detail]"),
      expect.any(Error),
    );
  });

  it("logs an HTTP error response that carries a backend detail message", async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Partner is not approved yet." }),
    });

    render(<LogisticsPartnerDetailPage />);

    expect(await screen.findByText("Partner is not approved yet.")).toBeInTheDocument();

    await waitFor(() => {
      expect(logger.error).toHaveBeenCalledTimes(1);
    });
    expect(logger.error).toHaveBeenCalledWith(
      expect.stringContaining("[logistics-partner-detail]"),
      expect.objectContaining({ message: "Partner is not approved yet." }),
    );
  });
});
