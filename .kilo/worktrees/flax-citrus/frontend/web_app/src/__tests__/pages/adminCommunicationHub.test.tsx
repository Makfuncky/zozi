import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { isAdminStaffRole, canAccessAdminEmailManagement } from "@shared/adminPermissions";

const mockPush = jest.fn();
const mockReplace = jest.fn();
let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockAuthLoading,
    logout: jest.fn(),
  }),
}));

jest.mock("@shared/adminPermissions", () => ({
  isAdminStaffRole: jest.fn(() => true),
  canAccessAdminEmailManagement: jest.fn(() => true),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children, title }: any) => (
    <div data-testid="admin-layout">
      {title && <h1>{title}</h1>}
      {children}
    </div>
  ),
}));

jest.mock("@/components/comms/CommandPalette", () => ({
  __esModule: true,
  default: () => <div data-testid="command-palette">⌘K</div>,
}));

jest.mock("@/components/comms/StatusDock", () => ({
  __esModule: true,
  default: () => <div data-testid="status-dock">Connected</div>,
}));

import CommunicationPage from "@/app/admin/communication/page";
import AdminVideoPage from "@/app/admin/video/page";
import AdminChatPage from "@/app/admin/chat/page";
import AdminEmailDashboard from "@/app/admin/email/page";

describe("Unified Communication hub (conversation deck)", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin", permissions: ["email.manage"] };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("renders the conversation deck with command palette and status dock", async () => {
    render(<CommunicationPage />);
    await waitFor(() => {
      expect(screen.getByText("Communication")).toBeInTheDocument();
    });
    expect(screen.getByTestId("command-palette")).toBeInTheDocument();
    expect(screen.getByTestId("status-dock")).toBeInTheDocument();
  });

  it("shows the welcome splash when no thread is selected", async () => {
    render(<CommunicationPage />);
    await waitFor(() => {
      expect(screen.getByText("Communication Hub")).toBeInTheDocument();
    });
    expect(screen.getByText(/Select a conversation/)).toBeInTheDocument();
  });

  it("shows the modality rail with inbox/direct/groups/channels/email/meet", async () => {
    render(<CommunicationPage />);
    await waitFor(() => {
      expect(screen.getByText("Unified Inbox")).toBeInTheDocument();
    });
    expect(screen.getByText("Direct")).toBeInTheDocument();
    expect(screen.getByText("Channels")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Meet")).toBeInTheDocument();
  });

  it("renders the thread list with sample conversations", async () => {
    render(<CommunicationPage />);
    await waitFor(() => {
      expect(screen.getByText("Aisha Al-Mamari")).toBeInTheDocument();
    });
    expect(screen.getByText("#oman-sales")).toBeInTheDocument();
    expect(screen.getByText("Invoice #INV-2024-0891")).toBeInTheDocument();
  });
});

describe("Communication redirect stubs", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin", permissions: ["email.manage"] };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("redirects /admin/video to the video tab of the hub for staff", async () => {
    render(<AdminVideoPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/communication?tab=video");
    });
  });

  it("redirects /admin/chat to the chat tab of the hub for staff", async () => {
    render(<AdminChatPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/communication?tab=chat");
    });
  });

  it("redirects /admin/email to the email tab of the hub for staff", async () => {
    render(<AdminEmailDashboard />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/communication?tab=email");
    });
  });

  it("redirects unauthenticated /admin/video to login", async () => {
    mockIsLoggedIn = false;
    mockUser = null;
    (isAdminStaffRole as unknown as jest.Mock).mockReturnValue(false);
    render(<AdminVideoPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/login");
    });
  });

  it("redirects an email page visitor without email permission to login", async () => {
    (canAccessAdminEmailManagement as unknown as jest.Mock).mockReturnValue(false);
    mockUser = { id: 2, username: "support", role: "support", permissions: [] };
    render(<AdminEmailDashboard />);
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/login");
    });
  });
});
