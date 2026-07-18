import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import ApprovalActionModal, { type ResourceAction } from "@/components/ApprovalActionModal";

const okJson = (data: unknown) =>
  new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

const mockApiFetch = jest.fn(() =>
  Promise.resolve(
    new Response("{}", {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  )
);
const mockAddToast = jest.fn();

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  API_URL: "http://localhost:8000",
  getAccessToken: () => "fake-token",
}));

jest.mock("@/lib/approvalMatrixApi", () => ({
  getApprovalMatrixRules: jest.fn(),
  getUserApprovalChain: jest.fn(),
}));

const mockGetApprovalMatrixRules = jest.requireMock("@/lib/approvalMatrixApi").getApprovalMatrixRules as jest.Mock;
const mockGetUserApprovalChain = jest.requireMock("@/lib/approvalMatrixApi").getUserApprovalChain as jest.Mock;

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: any) => selector({ addToast: mockAddToast }),
}));

jest.mock("@/components/PanelPage", () => ({
  PanelContent: ({ children }: any) => <div>{children}</div>,
  PanelTabs: ({ items, value, onChange }: any) => (
    <div data-testid="panel-tabs">
      {(items || []).map((t: any) => (
        <button key={t.key} onClick={() => onChange?.(t.key)} aria-current={t.key === value ? "page" : undefined}>
          {t.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock("@shared/components/EnterpriseDataTable", () => ({
  EnterpriseDataTable: ({ rows, columns }: any) => (
    <table data-testid="enterprise-table">
      <tbody>
        {(rows || []).map((row: any, i: number) => (
          <tr key={i}>
            {(columns || []).map((col: any, j: number) => (
              <td key={j}>{typeof col.render === "function" ? col.render(row) : String(row[col.key] ?? "")}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  ),
}));

const ME_RESPONSE = {
  id: 5,
  username: "approver",
  role: "admin",
  authority_level: 7,
};

const RULES_RESPONSE = {
  rules: {
    payout: {
      min_authority_level: 5,
      department: "Finance",
      org_unit_required: true,
      description: "High-value payouts require Finance approval.",
    },
  },
};

const CHAIN_RESPONSE = {
  user_id: 5,
  resource_type: "payout",
  chain: [
    { user_id: 5, username: "approver", role: "admin", authority_level: 7, distance: 1, org_unit_name: "HQ" },
    { user_id: 9, username: "final", role: "super_admin", authority_level: 10, distance: 2, org_unit_name: "HQ" },
  ],
  count: 2,
};

const ELIGIBILITY_RESPONSE = {
  can_approve: true,
  user_id: 5,
  resource_type: "payout",
  authority_level: 7,
  min_authority_level: 5,
};

function renderModal(props?: Partial<Parameters<typeof ApprovalActionModal>[0]>) {
  const defaultProps: Parameters<typeof ApprovalActionModal>[0] = {
    isOpen: true,
    onClose: jest.fn(),
    onConfirm: jest.fn().mockResolvedValue(undefined),
    resourceType: "payout",
    resourceLabel: "PO-1001",
    action: "verify" as ResourceAction,
  };

  return render(<ApprovalActionModal {...defaultProps} {...props} />);
}

describe("ApprovalActionModal", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/auth/me") return Promise.resolve(okJson(ME_RESPONSE));
      if (url.includes("/approval-matrix/rules")) return Promise.resolve(okJson(RULES_RESPONSE));
      if (url.includes("/approval-matrix/check")) return Promise.resolve(okJson(ELIGIBILITY_RESPONSE));
      if (url.includes("/authority-level")) return Promise.resolve(okJson({}));
      if (url.includes("/approval-chain")) return Promise.resolve(okJson(CHAIN_RESPONSE));
      return Promise.resolve(okJson({}));
    });

    mockGetApprovalMatrixRules.mockReset();
    mockGetApprovalMatrixRules.mockResolvedValue(RULES_RESPONSE);

    mockGetUserApprovalChain.mockReset();
    mockGetUserApprovalChain.mockResolvedValue(CHAIN_RESPONSE);

    mockAddToast.mockReset();
  });

  it("does not render when closed", () => {
    renderModal({ isOpen: false });
    expect(screen.queryByText(/Verify Payout/)).not.toBeInTheDocument();
  });

  it("renders the modal header with action and resource label", () => {
    renderModal();
    expect(screen.getByText(/Verify Payout PO-1001/)).toBeInTheDocument();
  });

  it("shows preview UI with note and status fields", async () => {
    renderModal();
    await waitFor(() => expect(screen.getByLabelText(/Note/)).toBeInTheDocument());
    expect(screen.getByLabelText(/Status/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Verify Payout/ })).toBeEnabled();
  });

  it("switches to rules tab and shows minimum authority level", async () => {
    renderModal();

    await waitFor(() => screen.getByTestId("panel-tabs"));

    const rulesTab = screen.getByRole("button", { name: /^Rule$/ });
    await act(async () => {
      fireEvent.click(rulesTab);
    });

    await waitFor(() =>
      expect(screen.getByText(/Minimum authority level:/)).toBeInTheDocument()
    );
    expect(screen.getByText("Finance")).toBeInTheDocument();
  });

  it("switches to chain tab and shows approver steps", async () => {
    renderModal();

    await waitFor(() => screen.getByTestId("panel-tabs"));

    const chainTab = screen.getByRole("button", { name: /Approval Chain/ });
    await act(async () => {
      fireEvent.click(chainTab);
    });

    await waitFor(() =>
      expect(screen.getByText("2 step(s) in chain")).toBeInTheDocument()
    );
    expect(screen.getByText("approver")).toBeInTheDocument();
    expect(screen.getByText("final")).toBeInTheDocument();
  });

  it("calls onConfirm with note and status when confirm is clicked", async () => {
    const onConfirm = jest.fn().mockResolvedValue(undefined);
    renderModal({ onConfirm });

    const noteField = screen.getByLabelText(/Note/);
    fireEvent.change(noteField, { target: { value: "All good" } });

    const confirmBtn = screen.getByRole("button", { name: /Verify Payout/ });
    fireEvent.click(confirmBtn);

    await waitFor(() =>
      expect(onConfirm).toHaveBeenCalledWith({ note: "All good", status: "processing" })
    );
  });

  it("disables confirm button and shows block notice when cannot approve", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/auth/me") return Promise.resolve(okJson(ME_RESPONSE));
      if (url.includes("/approval-matrix/rules")) return Promise.resolve(okJson(RULES_RESPONSE));
      if (url.includes("/approval-matrix/check")) {
        return Promise.resolve(
          okJson({
            can_approve: false,
            reason: "Level too low",
            authority_level: 7,
            min_authority_level: 9,
          })
        );
      }
      if (url.includes("/authority-level")) return Promise.resolve(okJson({}));
      return Promise.resolve(okJson({}));
    });

    renderModal();

    await waitFor(() =>
      expect(screen.getByText(/Requires higher authority/)).toBeInTheDocument()
    );

    const confirmBtn = screen.getByRole("button", { name: /Cannot verify payout/ });
    expect(confirmBtn).toBeDisabled();
  });

  it("shows an error toast when onConfirm throws", async () => {
    const onConfirm = jest.fn().mockRejectedValue(new Error("Server error"));
    renderModal({ onConfirm });

    const confirmBtn = screen.getByRole("button", { name: /Verify Payout/ });
    fireEvent.click(confirmBtn);

    await waitFor(() =>
      expect(mockAddToast).toHaveBeenCalledWith("Server error", "error")
    );
  });

  it("closes the modal when Close is clicked", async () => {
    const onClose = jest.fn();
    renderModal({ onClose });

    const closeBtn = screen.getByRole("button", { name: /Close/ });
    fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalled();
  });
});
