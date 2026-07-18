import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockRouterPush = jest.fn();
const mockRouterBack = jest.fn();
const mockOpenUrl = jest.fn();
const mockAlert = jest.fn();
const mockGetDocumentAsync = jest.fn();
const mockGetLogisticsPartnerProfile = jest.fn();
const mockGetLogisticsPartnerServiceAreas = jest.fn();
const mockGetPartnerBankAccount = jest.fn();
const mockListLogisticsPartnerDocuments = jest.fn();
const mockUploadLogisticsPartnerDocument = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    TextInput: (props: unknown) => React.createElement("TextInput", props),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    Modal: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Modal", props, children),
    Alert: { alert: (...args: unknown[]) => mockAlert(...args) },
    Linking: { openURL: (...args: unknown[]) => mockOpenUrl(...args) },
    StyleSheet: {
      create: (styles: unknown) => styles,
      hairlineWidth: 1,
      absoluteFill: {},
      absoluteFillObject: {},
    },
  };
});

jest.mock("expo-document-picker", () => ({
  getDocumentAsync: (...args: unknown[]) => mockGetDocumentAsync(...args),
}));

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush, back: mockRouterBack }),
}));

jest.mock("@/lib/api", () => ({
  getLogisticsPartnerProfile: (...args: unknown[]) => mockGetLogisticsPartnerProfile(...args),
  updateLogisticsPartnerProfile: jest.fn(),
  getLogisticsPartnerServiceAreas: (...args: unknown[]) => mockGetLogisticsPartnerServiceAreas(...args),
  addLogisticsPartnerServiceArea: jest.fn(),
  removeLogisticsPartnerServiceArea: jest.fn(),
  acceptLogisticsPartnerTerms: jest.fn(),
  getPartnerBankAccount: (...args: unknown[]) => mockGetPartnerBankAccount(...args),
  upsertPartnerBankAccount: jest.fn(),
  listLogisticsPartnerDocuments: (...args: unknown[]) => mockListLogisticsPartnerDocuments(...args),
  uploadLogisticsPartnerDocument: (...args: unknown[]) => mockUploadLogisticsPartnerDocument(...args),
  deleteLogisticsPartnerDocument: jest.fn(),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: (selector: (state: { theme: unknown }) => unknown) => selector({
    theme: {
      colors: {
        brand: "#1d4ed8",
        onBrand: "#ffffff",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#e2e8f0",
        border: "#cbd5e1",
        text: "#0f172a",
        textMuted: "#475569",
        textFaint: "#64748b",
        success: "#16a34a",
        warning: "#f59e0b",
        danger: "#dc2626",
      },
      spacing: { sm: 12, md: 16, lg: 20 },
      radius: { lg: 12, xl: 16 },
      fontSize: { xs: 12, sm: 14, md: 16, lg: 18 },
    },
  }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: (state: { locale: string }) => unknown) => selector({ locale: "en" }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (texts: string[]) => texts,
}));

jest.mock("@shared/localization", () => ({
  isRtlLocale: () => false,
}));

const Screen = require("../../app/logistics-partner/profile").default;

function flattenText(value: unknown): string {
  if (Array.isArray(value)) return value.map(flattenText).join(" ");
  if (value == null || typeof value === "boolean") return "";
  return String(value);
}

function getRenderedText(renderer: TestRenderer.ReactTestRenderer): string {
  return renderer.root
    .findAll((node) => String(node.type) === "Text")
    .map((node) => flattenText(node.props.children))
    .join(" ");
}

function findTouchableByLabel(renderer: TestRenderer.ReactTestRenderer, label: string) {
  return renderer.root.findAll((node) => {
    if (String(node.type) !== "TouchableOpacity") return false;
    return node.findAll((child) => String(child.type) === "Text" && flattenText(child.props.children).includes(label)).length > 0;
  })[0];
}

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("logistics partner profile mobile documents tab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetLogisticsPartnerProfile.mockResolvedValue({
      id: 5,
      name: "Falcon Fleet",
      code: "FF-01",
      business_type: "courier",
      contact_name: "Amina Noor",
      contact_email: "ops@falconfleet.test",
      contact_phone: "+971500000000",
      verification_status: "approved",
      status: "active",
      service_types: ["standard"],
      is_terms_accepted: true,
      terms_version: "1.0",
    });
    mockGetLogisticsPartnerServiceAreas.mockResolvedValue([]);
    mockGetPartnerBankAccount.mockResolvedValue({ configured: false });
    mockListLogisticsPartnerDocuments.mockResolvedValue([
      {
        id: 44,
        partner_id: 5,
        document_type: "insurance",
        document_name: "Fleet Insurance 2026",
        file_url: "https://example.test/docs/insurance.pdf",
        status: "pending",
        created_at: "2026-04-16T10:00:00",
        review_note: null,
      },
    ]);
    mockGetDocumentAsync.mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file:///insurance.pdf", name: "insurance.pdf", mimeType: "application/pdf" }],
    });
    mockUploadLogisticsPartnerDocument.mockResolvedValue({ id: 45, status: "pending" });
  });

  it("renders native document management instead of the old web-only handoff", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<Screen />);
    });
    await flush();

    act(() => {
      findTouchableByLabel(renderer, "Docs").props.onPress();
    });
    await flush();

    expect(mockListLogisticsPartnerDocuments).toHaveBeenCalledTimes(1);

    const text = getRenderedText(renderer);
    expect(text).toContain("KYC Documents");
    expect(text).toContain("Fleet Insurance 2026");
    expect(text).toContain("Choose File");
    expect(text).not.toContain("Document upload requires the web dashboard");
  });

  it("uploads a newly selected document from the mobile documents tab", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<Screen />);
    });
    await flush();

    act(() => {
      findTouchableByLabel(renderer, "Docs").props.onPress();
    });
    await flush();

    await act(async () => {
      findTouchableByLabel(renderer, "Choose File").props.onPress();
    });
    await flush();

    await act(async () => {
      findTouchableByLabel(renderer, "Upload Document").props.onPress();
    });
    await flush();

    expect(mockGetDocumentAsync).toHaveBeenCalled();
    expect(mockUploadLogisticsPartnerDocument).toHaveBeenCalledWith({
      file: {
        uri: "file:///insurance.pdf",
        name: "insurance.pdf",
        mimeType: "application/pdf",
      },
      documentType: "trade_license",
      documentName: "insurance",
      expiresAt: null,
    });
    expect(mockListLogisticsPartnerDocuments).toHaveBeenCalledTimes(2);
  });
});