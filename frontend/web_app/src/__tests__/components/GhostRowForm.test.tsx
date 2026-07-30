/**
 * Tests for GhostRowForm — Quick-add country form with auto-populate
 * Tests form rendering, auto-populate search, form submission, and edge cases.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import GhostRowForm from "@/components/country/GhostRowForm";

// ── Mocks ────────────────────────────────────────────────────────────────────
const mockAddToast = jest.fn();
jest.mock("@/lib/toastStore", () => ({
  useToastStore: () => mockAddToast,
}));

const mockApiFetch = jest.fn();
const mockParseJsonResponse = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  parseJsonResponse: (...args: any[]) => mockParseJsonResponse(...args),
}));

const mockOnCountryCreated = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
});

// Helper to open the form
function openForm() {
  render(<GhostRowForm onCountryCreated={mockOnCountryCreated} />);
  const addBtn = screen.getByRole("button", { name: /add country/i });
  fireEvent.click(addBtn);
  return addBtn;
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("GhostRowForm", () => {
  it("renders Add Country button initially", () => {
    render(<GhostRowForm />);
    expect(screen.getByRole("button", { name: /add country/i })).toBeInTheDocument();
  });

  it("opens form when Add Country is clicked", () => {
    openForm();
    expect(screen.getByLabelText(/country code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/country name/i)).toBeInTheDocument();
  });

  it("shows auto-populate search input when form is open", () => {
    openForm();
    expect(screen.getByTestId("auto-populate-search-input")).toBeInTheDocument();
  });

  it("hides form when Cancel is clicked", () => {
    openForm();
    const cancelBtn = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelBtn);
    expect(screen.queryByLabelText(/country code/i)).not.toBeInTheDocument();
  });

  it("requires code and name fields", () => {
    openForm();
    const codeInput = screen.getByLabelText(/country code/i);
    const nameInput = screen.getByLabelText(/country name/i);
    expect(codeInput).toBeRequired();
    expect(nameInput).toBeRequired();
  });

  it("calls apiFetch on auto-populate search", async () => {
    mockApiFetch.mockResolvedValueOnce({ ok: true });
    mockParseJsonResponse.mockResolvedValueOnce({
      code: "SA",
      name: "Saudi Arabia",
      currency: "SAR",
      currency_symbol: "﷼",
      phone_code: "+966",
      language: "ar",
      timezone: "UTC+03:00",
    });

    openForm();
    const searchInput = screen.getByTestId("auto-populate-search-input");
    fireEvent.change(searchInput, { target: { value: "Saudi Arabia" } });

    const searchBtn = screen.getByRole("button", { name: /search|auto-populate/i });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByDisplayValue("SA")).toBeInTheDocument();
    });
    expect(screen.getByTestId("ghost-name-input")).toHaveValue("Saudi Arabia");
  });

  it("shows toast on failed auto-populate", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Auto-populate failed"));

    openForm();
    const searchInput = screen.getByTestId("auto-populate-search-input");
    fireEvent.change(searchInput, { target: { value: "Unknown" } });

    const searchBtn = screen.getByRole("button", { name: /search|auto-populate/i });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith(
        expect.stringContaining("failed"),
        "error"
      );
    });
  });

  it("shows warning for empty auto-populate search", () => {
    openForm();
    const searchBtn = screen.getByRole("button", { name: /search|auto-populate/i });
    fireEvent.click(searchBtn);

    expect(mockAddToast).toHaveBeenCalledWith(
      expect.stringContaining("Enter a country"),
      "warning"
    );
  });

  it("auto-populate fills form fields from response", async () => {
    mockApiFetch.mockResolvedValueOnce({ ok: true });
    mockParseJsonResponse.mockResolvedValueOnce({
      code: "AE",
      name: "United Arab Emirates",
      currency: "AED",
      currency_symbol: "د.إ",
      phone_code: "+971",
      language: "ar",
      timezone: "UTC+04:00",
    });

    openForm();
    const searchInput = screen.getByTestId("auto-populate-search-input");
    fireEvent.change(searchInput, { target: { value: "UAE" } });

    const searchBtn = screen.getByRole("button", { name: /search|auto-populate/i });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(screen.getByDisplayValue("AE")).toBeInTheDocument();
      expect(screen.getByDisplayValue("United Arab Emirates")).toBeInTheDocument();
    });
  });

  it("calls onCountryCreated after successful creation", async () => {
    mockApiFetch.mockResolvedValueOnce({ ok: true });
    mockParseJsonResponse.mockResolvedValueOnce({ status: "created", country_code: "EG" });

    openForm();
    const codeInput = screen.getByLabelText(/country code/i);
    fireEvent.change(codeInput, { target: { value: "EG" } });
    const nameInput = screen.getByLabelText(/country name/i);
    fireEvent.change(nameInput, { target: { value: "Egypt" } });

    const saveBtn = screen.getByRole("button", { name: /save|create/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(mockOnCountryCreated).toHaveBeenCalled();
    });
  });

  it("disables search button while searching", async () => {
    mockApiFetch.mockImplementationOnce(() => new Promise(() => {})); // Never resolves

    openForm();
    const searchInput = screen.getByTestId("auto-populate-search-input");
    fireEvent.change(searchInput, { target: { value: "Test" } });

    const searchBtn = screen.getByRole("button", { name: /search|auto-populate/i });
    fireEvent.click(searchBtn);

    expect(searchBtn).toBeDisabled();
  });

  it("code input auto-uppercases", () => {
    openForm();
    const codeInput = screen.getByLabelText(/country code/i) as HTMLInputElement;
    fireEvent.change(codeInput, { target: { value: "in" } });
    expect(codeInput.value).toBe("IN");
  });
});

describe("GhostRowForm with no onCountryCreated callback", () => {
  it("renders without crashing", () => {
    render(<GhostRowForm />);
    expect(screen.getByRole("button", { name: /add country/i })).toBeInTheDocument();
  });
});