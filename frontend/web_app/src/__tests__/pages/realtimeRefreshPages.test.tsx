import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const mockRouter = { push: mockPush, replace: jest.fn(), prefetch: jest.fn() };
const mockSocketClose = jest.fn();
const mockConnectUserRealtimeSocket = jest.fn();
const mockIsNotificationRealtimeMessage = jest.fn((payload: { type?: string } | null) => payload?.type?.startsWith("notification."));
const mockIsTicketRealtimeMessage = jest.fn((payload: { type?: string } | null) => payload?.type?.startsWith("ticket."));

let mockIsLoggedIn = true;
let mockIsLoading = false;
let mockParams = { id: "9" };
let mockPathname = "/notifications";
let websocketHandler: ((payload: any) => void) | null = null;

jest.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
  useParams: () => mockParams,
  usePathname: () => mockPathname,
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href }: any) => <a href={href}>{children}</a>,
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockIsLoading,
    user: mockIsLoggedIn ? { id: 31, username: "amina_customer", email: "customer@zozi.test", role: "customer" } : null,
    logout: jest.fn(),
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: mockApiFetch,
}));

const mockCartStore = {
  getItemCount: () => 0,
  initialize: jest.fn(),
};

const mockWishlistStore = {
  ids: [],
  initialize: jest.fn(),
};

jest.mock("@/lib/cartStore", () => ({
  useCartStore: Object.assign(
    (selector: any) => (selector ? selector(mockCartStore) : mockCartStore),
    { getState: () => mockCartStore },
  ),
}));

jest.mock("@/lib/wishlistStore", () => ({
  useWishlistStore: Object.assign(
    (selector: any) => (selector ? selector(mockWishlistStore) : mockWishlistStore),
    { getState: () => mockWishlistStore },
  ),
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: mockConnectUserRealtimeSocket,
  isNotificationRealtimeMessage: mockIsNotificationRealtimeMessage,
  isTicketRealtimeMessage: mockIsTicketRealtimeMessage,
}));

jest.mock("@shared/realtime", () => ({
  createRealtimeRefreshScheduler: (refresh: () => void | Promise<void>) => ({
    cancel: jest.fn(),
    trigger: () => {
      void refresh();
    },
  }),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

jest.mock("@/components/ThemeToggle", () => function ThemeToggleMock() {
  return <button type="button">theme</button>;
});

jest.mock("@/components/Logo", () => function LogoMock() {
  return <div data-testid="logo" />;
});

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => {
    const store = { locale: "en", t: (key: string) => key, setLocale: jest.fn(), syncLocaleToServer: jest.fn() };
    return selector ? selector(store) : store;
  },
}));

jest.mock("@/lib/authModalStore", () => ({
  useAuthModalStore: (selector: any) => {
    const store = { open: jest.fn() };
    return selector ? selector(store) : store;
  },
}));

import NotificationsPage from "@/app/notifications/page";
import TicketDetailPage from "@/app/tickets/[id]/page";
import Header from "@/components/Header";
import { notificationStore } from "@/lib/notificationStore";

type TicketReply = {
  id: number;
  message: string;
  is_admin: boolean;
  created_at: string;
  attachments: string[];
};

type TicketPayload = {
  id: number;
  subject: string;
  message: string;
  status: string;
  priority: string;
  ticket_category: string;
  created_at: string;
  replies: TicketReply[];
  attachments: string[];
};

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("web realtime page refreshes", () => {
  beforeEach(() => {
    mockIsLoggedIn = true;
    mockIsLoading = false;
    mockParams = { id: "9" };
    mockPathname = "/notifications";
    websocketHandler = null;
    mockSocketClose.mockReset();
    mockPush.mockReset();
    mockApiFetch.mockReset();
    mockConnectUserRealtimeSocket.mockReset();
    mockIsNotificationRealtimeMessage.mockClear();
    mockIsTicketRealtimeMessage.mockClear();
    mockCartStore.initialize.mockClear();
    mockWishlistStore.initialize.mockClear();
    notificationStore.getState().reset();
    mockApiFetch.mockResolvedValue(okJson([]));
    mockConnectUserRealtimeSocket.mockImplementation((_onStatusChange, onMessage) => {
      websocketHandler = onMessage;
      return { close: mockSocketClose } as any;
    });
  });

  it("refreshes the notifications page when a notification websocket event arrives", async () => {
    let currentNotifications = [
      {
        id: 1,
        type: "system",
        title: "Initial notice",
        message: "Before realtime refresh",
        read: false,
        created_at: "2026-03-30T10:00:00Z",
      },
    ];
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/notifications") {
        return okJson(currentNotifications);
      }
      return okJson([]);
    });

    render(<NotificationsPage />);

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(mockApiFetch.mock.calls.length).toBeGreaterThan(0);
    const initialNotificationCalls = mockApiFetch.mock.calls.filter(([path]) => path === "/notifications").length;

    currentNotifications = [
      {
        id: 2,
        type: "system",
        title: "Refreshed notice",
        message: "After realtime refresh",
        read: false,
        created_at: "2026-03-30T10:05:00Z",
      },
    ];

    await act(async () => {
      websocketHandler?.({ type: "notification.created", notification_id: 2 });
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockApiFetch.mock.calls.filter(([path]) => path === "/notifications").length).toBeGreaterThan(initialNotificationCalls);
  });

  it("does not trigger a Header render-phase update when notification actions change unread state", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/notifications") {
        return okJson([
          {
            id: 1,
            type: "system",
            title: "Unread notice",
            message: "Needs review",
            read: false,
            created_at: "2026-03-30T10:00:00Z",
          },
        ]);
      }

      if (path === "/notifications/read-all") {
        return okJson({ ok: true });
      }

      return okJson([]);
    });

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <>
        <Header />
        <NotificationsPage />
      </>,
    );

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    fireEvent.click(screen.getByRole("button", { name: /mark all as read/i }));

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(
      consoleErrorSpy.mock.calls.some(([message]) => String(message).includes("Cannot update a component (`Header`) while rendering a different component (`NotificationsPage`)")),
    ).toBe(false);

    consoleErrorSpy.mockRestore();
  });

  it("refreshes the ticket detail page when a matching ticket websocket event arrives", async () => {
    let currentTicket: TicketPayload = {
        id: 9,
        subject: "Order issue",
        message: "Initial ticket message",
        status: "open",
        priority: "normal",
        ticket_category: "customer",
        created_at: "2026-03-30T10:00:00Z",
        replies: [],
        attachments: [],
      };
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/tickets/9") {
        return okJson(currentTicket);
      }
      return okJson([]);
    });

    render(<TicketDetailPage />);

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(mockApiFetch.mock.calls.length).toBeGreaterThan(0);
    const initialTicketCalls = mockApiFetch.mock.calls.filter(([path]) => path === "/tickets/9").length;

    currentTicket = {
      ...currentTicket,
      replies: [
        {
          id: 11,
          message: "Support replied in realtime.",
          is_admin: true,
          created_at: "2026-03-30T10:06:00Z",
          attachments: [],
        },
      ],
    };

    await act(async () => {
      websocketHandler?.({ type: "ticket.reply_created", ticket_id: 9, reply_id: 11, is_admin: true });
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockApiFetch.mock.calls.filter(([path]) => path === "/tickets/9").length).toBeGreaterThan(initialTicketCalls);
  });
});


