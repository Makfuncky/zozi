"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useEffect, useRef, useState, type ChangeEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  User,
  Mail,
  Building,
  Save,
  Shield,
  Lock,
  AlertCircle,
  Package,
  DollarSign,
  TrendingUp,
  Globe,
  MapPin,
  Phone,
  FileText,
  CheckCircle,
  Clock,
  XCircle,
  Star,
  ExternalLink,
  Eye,
  Plus,
  Trash2,
  ImageIcon,
  BadgeCheck,
  Upload,
  Link2,
  RefreshCw,
  Search,
  Loader2,
  Info,
} from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { normalizeListPage } from "@/lib/listResponse";
import { useAuth } from "@/lib/useAuth";
import { Product, SupplierPublicProfile } from "@/lib/types";
import { resolveImage, supplierStorefrontPath } from "@/lib/utils";
import { useCurrencyStore } from "@/lib/currencyStore";

type Tab = "account" | "business" | "storefront" | "security" | "bank" | "documents" | "coverage" | "terms" | "guide";

type CertificationForm = {
  title: string;
  issuer: string;
  year: string;
  image_url: string;
};

type SocialLinksForm = {
  instagram: string;
  facebook: string;
  twitter: string;
  linkedin: string;
  youtube: string;
  tiktok: string;
};

type MediaField = "logo_url" | "banner_url" | "video_url" | "certification_image";

interface BusinessProfile {
  business_name: string;
  business_type: string;
  country: string;
  region: string;
  city: string;
  address: string;
  postal_code: string;
  phone_business: string;
  website: string;
  tax_id: string;
  bio: string;
  about_us: string;
  logo_url: string;
  banner_url: string;
  video_url: string;
  established_year: string;
  certifications: CertificationForm[];
  social_links: SocialLinksForm;
  is_terms_accepted: boolean;
  terms_version: string | null;
  terms_accepted_at: string | null;
  verification_status: string;
}

interface SupplierDocumentSummary {
  id: number;
  document_type?: string;
  document_name?: string;
  file_url?: string;
  status: string;
  review_note?: string | null;
  expires_at?: string | null;
  created_at?: string;
}

interface SupplierRegionSummary {
  operating_regions?: string[];
  origin_country?: string | null;
  city?: string | null;
}

interface RecipientBankAccount {
  configured: boolean;
  id?: number;
  beneficiary_name?: string | null;
  bank_name?: string | null;
  branch_name?: string | null;
  account_number?: string | null;
  iban?: string | null;
  swift_code?: string | null;
  routing_number?: string | null;
  currency?: string;
  bank_country?: string | null;
  verification_status?: "pending" | "verified" | "rejected";
  verification_note?: string | null;
  verified_at?: string | null;
}

const EMPTY_BANK_FORM = {
  beneficiary_name: "",
  bank_name: "",
  branch_name: "",
  account_number: "",
  iban: "",
  swift_code: "",
  routing_number: "",
  currency: "OMR",
  bank_country: "",
};

const BUSINESS_TYPES = [
  { value: "individual", label: "Individual / Sole Trader" },
  { value: "company", label: "Company / Corporation" },
  { value: "partnership", label: "Partnership" },
  { value: "llc", label: "LLC" },
];

const PROFILE_ACTIONS = [
  { key: "account", label: "Account", icon: User },
  { key: "business", label: "Business & Location", icon: Building },
  { key: "storefront", label: "Storefront & About", icon: Globe },
  { key: "security", label: "Security", icon: Shield },
  { key: "bank", label: "Bank Details", icon: Building },
  { key: "documents", label: "KYC Documents", icon: FileText },
  { key: "coverage", label: "Coverage", icon: MapPin },
  { key: "terms", label: "Terms & Conditions", icon: FileText },
  { key: "guide", label: "Supplier Guide", icon: ExternalLink },
] as const;

const GUIDE_CHECKLIST = [
  "Review account, business, and storefront data before requesting approval.",
  "Upload KYC files and keep coverage regions current for pickup readiness.",
  "Use product media plus AI to fill name, category, color, tags, and description faster.",
  "Upload parcel proof from Orders so the handoff moves into Prepared before logistics pickup.",
];

const GUIDE_TIPS = [
  "The first clean product photo gives the AI the best chance of naming and categorizing the listing correctly.",
  "Coverage and terms now sit inside Profile, so you can resolve compliance issues without leaving this workspace.",
  "Products only surface well to customers when stock, sizes, and gallery media are all complete.",
];

const GUIDE_WALKTHROUGH = [
  {
    title: "1. Set up your profile",
    body: "Complete account details, business identity, storefront visuals, and compliance data before you ask for approval or share the public storefront.",
  },
  {
    title: "2. Build product listings",
    body: "Use product media plus AI to draft names, categories, colors, tags, and descriptions, then verify stock, sizes, return windows, and gallery media before publishing.",
  },
  {
    title: "3. Manage orders and handoff",
    body: "Track customer orders in the merged Orders workspace, upload parcel proof when a parcel is packed, and monitor the Prepared to logistics pickup transition from the same workspace.",
  },
  {
    title: "4. Resolve payouts and support",
    body: "Use Payouts for settlement timing and invoice records, and use Support for disputes or operational follow-up that needs formal review.",
  },
];

const DOCUMENT_TYPES = [
  { value: "business_license", label: "Business License" },
  { value: "trade_license", label: "Trade License" },
  { value: "tax_certificate", label: "Tax Certificate / VAT" },
  { value: "national_id", label: "National ID / Passport" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "product_certificate", label: "Product Certificate" },
  { value: "insurance", label: "Insurance Document" },
  { value: "other", label: "Other" },
] as const;

const STATUS_CHIP: Record<string, string> = {
  pending: "theme-chip-warning",
  under_review: "theme-chip-info",
  approved: "theme-chip-success",
  rejected: "theme-chip-danger",
  expired: "theme-chip-muted",
};

const ALL_COUNTRIES = [
  "Afghanistan", "Albania", "Algeria", "Angola", "Argentina", "Armenia", "Australia",
  "Austria", "Azerbaijan", "Bahrain", "Bangladesh", "Belarus", "Belgium", "Bolivia",
  "Bosnia and Herzegovina", "Brazil", "Bulgaria", "Cambodia", "Cameroon", "Canada",
  "Chile", "China", "Colombia", "Croatia", "Czech Republic", "Denmark", "Ecuador",
  "Egypt", "Ethiopia", "Finland", "France", "Georgia", "Germany", "Ghana", "Greece",
  "Hungary", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy",
  "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Lebanon", "Libya",
  "Malaysia", "Mexico", "Morocco", "Myanmar", "Netherlands", "New Zealand", "Nigeria",
  "Norway", "Oman", "Pakistan", "Palestine", "Philippines", "Poland", "Portugal",
  "Qatar", "Romania", "Russia", "Saudi Arabia", "Senegal", "Serbia", "Singapore",
  "Somalia", "South Africa", "South Korea", "Spain", "Sri Lanka", "Sudan", "Sweden",
  "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand", "Tunisia", "Turkey",
  "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
  "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zimbabwe",
];

const REGION_GROUPS = [
  { label: "GCC (Gulf)", countries: ["Saudi Arabia", "United Arab Emirates", "Kuwait", "Qatar", "Bahrain", "Oman"] },
  { label: "Middle East & North Africa", countries: ["Egypt", "Jordan", "Lebanon", "Iraq", "Syria", "Yemen", "Libya", "Tunisia", "Algeria", "Morocco", "Palestine"] },
  { label: "South Asia", countries: ["India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"] },
  { label: "Europe", countries: ["United Kingdom", "Germany", "France", "Netherlands", "Spain", "Italy", "Portugal", "Belgium", "Sweden", "Norway", "Finland", "Denmark", "Poland", "Czech Republic", "Romania", "Hungary", "Austria", "Switzerland", "Greece", "Croatia", "Bulgaria", "Serbia"] },
  { label: "South-East Asia", countries: ["Malaysia", "Singapore", "Thailand", "Vietnam", "Indonesia", "Philippines", "Myanmar", "Cambodia"] },
  { label: "Americas", countries: ["United States", "Canada", "Brazil", "Mexico", "Argentina", "Colombia", "Chile", "Ecuador", "Bolivia", "Venezuela"] },
  { label: "Africa (Sub-Saharan)", countries: ["Nigeria", "Kenya", "Ethiopia", "South Africa", "Ghana", "Tanzania", "Uganda", "Senegal", "Cameroon", "Angola", "Zimbabwe", "Sudan", "Somalia"] },
] as const;

const TERMS_SECTIONS = [
  { title: "1. Eligibility", body: "You must be at least 18 years old and legally authorised to sell products in your jurisdiction. By registering as a ZOZI supplier, you confirm that you meet these requirements and that all information you provide is accurate and truthful." },
  { title: "2. Product Listings", body: "All products listed must be authentic, accurately described, and compliant with applicable laws and regulations. Counterfeit, illegal, or dangerous goods are strictly prohibited and will result in immediate account suspension and potential legal action. ZOZI reserves the right to remove any product listing at its sole discretion." },
  { title: "3. Pricing & Platform Commission", body: "ZOZI charges a platform commission on each completed sale. Commission rates are displayed in your supplier dashboard and may be updated with notice. Pricing and supplier-facing payout surfaces follow the configured regional currency rules for your operating market." },
  { title: "4. Order Fulfilment", body: "Suppliers are responsible for preparing orders within their lead time, uploading parcel proof when the package is ready, and handing parcels to the assigned logistics partner for shipment progression." },
  { title: "5. Returns & Refunds", body: "Suppliers must honour ZOZI's return and refund policy for orders placed through the platform. Supplier-caused returns may be deducted from future payouts." },
  { title: "6. Payouts", body: "Payouts are processed on a rolling schedule after applicable commission, refunds, and adjustments. ZOZI may withhold payouts while disputes, fraud, or policy violations are under review." },
  { title: "7. Data & Privacy", body: "Customer personal data obtained through ZOZI may only be used to fulfil the relevant order and must not be reused for marketing or third-party sharing." },
  { title: "8. Intellectual Property", body: "By uploading product images and descriptions to ZOZI, you grant ZOZI a non-exclusive licence to display that content to customers for platform operation and marketing." },
  { title: "9. Prohibited Conduct", body: "Suppliers must not circumvent the platform, manipulate reviews, or engage in fraud. Violations may lead to immediate account termination." },
  { title: "10. Account Termination", body: "ZOZI may suspend or terminate supplier accounts that violate platform policy, subject to review of outstanding orders, payouts, and obligations." },
  { title: "11. Changes to Terms", body: "ZOZI may update these terms over time. Continued use of the platform after the effective date constitutes acceptance of the updated terms." },
] as const;

const emptyCertification = (): CertificationForm => ({
  title: "",
  issuer: "",
  year: "",
  image_url: "",
});

const defaultBusinessProfile = (): BusinessProfile => ({
  business_name: "",
  business_type: "individual",
  country: "",
  region: "",
  city: "",
  address: "",
  postal_code: "",
  phone_business: "",
  website: "",
  tax_id: "",
  bio: "",
  about_us: "",
  logo_url: "",
  banner_url: "",
  video_url: "",
  established_year: "",
  certifications: [emptyCertification()],
  social_links: {
    instagram: "",
    facebook: "",
    twitter: "",
    linkedin: "",
    youtube: "",
    tiktok: "",
  },
  is_terms_accepted: false,
  terms_version: null,
  terms_accepted_at: null,
  verification_status: "pending",
});

function normalizeBusinessProfile(data: any): BusinessProfile {
  const base = defaultBusinessProfile();
  const certifications = Array.isArray(data?.certifications)
    ? data.certifications
        .map((cert: any) => ({
          title: String(cert?.title ?? ""),
          issuer: String(cert?.issuer ?? ""),
          year: cert?.year != null ? String(cert.year) : "",
          image_url: String(cert?.image_url ?? ""),
        }))
        .filter((cert: CertificationForm) => Object.values(cert).some(Boolean))
    : [];

  return {
    ...base,
    ...data,
    business_name: String(data?.business_name ?? ""),
    business_type: String(data?.business_type ?? "individual"),
    country: String(data?.country ?? ""),
    region: String(data?.region ?? ""),
    city: String(data?.city ?? ""),
    address: String(data?.address ?? ""),
    postal_code: String(data?.postal_code ?? ""),
    phone_business: String(data?.phone_business ?? ""),
    website: String(data?.website ?? ""),
    tax_id: String(data?.tax_id ?? ""),
    bio: String(data?.bio ?? ""),
    about_us: String(data?.about_us ?? ""),
    logo_url: String(data?.logo_url ?? ""),
    banner_url: String(data?.banner_url ?? ""),
    video_url: String(data?.video_url ?? ""),
    established_year: data?.established_year != null ? String(data.established_year) : "",
    certifications: certifications.length > 0 ? certifications : [emptyCertification()],
    social_links: {
      ...base.social_links,
      ...(data?.social_links ?? {}),
    },
  };
}

function SupplierProfilePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, refresh, isLoading: authLoading } = useAuth();
  const formatPrice = useCurrencyStore((s) => s.format);
  const logoInputRef = useRef<HTMLInputElement>(null);
  const bannerInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const [tab, setTab] = useState<Tab>("business");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [uploadingMediaField, setUploadingMediaField] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [documents, setDocuments] = useState<SupplierDocumentSummary[]>([]);
  const [regionSummary, setRegionSummary] = useState<SupplierRegionSummary | null>(null);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docUploading, setDocUploading] = useState(false);
  const [docDeleteId, setDocDeleteId] = useState<number | null>(null);
  const [selectedDocFile, setSelectedDocFile] = useState<File | null>(null);
  const [docForm, setDocForm] = useState({ document_type: "business_license", document_name: "", expires_at: "" });
  const [coverageSearch, setCoverageSearch] = useState("");
  const [coverageSaving, setCoverageSaving] = useState(false);
  const [coverageSaved, setCoverageSaved] = useState(false);
  const [coverageDraft, setCoverageDraft] = useState({ origin_country: "", city: "", operating_regions: [] as string[] });
  const [termsAccepting, setTermsAccepting] = useState(false);
  const [storefrontInsights, setStorefrontInsights] = useState<SupplierPublicProfile | null>(null);
  const [storefrontInsightsLoading, setStorefrontInsightsLoading] = useState(false);
  const [bankAccount, setBankAccount] = useState<RecipientBankAccount | null>(null);
  const [bankForm, setBankForm] = useState({ ...EMPTY_BANK_FORM });
  const [bankSaving, setBankSaving] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [biz, setBiz] = useState<BusinessProfile>(defaultBusinessProfile);
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");

  useEffect(() => {
    const requestedTab = searchParams?.get("tab");
    if (!requestedTab) return;
    const normalizedTab = requestedTab === "payout" ? "bank" : requestedTab;
    if (PROFILE_ACTIONS.some((item) => item.key === normalizedTab)) {
      setTab(normalizedTab as Tab);
    }
  }, [searchParams]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) return;

    setUsername(user.username || "");
    setEmail(user.email || "");

    let cancelled = false;

    Promise.all([
      apiFetch("/supplier/products").then((r) => (r.ok ? r.json() : [])).catch(() => []),
      apiFetch("/supplier/profile/business").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      apiFetch("/supplier-documents/my").then((r) => (r.ok ? r.json() : [])).catch(() => []),
      apiFetch("/supplier/regions").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      apiFetch("/supplier/bank-account").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([productsPayload, businessPayload, documentsPayload, regionsPayload, bankPayload]) => {
      if (cancelled) return;
      setProducts(normalizeListPage<Product>(productsPayload).data);
      if (businessPayload) setBiz(normalizeBusinessProfile(businessPayload));
      setDocuments(normalizeListPage<SupplierDocumentSummary>(documentsPayload).data);
      setRegionSummary(regionsPayload && typeof regionsPayload === "object" ? regionsPayload : null);
      if (bankPayload && typeof bankPayload === "object" && (bankPayload as RecipientBankAccount).id) {
        const nextBank = bankPayload as RecipientBankAccount;
        setBankAccount(nextBank);
        setBankForm({
          beneficiary_name: nextBank.beneficiary_name || "",
          bank_name: nextBank.bank_name || "",
          branch_name: nextBank.branch_name || "",
          account_number: nextBank.account_number || "",
          iban: nextBank.iban || "",
          swift_code: nextBank.swift_code || "",
          routing_number: nextBank.routing_number || "",
          currency: nextBank.currency || "OMR",
          bank_country: nextBank.bank_country || "",
        });
      }
    });

    return () => {
      cancelled = true;
    };
  }, [authLoading, user]);

  useEffect(() => {
    setCoverageDraft({
      origin_country: regionSummary?.origin_country || "",
      city: regionSummary?.city || "",
      operating_regions: Array.isArray(regionSummary?.operating_regions) ? regionSummary!.operating_regions! : [],
    });
  }, [regionSummary]);

  useEffect(() => {
    if (authLoading || !user?.username) {
      setStorefrontInsights(null);
      setStorefrontInsightsLoading(false);
      return;
    }

    let cancelled = false;
    setStorefrontInsightsLoading(true);

    apiFetch(`/suppliers/resolve/${encodeURIComponent(user.username)}`)
      .then(async (resolveRes) => {
        if (!resolveRes.ok) return null;
        const resolved = await resolveRes.json();
        if (!resolved?.id) return null;

        const profileRes = await apiFetch(`/suppliers/${resolved.id}`);
        if (!profileRes.ok) return null;
        return await profileRes.json();
      })
      .then((profile: SupplierPublicProfile | null) => {
        if (cancelled) return;
        setStorefrontInsights(profile);
      })
      .catch(() => {
        if (!cancelled) setStorefrontInsights(null);
      })
      .finally(() => {
        if (!cancelled) setStorefrontInsightsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [authLoading, user?.username]);

  const fetchDocuments = async () => {
    setDocsLoading(true);
    try {
      const res = await apiFetch("/supplier-documents/my");
      if (res.ok) {
        const payload = normalizeListPage<SupplierDocumentSummary>(await res.json());
        setDocuments(payload.data);
      }
    } finally {
      setDocsLoading(false);
    }
  };

  const handleDocUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedDocFile) {
      setError("Select a KYC file before uploading");
      return;
    }
    if (!docForm.document_name.trim()) {
      setError("Document name is required");
      return;
    }

    setDocUploading(true);
    setError("");
    setMsg("");
    try {
      const formData = new FormData();
      formData.append("file", selectedDocFile);
      formData.append("document_type", docForm.document_type);
      formData.append("document_name", docForm.document_name.trim());
      if (docForm.expires_at) formData.append("expires_at", new Date(docForm.expires_at).toISOString());

      const res = await apiFetch("/supplier-documents/my/upload", { method: "POST", body: formData });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "KYC upload failed");
        return;
      }
      setDocForm({ document_type: "business_license", document_name: "", expires_at: "" });
      setSelectedDocFile(null);
      await fetchDocuments();
      setMsg("KYC document uploaded successfully");
    } catch {
      setError("KYC upload failed");
    } finally {
      setDocUploading(false);
    }
  };

  const handleDocDelete = async (id: number) => {
    if (!window.confirm("Delete this document?")) return;
    setDocDeleteId(id);
    try {
      const res = await apiFetch(`/supplier-documents/my/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDocuments((current) => current.filter((document) => document.id !== id));
      }
    } finally {
      setDocDeleteId(null);
    }
  };

  const toggleCoverageCountry = (country: string) => {
    setCoverageSaved(false);
    setCoverageDraft((current) => ({
      ...current,
      operating_regions: current.operating_regions.includes(country)
        ? current.operating_regions.filter((item) => item !== country)
        : [...current.operating_regions, country],
    }));
  };

  const updateCoverageGroup = (countries: readonly string[], add: boolean) => {
    setCoverageSaved(false);
    setCoverageDraft((current) => {
      const next = new Set(current.operating_regions);
      countries.forEach((country) => {
        if (add) next.add(country);
        else next.delete(country);
      });
      return { ...current, operating_regions: Array.from(next) };
    });
  };

  const saveCoverage = async () => {
    setCoverageSaving(true);
    setCoverageSaved(false);
    setError("");
    try {
      const res = await apiFetch("/supplier/regions", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(coverageDraft),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Failed to save coverage");
        return;
      }
      const payload = await res.json();
      setRegionSummary(payload && typeof payload === "object" ? payload : null);
      setCoverageSaved(true);
      setMsg("Coverage updated");
    } catch {
      setError("Failed to save coverage");
    } finally {
      setCoverageSaving(false);
    }
  };

  const acceptTerms = async () => {
    setTermsAccepting(true);
    setError("");
    setMsg("");
    try {
      const res = await apiFetch("/supplier/terms/accept", { method: "POST" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Failed to accept terms");
        return;
      }
      const payload = await res.json();
      setBiz((current) => ({
        ...current,
        is_terms_accepted: true,
        terms_version: payload.terms_version || current.terms_version,
        terms_accepted_at: new Date().toISOString(),
      }));
      setMsg("Terms accepted successfully");
    } catch {
      setError("Failed to accept terms");
    } finally {
      setTermsAccepting(false);
    }
  };

  const setBizField =
    (field: keyof BusinessProfile) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setBiz((current) => ({ ...current, [field]: event.target.value }));
    };

  const setSocialField =
    (field: keyof SocialLinksForm) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      setBiz((current) => ({
        ...current,
        social_links: { ...current.social_links, [field]: event.target.value },
      }));
    };

  const updateCertification =
    (index: number, field: keyof CertificationForm) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setBiz((current) => ({
        ...current,
        certifications: current.certifications.map((cert, certIndex) =>
          certIndex === index ? { ...cert, [field]: value } : cert
        ),
      }));
    };

  const addCertification = () => {
    setBiz((current) => ({ ...current, certifications: [...current.certifications, emptyCertification()] }));
  };

  const removeCertification = (index: number) => {
    setBiz((current) => {
      const next = current.certifications.filter((_, certIndex) => certIndex !== index);
      return { ...current, certifications: next.length > 0 ? next : [emptyCertification()] };
    });
  };

  const certificationUploadKey = (index: number) => `certification_image:${index}`;

  const uploadStorefrontMedia = async (field: MediaField, file: File, index?: number) => {
    setError("");
    setMsg("");
    setUploadingMediaField(field === "certification_image" && index != null ? certificationUploadKey(index) : field);

    const formData = new FormData();
    formData.append("field", field);
    formData.append("file", file);
    if (field === "certification_image" && index != null) {
      formData.append("index", String(index));
    }

    const fieldLabels: Record<MediaField, string> = {
      logo_url: "logo",
      banner_url: "banner",
      video_url: "video",
      certification_image: "certification image",
    };

    try {
      const res = await apiFetch("/supplier/profile/business/media", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || `Failed to upload ${fieldLabels[field]}`);
        return;
      }

      if (field === "certification_image" && index != null) {
        setBiz((current) => {
          const next = normalizeBusinessProfile(data.profile ?? data);
          const localCertification = current.certifications[index];
          if (!localCertification) return next;

          const mergedCertification = {
            ...localCertification,
            ...(next.certifications[index] ?? {}),
          };

          if (index >= next.certifications.length) {
            next.certifications = [...next.certifications, mergedCertification];
          } else {
            next.certifications = next.certifications.map((certification, certificationIndex) =>
              certificationIndex === index ? mergedCertification : certification
            );
          }

          return next;
        });
      } else {
        setBiz(normalizeBusinessProfile(data.profile ?? data));
      }
      setMsg(`Storefront ${fieldLabels[field]} uploaded`);
    } catch {
      setError(`Failed to upload ${fieldLabels[field]}`);
    } finally {
      setUploadingMediaField(null);
    }
  };

  const handleMediaSelection =
    (field: MediaField, index?: number) =>
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (!file) return;
      await uploadStorefrontMedia(field, file, index);
    };

  const saveAccount = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMsg("");
    setLoading(true);
    try {
      const res = await apiFetch("/auth/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Update failed");
        return;
      }
      setMsg("Account info updated");
      await refresh();
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const saveBusinessProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMsg("");
    setLoading(true);

    const certifications = biz.certifications
      .map((cert) => ({
        title: cert.title.trim(),
        issuer: cert.issuer.trim() || undefined,
        year: cert.year.trim() ? Number(cert.year.trim()) : undefined,
        image_url: cert.image_url.trim() || undefined,
      }))
      .filter((cert) => cert.title);

    const social_links = Object.fromEntries(
      Object.entries(biz.social_links)
        .map(([platform, url]) => [platform, url.trim()])
        .filter(([, url]) => Boolean(url))
    );

    try {
      const res = await apiFetch("/supplier/profile/business", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: biz.business_name,
          business_type: biz.business_type,
          country: biz.country,
          region: biz.region,
          city: biz.city,
          address: biz.address,
          postal_code: biz.postal_code,
          phone_business: biz.phone_business,
          website: biz.website,
          tax_id: biz.tax_id,
          bio: biz.bio,
          about_us: biz.about_us,
          logo_url: biz.logo_url,
          banner_url: biz.banner_url,
          video_url: biz.video_url,
          established_year: biz.established_year || undefined,
          certifications,
          social_links,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Save failed");
        return;
      }

      const data = await res.json();
      setBiz(normalizeBusinessProfile(data));
      setMsg("Supplier storefront saved");
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const changePw = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMsg("");
    if (newPw !== confirmPw) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const res = await apiFetch("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Change failed");
        return;
      }
      setMsg("Password changed");
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const saveBankAccount = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMsg("");
    setBankSaving(true);
    try {
      const response = await apiFetch("/supplier/bank-account", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beneficiary_name: bankForm.beneficiary_name.trim() || undefined,
          bank_name: bankForm.bank_name.trim() || undefined,
          branch_name: bankForm.branch_name.trim() || undefined,
          account_number: bankForm.account_number.trim() || undefined,
          iban: bankForm.iban.trim() || undefined,
          swift_code: bankForm.swift_code.trim() || undefined,
          routing_number: bankForm.routing_number.trim() || undefined,
          currency: bankForm.currency.trim() || "OMR",
          bank_country: bankForm.bank_country.trim() || undefined,
        }),
      });
      const payload = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }
      const nextBank = payload as RecipientBankAccount;
      setBankAccount(nextBank);
      setBankForm({
        beneficiary_name: nextBank.beneficiary_name || "",
        bank_name: nextBank.bank_name || "",
        branch_name: nextBank.branch_name || "",
        account_number: nextBank.account_number || "",
        iban: nextBank.iban || "",
        swift_code: nextBank.swift_code || "",
        routing_number: nextBank.routing_number || "",
        currency: nextBank.currency || "OMR",
        bank_country: nextBank.bank_country || "",
      });
      setMsg("Payout bank account saved. Finance will verify it before live payouts.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save bank account");
    } finally {
      setBankSaving(false);
    }
  };

  const totalRevenue = products.reduce((sum, product) => {
    const unitPrice = Number(product.price ?? 0);
    const salesCount = Number(product.sales_count ?? 0);
    const revenue = product.revenue != null ? Number(product.revenue) : unitPrice * salesCount;
    return sum + revenue;
  }, 0);
  const totalSales = products.reduce((sum, product) => sum + Number(product.sales_count ?? 0), 0);
  const storefrontReady = Boolean(biz.business_name && (biz.about_us || biz.bio) && (biz.logo_url || biz.banner_url));
  const storefrontUrl = user ? supplierStorefrontPath({ username: user.username, business_name: biz.business_name }) : undefined;
  const storefrontVisible = biz.verification_status === "approved" || biz.verification_status === "verified";
  const storefrontChecklist = [
    { label: "Business name", done: Boolean(biz.business_name.trim()) },
    { label: "About us or bio", done: Boolean(biz.about_us.trim() || biz.bio.trim()) },
    { label: "Storefront visuals", done: Boolean(biz.logo_url || biz.banner_url) },
    { label: "Contact link or video", done: Boolean(biz.website.trim() || biz.video_url.trim()) },
  ];
  const completedStorefrontItems = storefrontChecklist.filter((item) => item.done).length;
  const storefrontCompletionPercent = Math.round((completedStorefrontItems / storefrontChecklist.length) * 100);
  const resolvedVideoUrl = biz.video_url ? resolveImage(biz.video_url) : "";
  const isUploadedVideo = /\.(mp4|webm|ogg)(?:$|[?#])/i.test(resolvedVideoUrl);
  const reviewAverageLabel = storefrontInsights && storefrontInsights.total_reviews > 0
    ? storefrontInsights.avg_rating.toFixed(1)
    : "New";
  const reviewCount = storefrontInsights?.total_reviews ?? 0;
  const recentPublicReviews = storefrontInsights?.recent_reviews?.slice(0, 3) ?? [];
  const approvedDocs = documents.filter((document) => document.status === "approved").length;
  const pendingDocs = documents.filter((document) => document.status === "pending" || document.status === "under_review").length;
  const filteredCoverageCountries = coverageSearch
    ? ALL_COUNTRIES.filter((country) => country.toLowerCase().includes(coverageSearch.toLowerCase()))
    : ALL_COUNTRIES;

  const verificationBadge = () => {
    switch (biz.verification_status) {
      case "approved":
      case "verified":
        return <span className="inline-flex items-center gap-1 rounded-full bg-success/15 px-2 py-1 text-[10px] font-semibold text-success"><CheckCircle className="h-3 w-3" /> Public storefront live</span>;
      case "under_review":
        return <span className="inline-flex items-center gap-1 rounded-full bg-warning/15 px-2 py-1 text-[10px] font-semibold text-warning"><Clock className="h-3 w-3" /> Under review</span>;
      case "rejected":
        return <span className="inline-flex items-center gap-1 rounded-full bg-danger/15 px-2 py-1 text-[10px] font-semibold text-danger"><XCircle className="h-3 w-3" /> Rejected</span>;
      default:
        return <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-1 text-[10px] font-semibold text-text-muted"><Clock className="h-3 w-3" /> Draft storefront</span>;
    }
  };

  return (
    <SupplierLayout title="Profile">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-6 flex flex-wrap gap-1 rounded-xl border border-border bg-surface-2 p-1">
            {PROFILE_ACTIONS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => {
                    setTab(item.key);
                    router.replace(`/supplier/profile?tab=${item.key}`);
                    setMsg("");
                    setError("");
                  }}
                  className={`flex min-w-fit shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3 py-2.5 text-xs font-semibold transition-colors ${
                    tab === item.key ? "bg-primary text-on-primary" : "text-text-muted hover:text-text"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {item.label}
                </button>
              );
            })}
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-xl border border-danger/20 bg-danger/10 p-3 text-sm text-danger">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
          {msg && <div className="mb-4 rounded-xl border border-success/20 bg-success/10 p-3 text-sm text-success">{msg}</div>}

          {tab === "account" && (
            <motion.form initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} onSubmit={saveAccount} className="theme-card space-y-5 rounded-2xl border p-5">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Username</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                  <input type="text" value={username} onChange={(event) => setUsername(event.target.value)} className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                  <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                </div>
              </div>
              <button type="submit" disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary py-3 text-sm font-bold disabled:opacity-50">
                <Save className="h-4 w-4" />
                {loading ? "Saving..." : "Save account info"}
              </button>
            </motion.form>
          )}

          {tab === "business" && (
            <motion.form initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} onSubmit={saveBusinessProfile} className="theme-card space-y-5 rounded-2xl border p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold text-text-muted">Storefront status</p>
                  <p className="mt-1 text-sm text-text">Business information feeds your customer-facing supplier page.</p>
                </div>
                {verificationBadge()}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Business Name</label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="text" value={biz.business_name} onChange={setBizField("business_name")} placeholder="Dream Mart" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Business Type</label>
                  <select value={biz.business_type} onChange={setBizField("business_type")} className="theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none">
                    {BUSINESS_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Business Phone</label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="tel" value={biz.phone_business} onChange={setBizField("phone_business")} placeholder="+968 ..." className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Country</label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="text" value={biz.country} onChange={setBizField("country")} placeholder="Oman" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Region / State</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="text" value={biz.region} onChange={setBizField("region")} placeholder="Muscat" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">City</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="text" value={biz.city} onChange={setBizField("city")} placeholder="Muscat" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Postal Code</label>
                  <input type="text" value={biz.postal_code} onChange={setBizField("postal_code")} placeholder="112" className="theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Street Address</label>
                  <input type="text" value={biz.address} onChange={setBizField("address")} placeholder="ST 1411, Al Khuwair" className="theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Website</label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="url" value={biz.website} onChange={setBizField("website")} placeholder="https://dreammart.example" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Tax ID / VAT Number</label>
                  <div className="relative">
                    <FileText className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="text" value={biz.tax_id} onChange={setBizField("tax_id")} placeholder="Tax registration" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Business Bio</label>
                  <textarea value={biz.bio} onChange={setBizField("bio")} placeholder="Short version shown on supplier cards and search results." rows={3} className="theme-input w-full resize-none rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                </div>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-border bg-surface-2 p-3">
                <div>
                  <p className="text-xs font-semibold text-text">Terms & Conditions</p>
                  {biz.is_terms_accepted ? (
                    <p className="text-[10px] text-success">Accepted v{biz.terms_version} on {biz.terms_accepted_at ? new Date(biz.terms_accepted_at).toLocaleDateString() : "-"}</p>
                  ) : (
                    <p className="text-[10px] text-warning">Not yet accepted</p>
                  )}
                </div>
                {biz.is_terms_accepted ? <CheckCircle className="h-5 w-5 text-success" /> : <button type="button" onClick={() => setTab("terms")} className="text-[11px] font-semibold text-primary hover:underline">Review now</button>}
              </div>

              <button type="submit" disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary py-3 text-sm font-bold disabled:opacity-50">
                <Save className="h-4 w-4" />
                {loading ? "Saving..." : "Save business profile"}
              </button>
            </motion.form>
          )}

          {tab === "storefront" && (
            <motion.form initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} onSubmit={saveBusinessProfile} className="theme-card space-y-6 rounded-2xl border p-5">
              <div className="rounded-2xl border border-primary/20 bg-primary/5 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-text-faint">Customer-facing supplier page</p>
                    <h2 className="mt-1 text-lg font-bold text-text">Complete your storefront portfolio</h2>
                    <p className="mt-1 text-sm text-text-muted">Everything here feeds the public supplier page, supplier search, and the supplier card on product detail.</p>
                  </div>
                  {storefrontUrl && storefrontVisible ? (
                    <a href={storefrontUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-primary/20 bg-background px-3 py-2 text-xs font-semibold text-primary transition-colors hover:bg-primary/10">
                      <Eye className="h-3.5 w-3.5" />
                      Open live storefront
                    </a>
                  ) : (
                    <div className="inline-flex items-center gap-2 rounded-xl border border-warning/20 bg-warning/10 px-3 py-2 text-xs font-semibold text-warning">
                      <Clock className="h-3.5 w-3.5" />
                      Storefront link unlocks after approval
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                  <div className="rounded-2xl border border-border bg-surface-2 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Storefront completion</p>
                        <p className="mt-2 text-lg font-bold text-text">{storefrontCompletionPercent}% ready</p>
                        <p className="mt-1 text-sm text-text-muted">{completedStorefrontItems} of {storefrontChecklist.length} customer-facing essentials completed.</p>
                      </div>
                      <div className="rounded-2xl bg-primary/10 px-3 py-2 text-center text-primary">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em]">Status</p>
                        <p className="mt-1 text-sm font-bold">{storefrontVisible ? "Live" : "Draft"}</p>
                      </div>
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-background">
                      <div className="h-full rounded-full bg-gradient-to-r from-primary via-primary to-accent" style={{ width: `${storefrontCompletionPercent}%` }} />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface-2 p-4 text-sm text-text-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Public visibility</p>
                    <p className="mt-2 font-semibold text-text">{storefrontVisible ? "Customers can open your supplier page now." : "Customers cannot open your supplier page until approval is complete."}</p>
                    <p className="mt-2 leading-6">Current review state: <span className="font-semibold text-text">{String(biz.verification_status).replace(/_/g, " ")}</span>. Badge visibility and storefront routing follow the approved or verified status returned by the backend.</p>
                  </div>
                </div>

                {storefrontUrl && (
                  <div className="rounded-2xl border border-border bg-surface-2 p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-text">
                      <Link2 className="h-4 w-4 text-primary" />
                      {storefrontVisible ? "Live storefront URL" : "Planned storefront URL"}
                    </div>
                    <p className="mt-2 break-all text-sm font-semibold text-primary">{storefrontUrl}</p>
                    <p className="mt-2 text-xs text-text-muted">
                      {storefrontVisible
                        ? "Customers can open this direct supplier link now, and matching store-name slugs also resolve."
                        : "This is the storefront URL that will go live once the supplier profile is approved."}
                    </p>
                  </div>
                )}

                <div className="rounded-2xl border border-border bg-surface-2 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Customer reviews</p>
                      <p className="mt-2 text-lg font-bold text-text">{reviewAverageLabel} average</p>
                      <p className="mt-1 text-sm text-text-muted">{reviewCount} total public review{reviewCount === 1 ? "" : "s"}</p>
                    </div>
                    <div className="inline-flex items-center gap-1 rounded-full border border-warning/20 bg-warning/10 px-2.5 py-1 text-[11px] font-semibold text-warning">
                      <Star className="h-3.5 w-3.5 fill-warning text-warning" />
                      {reviewCount > 0 ? "Live" : "No reviews yet"}
                    </div>
                  </div>

                  {storefrontInsightsLoading ? (
                    <p className="mt-3 text-sm text-text-muted">Loading public review snapshot...</p>
                  ) : recentPublicReviews.length > 0 ? (
                    <div className="mt-3 space-y-2">
                      {recentPublicReviews.map((review) => (
                        <div key={review.id} className="rounded-xl border border-border bg-background px-3 py-2">
                          <div className="flex items-center justify-between gap-2">
                            <p className="truncate text-xs font-semibold text-text">{review.customer_name || review.username || "Customer"}</p>
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-warning">
                              <Star className="h-3 w-3 fill-warning text-warning" />
                              {review.rating.toFixed(1)}
                            </span>
                          </div>
                          <p className="mt-1 line-clamp-2 text-xs leading-5 text-text-muted">{review.comment || "Customer left a rating without a written comment."}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm leading-6 text-text-muted">Public review insights appear here after customers submit supplier reviews on your products.</p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">About Us</label>
                  <textarea value={biz.about_us} onChange={setBizField("about_us")} placeholder="Tell customers who you are, what you sell, and why they can trust your primary." rows={5} className="theme-input w-full resize-none rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                  <p className="mt-2 text-xs leading-5 text-text-faint">
                    Use short paragraphs for your story and separate standout points with bullet lines like "- Fast custom production" to make your storefront easier to scan.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-text-muted">Established Year</label>
                    <input type="number" value={biz.established_year} onChange={setBizField("established_year")} placeholder="2018" className="theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                  </div>
                  <div className="rounded-xl border border-border bg-surface-2 p-3 text-sm text-text-muted">
                    <p className="font-semibold text-text">Public visibility</p>
                    <p className="mt-1">Only approved and verified supplier storefronts are customer-visible. Pending, draft, and under-review profiles stay private until approval is complete.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                  <div className="rounded-2xl border border-border bg-surface-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-text">Logo</p>
                        <p className="text-xs text-text-muted">Upload a square storefront logo or keep using a direct image URL.</p>
                      </div>
                      <>
                        <Button variant="secondary" className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text transition-colors hover:text-primary disabled:opacity-60" type="button" onClick={() => logoInputRef.current?.click()} disabled={uploadingMediaField === "logo_url"}>
                          <Upload className="h-3.5 w-3.5" />
                          {uploadingMediaField === "logo_url" ? "Uploading..." : "Upload"}
                        </Button>
                        <input ref={logoInputRef} type="file" accept="image/*" onChange={handleMediaSelection("logo_url")} className="hidden" />
                      </>
                    </div>
                    {biz.logo_url && (
                      <div className="mt-4 flex items-center gap-3 rounded-xl border border-border bg-background p-3">
                        <div className="h-14 w-14 overflow-hidden rounded-2xl border border-border bg-surface-2">
                          <img src={resolveImage(biz.logo_url)} alt="Storefront logo" className="h-full w-full object-cover" />
                        </div>
                        <p className="min-w-0 break-all text-xs text-text-muted">{biz.logo_url}</p>
                      </div>
                    )}
                    <div className="relative mt-4">
                      <ImageIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                      <input type="url" value={biz.logo_url} onChange={setBizField("logo_url")} placeholder="https://.../logo.png" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-text">Banner</p>
                        <p className="text-xs text-text-muted">Upload a storefront cover image or keep using a hosted banner URL.</p>
                      </div>
                      <>
                        <Button variant="secondary" className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text transition-colors hover:text-primary disabled:opacity-60" type="button" onClick={() => bannerInputRef.current?.click()} disabled={uploadingMediaField === "banner_url"}>
                          <Upload className="h-3.5 w-3.5" />
                          {uploadingMediaField === "banner_url" ? "Uploading..." : "Upload"}
                        </Button>
                        <input ref={bannerInputRef} type="file" accept="image/*" onChange={handleMediaSelection("banner_url")} className="hidden" />
                      </>
                    </div>
                    {biz.banner_url && (
                      <div className="mt-4 overflow-hidden rounded-xl border border-border bg-background">
                        <img src={resolveImage(biz.banner_url)} alt="Storefront banner" className="h-24 w-full object-cover" />
                      </div>
                    )}
                    <div className="relative mt-4">
                      <ImageIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                      <input type="url" value={biz.banner_url} onChange={setBizField("banner_url")} placeholder="https://.../banner.jpg" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-surface-2 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-text">Supplier video</p>
                      <p className="text-xs text-text-muted">Upload MP4/WebM up to 25MB or paste a YouTube/Vimeo link.</p>
                    </div>
                    <>
                      <Button variant="secondary" className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text transition-colors hover:text-primary disabled:opacity-60" type="button" onClick={() => videoInputRef.current?.click()} disabled={uploadingMediaField === "video_url"}>
                        <Upload className="h-3.5 w-3.5" />
                        {uploadingMediaField === "video_url" ? "Uploading..." : "Upload video"}
                      </Button>
                      <input ref={videoInputRef} type="file" accept="video/mp4,video/webm" onChange={handleMediaSelection("video_url")} className="hidden" />
                    </>
                  </div>
                  {biz.video_url && (
                    isUploadedVideo ? (
                      <video controls className="mt-4 aspect-video w-full rounded-xl border border-border bg-background">
                        <source src={resolvedVideoUrl} />
                      </video>
                    ) : (
                      <a href={biz.video_url} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline">
                        <ExternalLink className="h-4 w-4" />
                        Preview current video link
                      </a>
                    )
                  )}
                  <div className="relative mt-4">
                    <ExternalLink className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="url" value={biz.video_url} onChange={setBizField("video_url")} placeholder="YouTube, Vimeo, or uploaded MP4/WebM" className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-surface-2 p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-text">Certifications</p>
                      <p className="text-xs text-text-muted">Add the business credentials customers should see on your supplier page.</p>
                    </div>
                    <Button variant="secondary" type="button" onClick={addCertification}>
                      <Plus className="h-3.5 w-3.5" />
                      Add certification
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {biz.certifications.map((cert, index) => (
                      <div key={`${index}-${cert.title}`} className="rounded-xl border border-border bg-background p-3">
                        <div className="mb-3 flex items-center justify-between gap-3">
                          <p className="text-xs font-semibold text-text-muted">Certification {index + 1}</p>
                          <button type="button" onClick={() => removeCertification(index)} className="inline-flex items-center gap-1 text-[11px] font-semibold text-danger hover:opacity-80">
                            <Trash2 className="h-3.5 w-3.5" />
                            Remove
                          </button>
                        </div>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                          <input type="text" value={cert.title} onChange={updateCertification(index, "title")} placeholder="Certification title" className="theme-input rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                          <input type="text" value={cert.issuer} onChange={updateCertification(index, "issuer")} placeholder="Issuer" className="theme-input rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                          <input type="number" value={cert.year} onChange={updateCertification(index, "year")} placeholder="Year" className="theme-input rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                          <div className="space-y-3 sm:col-span-2">
                            <div className="flex flex-wrap items-center gap-3">
                              <Button variant="secondary" className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text transition-colors hover:text-primary disabled:opacity-60" type="button" onClick={() => document.getElementById(`certification-upload-${index}`)?.click()} disabled={uploadingMediaField === certificationUploadKey(index)}>
                                <Upload className="h-3.5 w-3.5" />
                                {uploadingMediaField === certificationUploadKey(index) ? "Uploading..." : "Upload certificate image"}
                              </Button>
                              {cert.image_url ? <p className="text-xs text-text-muted">Current image: {cert.image_url}</p> : null}
                            </div>
                            <input id={`certification-upload-${index}`} type="file" accept="image/*" onChange={handleMediaSelection("certification_image", index)} className="hidden" />
                            {cert.image_url ? (
                              <div className="overflow-hidden rounded-xl border border-border bg-surface-2">
                                <img src={resolveImage(cert.image_url)} alt={cert.title || `Certification ${index + 1}`} className="h-28 w-full object-contain" />
                              </div>
                            ) : null}
                            <input type="url" value={cert.image_url} onChange={updateCertification(index, "image_url")} placeholder="Certificate image URL" className="theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-surface-2 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <BadgeCheck className="h-4 w-4 text-primary" />
                    <p className="text-sm font-semibold text-text">Social links</p>
                  </div>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {([
                      ["instagram", "Instagram"],
                      ["facebook", "Facebook"],
                      ["twitter", "Twitter / X"],
                      ["linkedin", "LinkedIn"],
                      ["youtube", "YouTube"],
                      ["tiktok", "TikTok"],
                    ] as const).map(([key, label]) => (
                      <div key={key}>
                        <label className="mb-1.5 block text-xs font-semibold text-text-muted">{label}</label>
                        <input type="url" value={biz.social_links[key]} onChange={setSocialField(key)} placeholder={`https://${key}.com/...`} className="theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <button type="submit" disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary py-3 text-sm font-bold disabled:opacity-50">
                <Save className="h-4 w-4" />
                {loading ? "Saving..." : "Save storefront portfolio"}
              </button>
            </motion.form>
          )}

          {tab === "security" && (
            <motion.form initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} onSubmit={changePw} className="theme-card space-y-5 rounded-2xl border p-5">
              {[
                { label: "Current Password", value: currentPw, setter: setCurrentPw },
                { label: "New Password", value: newPw, setter: setNewPw },
                { label: "Confirm New Password", value: confirmPw, setter: setConfirmPw },
              ].map((field) => (
                <div key={field.label}>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">{field.label}</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input type="password" value={field.value} onChange={(event) => field.setter(event.target.value)} required className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
                  </div>
                </div>
              ))}
              <button type="submit" disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary py-3 text-sm font-bold disabled:opacity-50">
                <Shield className="h-4 w-4" />
                {loading ? "Changing..." : "Change password"}
              </button>
            </motion.form>
          )}

          {tab === "bank" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <div className="theme-card rounded-2xl border p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Supplier bank profile</p>
                    <h3 className="mt-2 text-lg font-bold text-text">Bank account used for supplier settlements</h3>
                    <p className="mt-2 text-sm text-text-muted">
                      Keep the destination account here. Payout status, settlement timing, and invoice records now live in the dedicated Payouts workspace.
                    </p>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${bankAccount?.verification_status === "verified" ? "theme-chip-success" : bankAccount?.verification_status === "rejected" ? "theme-chip-danger" : "theme-chip-warning"}`}>
                    {bankAccount?.verification_status || "pending review"}
                  </span>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl border border-border bg-surface-2 p-3">
                    <p className="text-xs text-text-faint">Verification state</p>
                    <div className="mt-2 flex items-center gap-2 text-sm font-semibold text-text">
                      {bankAccount?.verification_status === "verified" ? <CheckCircle className="h-4 w-4 text-success" /> : bankAccount?.verification_status === "rejected" ? <XCircle className="h-4 w-4 text-danger" /> : <Clock className="h-4 w-4 text-warning" />}
                      {bankAccount?.verification_status === "verified" ? "Ready for payout batches" : bankAccount?.verification_status === "rejected" ? "Needs correction" : "Waiting for finance review"}
                    </div>
                    <p className="mt-1 text-[10px] text-text-faint">Update the details below if finance asks for corrections.</p>
                  </div>
                  <div className="rounded-xl border border-border bg-surface-2 p-3">
                    <p className="text-xs text-text-faint">Need payout status?</p>
                    <p className="mt-2 text-sm font-semibold text-text">Open the finance workspace for settlements, invoice records, and payout requests.</p>
                    <Button variant="secondary" className="mt-3 inline-flex items-center gap-2 rounded-xl border border-border bg-surface-base px-3 py-2 text-xs font-semibold text-text-muted transition-colors hover:text-primary" type="button" onClick={() => router.push("/supplier/payouts")}>
                      <TrendingUp className="h-4 w-4" /> Open payouts workspace
                    </Button>
                  </div>
                </div>

                {bankAccount?.verification_note ? (
                  <div className="mt-4 rounded-xl border border-danger/30 bg-danger/5 p-3 text-xs text-danger">
                    <p className="font-semibold">Finance review note</p>
                    <p className="mt-1">{bankAccount.verification_note}</p>
                  </div>
                ) : null}
              </div>

              <motion.form onSubmit={saveBankAccount} className="theme-card space-y-4 rounded-2xl border p-5">
                <div>
                  <h4 className="text-base font-bold text-text">Payout bank details</h4>
                  <p className="mt-1 text-sm text-text-muted">These details feed the finance verification queue and supplier payout dispatch batches.</p>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {[
                    ["beneficiary_name", "Beneficiary Name"],
                    ["bank_name", "Bank Name"],
                    ["branch_name", "Branch / Office"],
                    ["account_number", "Account Number"],
                    ["iban", "IBAN"],
                    ["swift_code", "SWIFT / BIC"],
                    ["routing_number", "Routing Number"],
                    ["currency", "Currency"],
                    ["bank_country", "Bank Country"],
                  ].map(([field, label]) => (
                    <div key={field}>
                      <label className="mb-1.5 block text-xs font-semibold text-text-muted">{label}</label>
                      <input
                        value={bankForm[field as keyof typeof bankForm]}
                        onChange={(event) => setBankForm((current) => ({ ...current, [field]: event.target.value }))}
                        className="theme-input w-full rounded-xl border px-3 py-2 text-sm"
                      />
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-3">
                  <button type="submit" disabled={bankSaving} className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
                    <Save className="h-4 w-4" />
                    {bankSaving ? "Saving..." : bankAccount?.id ? "Update bank account" : "Save bank account"}
                  </button>
                  <button type="button" onClick={() => setBankForm({ ...EMPTY_BANK_FORM })} className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2.5 text-sm font-semibold text-text-muted hover:text-text">
                    Reset
                  </button>
                </div>
              </motion.form>
            </motion.div>
          )}

          {tab === "documents" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card space-y-4 rounded-2xl border p-5">
              <div className="rounded-2xl border border-border bg-surface-2 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">KYC workspace</p>
                <p className="mt-2 text-lg font-bold text-text">{documents.length} documents on file</p>
                <p className="mt-1 text-sm text-text-muted">{approvedDocs} approved - {pendingDocs} pending review</p>
              </div>

              <form onSubmit={handleDocUpload} className="rounded-2xl border border-border bg-surface-2 p-4 space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-text-muted">Document Type</label>
                    <select value={docForm.document_type} onChange={(event) => setDocForm((current) => ({ ...current, document_type: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-sm">
                      {DOCUMENT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-text-muted">Document Name</label>
                    <input value={docForm.document_name} onChange={(event) => setDocForm((current) => ({ ...current, document_name: event.target.value }))} placeholder="Trade License 2026" className="theme-input w-full rounded-xl border px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-text-muted">Expiry Date</label>
                    <input type="date" value={docForm.expires_at} onChange={(event) => setDocForm((current) => ({ ...current, expires_at: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-text-muted">File</label>
                    <input type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      setSelectedDocFile(file);
                      if (file && !docForm.document_name) {
                        setDocForm((current) => ({ ...current, document_name: file.name.replace(/\.[^.]+$/, "") }));
                      }
                    }} className="theme-input w-full rounded-xl border px-3 py-2 text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-surface-3 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-text" />
                  </div>
                </div>
                <button type="submit" disabled={docUploading || !selectedDocFile} className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
                  {docUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  {docUploading ? "Uploading..." : "Upload KYC document"}
                </button>
              </form>

              <div className="rounded-2xl border border-border bg-surface-2 overflow-hidden">
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <p className="text-sm font-semibold text-text">Submitted Documents</p>
                  <button type="button" onClick={fetchDocuments} className="inline-flex items-center gap-1 text-xs font-semibold text-text-muted hover:text-text">
                    <RefreshCw className={`h-3.5 w-3.5 ${docsLoading ? "animate-spin" : ""}`} /> Refresh
                  </button>
                </div>
                <div className="divide-y divide-border">
                  {documents.length > 0 ? documents.map((document) => (
                    <div key={document.id} className="px-4 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <a href={document.file_url || "#"} target="_blank" rel="noreferrer" className="text-sm font-semibold text-text hover:text-primary">
                            {document.document_name || `Document #${document.id}`}
                          </a>
                          <p className="text-xs text-text-muted capitalize">{String(document.document_type || "other").replace(/_/g, " ")}</p>
                          {document.expires_at ? <p className="text-[11px] text-text-faint">Expires {new Date(document.expires_at).toLocaleDateString()}</p> : null}
                          {document.review_note ? <p className="mt-1 text-[11px] italic text-text-muted">Note: {document.review_note}</p> : null}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`rounded-lg px-2.5 py-0.5 text-xs font-semibold ${STATUS_CHIP[document.status] || "theme-chip-muted"}`}>{String(document.status).replace(/_/g, " ")}</span>
                          {document.status === "pending" || document.status === "rejected" ? (
                            <Button variant="danger" className="rounded-lg p-1.5 text-danger transition-colors disabled:opacity-50" type="button" onClick={() => handleDocDelete(document.id)} disabled={docDeleteId === document.id}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  )) : (
                    <div className="p-4 text-sm text-text-muted">No KYC documents uploaded yet. Add your business registration and compliance files here before requesting review.</div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {tab === "coverage" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card space-y-4 rounded-2xl border p-5">
              <div className="rounded-2xl border border-border bg-surface-2 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Coverage</p>
                <p className="mt-2 text-lg font-bold text-text">{coverageDraft.operating_regions.length} active regions</p>
                <p className="mt-1 text-sm text-text-muted">Customers only discover your storefront in the regions you activate here.</p>
              </div>
              <div className="flex items-start gap-2 rounded-xl border border-info/20 bg-info/8 p-3 text-xs text-info">
                <Info className="mt-0.5 h-4 w-4 shrink-0" />
                <p>Coverage changes take effect as soon as you save. Use quick-select to add whole regions, then fine-tune individual countries below.</p>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Origin Country</label>
                  <select value={coverageDraft.origin_country} onChange={(event) => setCoverageDraft((current) => ({ ...current, origin_country: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-sm">
                    <option value="">Select country...</option>
                    {ALL_COUNTRIES.map((country) => <option key={country} value={country}>{country}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">Pickup City</label>
                  <input value={coverageDraft.city} onChange={(event) => setCoverageDraft((current) => ({ ...current, city: event.target.value }))} placeholder="Muscat" className="theme-input w-full rounded-xl border px-3 py-2 text-sm" />
                </div>
              </div>
              <div className="rounded-2xl border border-border bg-surface-2 p-4 space-y-3">
                {REGION_GROUPS.map((group) => {
                  const allSelected = group.countries.every((country) => coverageDraft.operating_regions.includes(country));
                  return (
                    <div key={group.label} className="flex items-center justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0">
                      <div>
                        <p className="text-xs font-semibold text-text">{group.label}</p>
                        <p className="text-[11px] text-text-faint">{group.countries.filter((country) => coverageDraft.operating_regions.includes(country)).length} / {group.countries.length} selected</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="primary" className="rounded-lg px-2.5 py-1 text-[10px] font-semibold text-success" type="button" onClick={() => updateCoverageGroup(group.countries, true)}>All</Button>
                        {allSelected ? <Button variant="danger" className="rounded-lg px-2.5 py-1 text-[10px] font-semibold text-danger" type="button" onClick={() => updateCoverageGroup(group.countries, false)}>Clear</Button> : null}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
                <input value={coverageSearch} onChange={(event) => setCoverageSearch(event.target.value)} placeholder="Search countries..." className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-sm" />
              </div>
              <div className="grid max-h-72 grid-cols-2 gap-1.5 overflow-y-auto pr-1 sm:grid-cols-3">
                {filteredCoverageCountries.map((country) => {
                  const active = coverageDraft.operating_regions.includes(country);
                  return (
                    <button key={country} type="button" onClick={() => toggleCoverageCountry(country)} className={`rounded-lg border px-2.5 py-2 text-left text-[11px] font-medium transition-all ${active ? "border-success/30 bg-success/15 text-success" : "border-transparent bg-surface-2 text-text-muted hover:border-border hover:text-text"}`}>
                      {country}
                    </button>
                  );
                })}
              </div>
              {coverageDraft.operating_regions.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {coverageDraft.operating_regions.slice().sort().map((country) => (
                    <Button variant="primary" className="rounded-full border border-success/25 px-3 py-1 text-[10px] font-semibold text-success" key={country} type="button" onClick={() => toggleCoverageCountry(country)}>
                      {country}
                    </Button>
                  ))}
                </div>
              ) : null}
              <div className="flex items-center justify-between gap-3">
                {coverageSaved ? <span className="text-xs font-semibold text-success">Coverage saved successfully</span> : <span />}
                <button type="button" onClick={saveCoverage} disabled={coverageSaving} className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
                  {coverageSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                  Save Coverage
                </button>
              </div>
            </motion.div>
          )}

          {tab === "terms" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card space-y-4 rounded-2xl border p-5">
              <div className="rounded-2xl border border-border bg-surface-2 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Terms & compliance</p>
                <p className="mt-2 text-lg font-bold text-text">{biz.is_terms_accepted ? "Terms already accepted" : "Terms still need review"}</p>
                <p className="mt-1 text-sm text-text-muted">
                  {biz.is_terms_accepted
                    ? `Version ${biz.terms_version || "current"} accepted ${biz.terms_accepted_at ? `on ${new Date(biz.terms_accepted_at).toLocaleDateString()}` : "recently"}.`
                    : "Acceptance is required before the supplier account can operate without compliance blockers."}
                </p>
              </div>
              <div className="space-y-2 rounded-2xl border border-border bg-surface-2 p-4 text-sm text-text-muted">
                <p>Keep business identity, pickup location, and operating regions accurate.</p>
                <p>Use parcel proof and verified handoff events for Prepared and Shipped transitions.</p>
                <p>Maintain KYC documents whenever ownership, licensing, or tax details change.</p>
              </div>
              <div className="rounded-2xl border border-border bg-surface-2 p-4 space-y-4 text-sm text-text-muted">
                {TERMS_SECTIONS.map((section) => (
                  <div key={section.title}>
                    <p className="font-semibold text-text">{section.title}</p>
                    <p className="mt-1">{section.body}</p>
                  </div>
                ))}
              </div>
              {!biz.is_terms_accepted ? (
                <button type="button" onClick={acceptTerms} disabled={termsAccepting} className="inline-flex items-center justify-center gap-2 rounded-xl theme-btn-primary px-4 py-3 text-sm font-semibold disabled:opacity-50">
                  {termsAccepting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                  {termsAccepting ? "Accepting..." : "I Accept these Terms & Conditions"}
                </button>
              ) : null}
            </motion.div>
          )}

          {tab === "guide" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card space-y-4 rounded-2xl border p-5">
              <div className="rounded-2xl border border-primary/20 bg-primary/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Supplier guide</p>
                <p className="mt-2 text-lg font-bold text-text">Profile, Product Management, Orders, Reports, and Payouts now work as one system.</p>
                <p className="mt-1 text-sm text-text-muted">Use this tab for the operational summary, then open the full guide when you want the complete walkthrough.</p>
              </div>
              <div className="rounded-2xl border border-border bg-surface-2 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Quick checklist</p>
                <div className="mt-3 space-y-2">
                  {GUIDE_CHECKLIST.map((item) => (
                    <div key={item} className="flex items-start gap-2 rounded-xl border border-border bg-background px-3 py-2 text-sm text-text-muted">
                      <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-border bg-surface-2 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Operational tips</p>
                <div className="mt-3 space-y-2 text-sm text-text-muted">
                  {GUIDE_TIPS.map((tip) => (
                    <p key={tip}>{tip}</p>
                  ))}
                </div>
              </div>
              <div id="full-guide" className="rounded-2xl border border-border bg-surface-2 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Detailed walkthrough</p>
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  {GUIDE_WALKTHROUGH.map((section) => (
                    <div key={section.title} className="rounded-xl border border-border bg-background p-4">
                      <p className="text-sm font-semibold text-text">{section.title}</p>
                      <p className="mt-2 text-sm text-text-muted">{section.body}</p>
                    </div>
                  ))}
                </div>
              </div>
              <a href="#full-guide" className="inline-flex rounded-xl theme-btn-primary px-3 py-2 text-xs font-semibold">
                Open full supplier guide
              </a>
            </motion.div>
          )}
        </div>

        <div className="space-y-4">
          <div className="theme-card rounded-2xl border p-5">
            <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <User className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-center font-bold text-text">{user?.username || "Supplier"}</h3>
            <p className="mb-1 text-center text-xs text-text-muted">{user?.email}</p>
            {biz.business_name && <p className="mb-3 text-center text-xs font-semibold text-primary">{biz.business_name}</p>}

            <div className="mb-4 rounded-2xl border border-border bg-surface-2 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Storefront readiness</p>
              <p className="mt-2 text-sm font-semibold text-text">{storefrontReady ? "Ready for customers" : "Needs more public content"}</p>
              <p className="mt-1 text-xs text-text-muted">Add your About Us, storefront visuals, and certifications so customers can see a complete supplier page.</p>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-background">
                <div className="h-full rounded-full bg-gradient-to-r from-primary via-primary to-accent" style={{ width: `${storefrontCompletionPercent}%` }} />
              </div>
              <p className="mt-2 text-[11px] text-text-faint">{completedStorefrontItems} of {storefrontChecklist.length} essentials complete.</p>
            </div>

            <div className="mb-4 rounded-2xl border border-border bg-surface-2 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Storefront essentials</p>
              <div className="mt-3 space-y-2">
                {storefrontChecklist.map((item) => (
                  <div key={item.label} className="flex items-center justify-between rounded-xl border border-border bg-background px-3 py-2">
                    <span className="text-xs text-text-muted">{item.label}</span>
                    {item.done ? (
                      <CheckCircle className="h-4 w-4 text-success" />
                    ) : (
                      <Clock className="h-4 w-4 text-text-faint" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {storefrontUrl && (
              <div className="mb-4 rounded-2xl border border-border bg-surface-2 p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Public link</p>
                <p className="mt-2 break-all text-xs font-semibold text-primary">{storefrontUrl}</p>
                <p className="mt-1 text-[11px] text-text-muted">{storefrontVisible ? "Use this direct supplier URL when sharing your storefront." : "This URL becomes customer-visible after approval."}</p>
              </div>
            )}

            <div className="space-y-3">
              {[
                { icon: Package, label: "Products", value: products.length },
                { icon: TrendingUp, label: "Total Sales", value: totalSales },
                { icon: DollarSign, label: "Revenue", value: formatPrice(totalRevenue) },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-xl border border-border bg-surface-2 p-3">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-4 w-4 text-text-faint" />
                    <span className="text-xs text-text-muted">{item.label}</span>
                  </div>
                  <span className="text-xs font-bold text-text">{item.value}</span>
                </div>
              ))}
            </div>

            {storefrontUrl && storefrontVisible ? (
              <a href={storefrontUrl} target="_blank" rel="noreferrer" className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-primary/20 bg-primary/10 px-4 py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-primary/15">
                <Eye className="h-4 w-4" />
                View public supplier page
              </a>
            ) : storefrontUrl ? (
              <div className="mt-4 rounded-xl border border-warning/20 bg-warning/10 px-4 py-3 text-center text-xs font-semibold text-warning">
                Your public storefront link will activate after approval.
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </SupplierLayout>
  );
}

export default function SupplierProfilePage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <SupplierProfilePageContent />
    </Suspense>
  );
}



