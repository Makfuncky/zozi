import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
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

jest.mock("@/components/PanelPage", () => ({
  PanelContent: ({ children }: any) => <div data-testid="panel-content">{children}</div>,
  PanelTabs: ({ items, value, onChange }: any) => (
    <div role="tablist">
      {items.map((it: any) => (
        <button
          key={it.key}
          role="tab"
          aria-selected={value === it.key}
          data-testid={`tab-${it.key}`}
          onClick={() => onChange(it.key)}
        >
          {it.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock("@/components/admin/AdminEmailPanel", () => ({ __esModule: true, default: () => <div>ADMIN EMAIL PANEL</div> }));
jest.mock("@/components/admin/AdminChatPanel", () => ({ __esModule: true, default: () => <div>ADMIN CHAT PANEL</div> }));
jest.mock("@/components/admin/AdminVideoPanel", () => ({ __esModule: true, default: () => <div>ADMIN VIDEO PANEL</div> }));

import CommunicationPage from "@/app/admin/communication/page";
import AdminVideoPage from "@/app/admin/video/page";
import AdminChatPage from "@/app/admin/chat/page";
import AdminEmailDashboard from "@/app/admin/email/page";

describe("Unified Communication hub", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin", permissions: ["email.manage"] };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("renders the unified hub with Email, Chat and Video tabs", async () => {
    render(<CommunicationPage />);
    await waitFor(() => {
      expect(screen.getByText("Unified internal & external communication hub")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "Communication" })).toBeInTheDocument();
    expect(screen.getByTestId("tab-email")).toBeInTheDocument();
    expect(screen.getByTestId("tab-chat")).toBeInTheDocument();
    expect(screen.getByTestId("tab-video")).toBeInTheDocument();
  });

  it("shows the Email panel by default", async () => {
    render(<CommunicationPage />);
    await waitFor(() => {
      expect(screen.getByText("ADMIN EMAIL PANEL")).toBeInTheDocument();
    });
    expect(screen.queryByText("ADMIN CHAT PANEL")).not.toBeInTheDocument();
    expect(screen.queryByText("ADMIN VIDEO PANEL")).not.toBeInTheDocument();
  });

  it("switches to Chat panel when the Chat tab is clicked", async () => {
    render(<CommunicationPage />);
    await waitFor(() => expect(screen.getByTestId("tab-chat")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("tab-chat"));
    await waitFor(() => {
      expect(screen.getByText("ADMIN CHAT PANEL")).toBeInTheDocument();
    });
    expect(screen.queryByText("ADMIN EMAIL PANEL")).not.toBeInTheDocument();
  });

  it("switches to Video panel when the Video tab is clicked", async () => {
    render(<CommunicationPage />);
    await waitFor(() => expect(screen.getByTestId("tab-video")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("tab-video"));
    await waitFor(() => {
      expect(screen.getByText("ADMIN VIDEO PANEL")).toBeInTheDocument();
    });
    expect(screen.queryByText("ADMIN EMAIL PANEL")).not.toBeInTheDocument();
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
