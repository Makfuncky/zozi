import React, { useEffect, useRef, useState } from "react";
import { View, Text, ScrollView, KeyboardAvoidingView, Platform, StyleSheet, ActivityIndicator, Alert, TouchableOpacity } from "react-native";

import { Stack, router } from "expo-router";
import * as DocumentPicker from "expo-document-picker";
import { apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { toast } from "@/lib/toastStore";
import { buildSupplierStorefrontSlug } from "@shared/utils";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: { padding: theme.spacing.md, gap: 14, paddingBottom: 40, alignItems: "stretch" },
  actionStrip: { gap: 8, paddingBottom: 4 },
  actionChip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8 },
  optionRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  optionChip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8 },
  smallLabel: { fontSize: 12, fontWeight: "700" },
  helperBox: { borderRadius: 12, borderWidth: 1, padding: 12, gap: 6 },
  documentRow: { borderRadius: theme.radius.lg, borderWidth: 1, padding: theme.spacing.sm, gap: 8 },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "center",
    marginBottom: theme.spacing.xs,
  },
  avatarText: { color: "#fff", fontSize: theme.fontSize.xl, fontWeight: "700" },
  sectionTitle: { fontSize: theme.fontSize.md, fontWeight: "700", paddingHorizontal: theme.spacing.xs },
  card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 14 },
  errorBox: { borderWidth: 1, borderRadius: 10, padding: 12 },
  statusPill: { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6, alignSelf: "flex-start" },
  certificationRow: { borderRadius: theme.radius.lg, borderWidth: 1, padding: theme.spacing.sm, gap: 10 },
  heroCard: { gap: 14 },
  heroHeader: { flexDirection: "row", alignItems: "center", gap: 12 },
  heroCopy: { flex: 1, gap: 4 },
  progressTrack: { height: 8, borderRadius: 999, overflow: "hidden" },
  progressFill: { height: "100%", borderRadius: 999 },
  metricsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  metricCard: { flexGrow: 1, minWidth: 100, borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
  metricValue: { fontSize: theme.fontSize.lg, fontWeight: "800" },
  metricLabel: { fontSize: theme.fontSize.xs },
});

interface CertificationForm {
  title: string;
  issuer: string;
  year: string;
  image_url: string;
}

interface SocialLinksForm {
  instagram: string;
  facebook: string;
  twitter: string;
  linkedin: string;
  youtube: string;
  tiktok: string;
}

type MediaField = "logo_url" | "banner_url" | "video_url" | "certification_image";

interface SupplierBusinessProfile {
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
  verification_status: string;
  is_terms_accepted?: boolean;
  terms_version?: string;
  terms_accepted_at?: string | null;
}

interface SupplierDocumentRecord {
  id: number;
  document_type?: string;
  document_name?: string;
  file_url?: string;
  status: string;
  review_note?: string | null;
  expires_at?: string | null;
}

interface SupplierRegionRecord {
  origin_country?: string;
  city?: string;
  operating_regions?: string[];
}

const DOCUMENT_TYPES = [
  { value: "business_license", label: "Business License" },
  { value: "trade_license", label: "Trade License" },
  { value: "tax_certificate", label: "Tax / VAT" },
  { value: "national_id", label: "National ID" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "product_certificate", label: "Certificate" },
  { value: "insurance", label: "Insurance" },
  { value: "other", label: "Other" },
] as const;

const ALL_COUNTRIES = [
  "Afghanistan", "Albania", "Algeria", "Angola", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
  "Bahrain", "Bangladesh", "Belarus", "Belgium", "Bolivia", "Bosnia and Herzegovina", "Brazil", "Bulgaria",
  "Cambodia", "Cameroon", "Canada", "Chile", "China", "Colombia", "Croatia", "Czech Republic", "Denmark",
  "Ecuador", "Egypt", "Ethiopia", "Finland", "France", "Georgia", "Germany", "Ghana", "Greece", "Hungary",
  "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Japan", "Jordan", "Kazakhstan", "Kenya",
  "Kuwait", "Lebanon", "Libya", "Malaysia", "Mexico", "Morocco", "Myanmar", "Netherlands", "New Zealand", "Nigeria",
  "Norway", "Oman", "Pakistan", "Palestine", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
  "Saudi Arabia", "Senegal", "Serbia", "Singapore", "Somalia", "South Africa", "South Korea", "Spain", "Sri Lanka",
  "Sudan", "Sweden", "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand", "Tunisia", "Turkey", "Uganda",
  "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zimbabwe",
];

const REGION_GROUPS = [
  { label: "GCC", countries: ["Saudi Arabia", "United Arab Emirates", "Kuwait", "Qatar", "Bahrain", "Oman"] },
  { label: "MENA", countries: ["Egypt", "Jordan", "Lebanon", "Iraq", "Syria", "Yemen", "Libya", "Tunisia", "Algeria", "Morocco", "Palestine"] },
  { label: "South Asia", countries: ["India", "Pakistan", "Bangladesh", "Sri Lanka"] },
  { label: "Europe", countries: ["United Kingdom", "Germany", "France", "Netherlands", "Spain", "Italy", "Portugal", "Belgium", "Sweden", "Norway", "Finland", "Denmark"] },
  { label: "Americas", countries: ["United States", "Canada", "Brazil", "Mexico", "Argentina", "Colombia", "Chile"] },
] as const;

const TERMS_SECTIONS = [
  "You must be legally authorised to sell and fulfil products in your market.",
  "Product listings must be authentic, accurate, and compliant with applicable laws.",
  "Supplier payouts are processed after commission, refunds, and review adjustments.",
  "Prepared and shipped order states depend on real parcel proof and logistics handoff.",
  "Customer data may only be used to fulfil platform orders.",
  "Policy violations can lead to suspension or account termination.",
] as const;

const GUIDE_TIPS = [
  "Lead with clean product media so AI can infer the name, category, color, description, and tags.",
  "Keep KYC, coverage, and terms current here before requesting supplier review.",
  "Upload parcel proof from Orders when the package is prepared for carrier handoff.",
] as const;

const emptyCertification = (): CertificationForm => ({
  title: "",
  issuer: "",
  year: "",
  image_url: "",
});

const defaultProfile = (): SupplierBusinessProfile => ({
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
  verification_status: "pending",
});

function normalizeProfile(data: any): SupplierBusinessProfile {
  const base = defaultProfile();
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
    verification_status: String(data?.verification_status ?? "pending"),
  };
}

export default function SupplierProfileScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user, logout } = useAuthStore();
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const scrollRef = useRef<ScrollView>(null);
  const sectionOffsets = useRef<Record<string, number>>({});
  const [supplierProfileTitle, accountLabel, usernameLabel, supplierFallbackLabel, emailLabel, previewPublicPageLabel, profileActionsLabel, businessLocationLabel, storefrontAboutLabel, securityLabel, payoutLabel, kycDocumentsLabel, coverageLabel, termsConditionsLabel, supplierGuideLabel, workspaceSummaryLabel, kycUploadedLabel, pendingReviewLabel, coverageRegionsConfiguredLabel, supplierProfileVerifiedLabel, complianceReviewLabel, documentTypeLabel, documentNameLabel, expiryDateLabel, chooseKycFileLabel, uploadKycDocumentLabel, documentLabel, statusLabel, noteLabel, expiresLabel, deleteDocumentLabel, quickSelectLabel, originCountryLabel, pickupCityLabel, searchCountriesLabel, saveCoverageLabel, termsAcceptedLabel, acceptTermsLabel, businessBasicsLabel, businessNameLabel, businessTypeLabel, businessPhoneLabel, websiteLabel, shortBioLabel, locationContactLabel, countryLabel, regionStateLabel, cityLabel, postalCodeLabel, streetAddressLabel, taxIdLabel, publicStorefrontLabel, aboutUsLabel, establishedYearLabel, uploadLogoLabel, currentLogoLabel, logoUrlLabel, uploadBannerLabel, currentBannerLabel, bannerUrlLabel, uploadVideoLabel, videoHelpLabel, currentVideoLabel, videoUrlLabel, certificationsLabel, certificationLabel, issuerLabel, yearLabel, uploadCertificateImageLabel, certificateImageUrlLabel, removeCertificationLabel, addCertificationLabel, socialLinksLabel, saveChangesLabel, logoutLabel, storefrontMediaUploadedLabel, failedUploadMediaLabel, businessNameRequiredLabel, profileUpdatedLabel, failedUpdateProfileLabel, selectFileBeforeUploadLabel, documentNameRequiredLabel, kycDocumentUploadedLabel, failedUploadKycDocumentLabel, coverageUpdatedLabel, failedSaveCoverageLabel, deleteDocumentTitleLabel, deleteDocumentPromptLabel, cancelLabel, deleteLabel, failedDeleteDocumentLabel, termsAcceptedSuccessLabel, failedAcceptTermsLabel, logoutPromptTitleLabel, logoutPromptMessageLabel, storefrontVerifiedLabel, underReviewLabel, needsChangesLabel, draftStorefrontLabel, documentsUploadedSoFarLabel, filesWaitingReviewLabel, coverageActiveSummaryLabel, coverageUpdateHintLabel, selectedLabel, instagramLabel, facebookLabel, twitterXLabel, linkedInLabel, youTubeLabel, tikTokLabel, gccLabel, menaLabel, southAsiaLabel, europeLabel, americasLabel] = useTranslateTexts([
    "Supplier Profile",
    "Account",
    "Username",
    "Supplier",
    "Email",
    "Preview Public Page",
    "Profile Actions",
    "Business & Location",
    "Storefront & About",
    "Security",
    "Payout",
    "KYC Documents",
    "Coverage",
    "Terms & Conditions",
    "Supplier Guide",
    "Workspace Summary",
    "KYC documents uploaded",
    "pending review",
    "coverage regions configured",
    "Supplier profile verified",
    "Terms and compliance still need review",
    "Document Type",
    "Document Name",
    "Expiry Date",
    "Choose KYC File",
    "Upload KYC Document",
    "Document",
    "Status",
    "Note",
    "Expires",
    "Delete Document",
    "Quick Select",
    "Origin Country",
    "Pickup City",
    "Search Countries",
    "Save Coverage",
    "Terms accepted",
    "Accept Terms & Conditions",
    "Business Basics",
    "Business Name *",
    "Business Type",
    "Business Phone",
    "Website",
    "Short Bio",
    "Location & Contact",
    "Country",
    "Region / State",
    "City",
    "Postal Code",
    "Street Address",
    "Tax ID / VAT Number",
    "Public Storefront",
    "About Us",
    "Established Year",
    "Upload Logo",
    "Current logo",
    "Logo URL",
    "Upload Banner",
    "Current banner",
    "Banner URL",
    "Upload Video",
    "Upload MP4/WebM or keep using an external brand video link.",
    "Current video",
    "Video URL",
    "Certifications",
    "Certification",
    "Issuer",
    "Year",
    "Upload Certificate Image",
    "Certificate Image URL",
    "Remove Certification",
    "Add Certification",
    "Social Links",
    "Save Changes",
    "Logout",
    "Storefront media uploaded!",
    "Failed to upload media.",
    "Business name is required",
    "Profile updated!",
    "Failed to update profile.",
    "Select a file before uploading",
    "Document name is required",
    "KYC document uploaded",
    "Failed to upload KYC document.",
    "Coverage updated",
    "Failed to save coverage.",
    "Delete Document",
    "Delete this KYC document?",
    "Cancel",
    "Delete",
    "Failed to delete document.",
    "Terms accepted",
    "Failed to accept terms.",
    "Logout",
    "Are you sure you want to logout?",
    "Storefront verified",
    "Under review",
    "Needs changes",
    "Draft storefront",
    "documents uploaded so far.",
    "files are still waiting for compliance review.",
    "operating regions are active for customer discovery and pickup planning.",
    "Update coverage whenever your origin city or service footprint changes.",
    "Selected",
    "Instagram",
    "Facebook",
    "Twitter / X",
    "LinkedIn",
    "YouTube",
    "TikTok",
    "GCC",
    "MENA",
    "South Asia",
    "Europe",
    "Americas",
  ]);
  const translatedDocumentTypeLabels = useTranslateTexts(DOCUMENT_TYPES.map((item) => item.label));
  const translatedTermsSections = useTranslateTexts([...TERMS_SECTIONS]);
  const translatedGuideTips = useTranslateTexts([...GUIDE_TIPS]);
  const translatedRegionGroupLabels = [gccLabel, menaLabel, southAsiaLabel, europeLabel, americasLabel];

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingField, setUploadingField] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [documentCount, setDocumentCount] = useState(0);
  const [pendingDocuments, setPendingDocuments] = useState(0);
  const [regionCount, setRegionCount] = useState(0);
  const [documents, setDocuments] = useState<SupplierDocumentRecord[]>([]);
  const [regions, setRegions] = useState<SupplierRegionRecord | null>(null);
  const [docType, setDocType] = useState<string>("business_license");
  const [docName, setDocName] = useState("");
  const [docExpiry, setDocExpiry] = useState("");
  const [docFile, setDocFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [docUploading, setDocUploading] = useState(false);
  const [docDeleting, setDocDeleting] = useState<number | null>(null);
  const [coverageSearch, setCoverageSearch] = useState("");
  const [coverageSaving, setCoverageSaving] = useState(false);
  const [coverageDraft, setCoverageDraft] = useState({ origin_country: "", city: "", operating_regions: [] as string[] });
  const [termsAccepting, setTermsAccepting] = useState(false);

  const [form, setForm] = useState<SupplierBusinessProfile>(defaultProfile);

  useEffect(() => {
    Promise.all([
      apiFetch<SupplierBusinessProfile>("/supplier/profile/business").catch(() => null),
      apiFetch<SupplierDocumentRecord[]>("/supplier-documents/my").catch(() => []),
      apiFetch<SupplierRegionRecord>("/supplier/regions").catch(() => null),
    ])
      .then(([profileData, documentsData, regionsData]) => {
        setForm(profileData ? normalizeProfile(profileData) : defaultProfile());
        const docs = normalizeCollectionResponse<SupplierDocumentRecord>(documentsData as any);
        setDocuments(docs);
        setDocumentCount(docs.length);
        setPendingDocuments(docs.filter((document) => ["pending", "under_review"].includes(String(document.status))).length);
        setRegions(regionsData && typeof regionsData === "object" ? regionsData : null);
        setRegionCount(Array.isArray(regionsData?.operating_regions) ? regionsData!.operating_regions!.length : 0);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setCoverageDraft({
      origin_country: regions?.origin_country || "",
      city: regions?.city || "",
      operating_regions: Array.isArray(regions?.operating_regions) ? regions.operating_regions : [],
    });
  }, [regions]);

  function update(field: keyof SupplierBusinessProfile, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
    setError(null);
  }

  function updateSocial(field: keyof SocialLinksForm, value: string) {
    setForm((current) => ({
      ...current,
      social_links: { ...current.social_links, [field]: value },
    }));
    setError(null);
  }

  function updateCertification(index: number, field: keyof CertificationForm, value: string) {
    setForm((current) => ({
      ...current,
      certifications: current.certifications.map((cert, certIndex) =>
        certIndex === index ? { ...cert, [field]: value } : cert
      ),
    }));
    setError(null);
  }

  function addCertification() {
    setForm((current) => ({ ...current, certifications: [...current.certifications, emptyCertification()] }));
  }

  function removeCertification(index: number) {
    setForm((current) => {
      const next = current.certifications.filter((_, certIndex) => certIndex !== index);
      return { ...current, certifications: next.length > 0 ? next : [emptyCertification()] };
    });
  }

  function certificationUploadKey(index: number) {
    return `certification_image:${index}`;
  }

  async function pickAndUploadMedia(field: MediaField, type: "image/*" | "video/*", index?: number) {
    const fieldLabels: Record<MediaField, string> = {
      logo_url: "logo",
      banner_url: "banner",
      video_url: "video",
      certification_image: "certification image",
    };

    try {
      const result = await DocumentPicker.getDocumentAsync({
        type,
        copyToCacheDirectory: true,
      });
      if (result.canceled || !result.assets?.length) return;

      const asset = result.assets[0];
      setUploadingField(field === "certification_image" && index != null ? certificationUploadKey(index) : field);
      setError(null);

      const formData = new FormData();
      formData.append("field", field);
      if (field === "certification_image" && index != null) {
        formData.append("index", String(index));
      }
      formData.append("file", {
        uri: asset.uri,
        name: asset.name || `${fieldLabels[field]}.${field === "video_url" ? "mp4" : "jpg"}`,
        type: asset.mimeType || (field === "video_url" ? "video/mp4" : "image/jpeg"),
      } as any);

      const response = await apiFetch<{ profile?: SupplierBusinessProfile }>("/supplier/profile/business/media", {
        method: "POST",
        body: formData,
      });

      if (field === "certification_image" && index != null) {
        setForm((current) => {
          const next = normalizeProfile(response.profile ?? response);
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
        setForm(normalizeProfile(response.profile ?? response));
      }
      toast.success(storefrontMediaUploadedLabel);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : failedUploadMediaLabel);
    } finally {
      setUploadingField(null);
    }
  }

  async function handleSave() {
    if (!form.business_name.trim()) return setError(businessNameRequiredLabel);
    setSaving(true);
    setError(null);

    const certifications = form.certifications
      .map((cert) => ({
        title: cert.title.trim(),
        issuer: cert.issuer.trim() || undefined,
        year: cert.year.trim() ? Number(cert.year.trim()) : undefined,
        image_url: cert.image_url.trim() || undefined,
      }))
      .filter((cert) => cert.title);

    const social_links = Object.fromEntries(
      Object.entries(form.social_links)
        .map(([platform, url]) => [platform, url.trim()])
        .filter(([, url]) => Boolean(url))
    );

    try {
      const response = await apiFetch<SupplierBusinessProfile>("/supplier/profile/business", {
        method: "PUT",
        body: JSON.stringify({
          business_name: form.business_name.trim() || undefined,
          business_type: form.business_type.trim() || undefined,
          country: form.country.trim() || undefined,
          region: form.region.trim() || undefined,
          city: form.city.trim() || undefined,
          address: form.address.trim() || undefined,
          postal_code: form.postal_code.trim() || undefined,
          phone_business: form.phone_business.trim() || undefined,
          website: form.website.trim() || undefined,
          tax_id: form.tax_id.trim() || undefined,
          bio: form.bio.trim() || undefined,
          about_us: form.about_us.trim() || undefined,
          logo_url: form.logo_url.trim() || undefined,
          banner_url: form.banner_url.trim() || undefined,
          video_url: form.video_url.trim() || undefined,
          established_year: form.established_year.trim() ? Number(form.established_year.trim()) : undefined,
          certifications,
          social_links,
        }),
      });
      setForm(normalizeProfile(response));
      toast.success(profileUpdatedLabel);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : failedUpdateProfileLabel);
    } finally {
      setSaving(false);
    }
  }

  async function refreshDocuments() {
    const docs = await apiFetch<any>("/supplier-documents/my").catch(() => []);
    const list = normalizeCollectionResponse<SupplierDocumentRecord>(docs);
    setDocuments(list);
    setDocumentCount(list.length);
    setPendingDocuments(list.filter((document) => ["pending", "under_review"].includes(String(document.status))).length);
  }

  async function pickKycFile() {
    const result = await DocumentPicker.getDocumentAsync({ type: ["application/pdf", "image/*"], copyToCacheDirectory: true });
    if (result.canceled || !result.assets?.length) return;
    const asset = result.assets[0];
    setDocFile(asset);
    if (!docName.trim()) setDocName(asset.name.replace(/\.[^.]+$/, ""));
  }

  async function uploadKycDocument() {
    if (!docFile) return setError(selectFileBeforeUploadLabel);
    if (!docName.trim()) return setError(documentNameRequiredLabel);

    try {
      setDocUploading(true);
      setError(null);
      const formData = new FormData();
      formData.append("file", {
        uri: docFile.uri,
        name: docFile.name || "document.pdf",
        type: docFile.mimeType || "application/octet-stream",
      } as any);
      formData.append("document_type", docType);
      formData.append("document_name", docName.trim());
      if (docExpiry.trim()) formData.append("expires_at", new Date(docExpiry.trim()).toISOString());

      await apiFetch("/supplier-documents/my/upload", { method: "POST", body: formData });
      setDocFile(null);
      setDocName("");
      setDocExpiry("");
      setDocType("business_license");
      await refreshDocuments();
      toast.success(kycDocumentUploadedLabel);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : failedUploadKycDocumentLabel);
    } finally {
      setDocUploading(false);
    }
  }

  function removeCoverageCountry(country: string) {
    setCoverageDraft((current) => ({
      ...current,
      operating_regions: current.operating_regions.includes(country)
        ? current.operating_regions.filter((item) => item !== country)
        : [...current.operating_regions, country],
    }));
  }

  function applyCoverageGroup(countries: readonly string[], add: boolean) {
    setCoverageDraft((current) => {
      const next = new Set(current.operating_regions);
      countries.forEach((country) => {
        if (add) next.add(country);
        else next.delete(country);
      });
      return { ...current, operating_regions: Array.from(next) };
    });
  }

  async function saveCoverage() {
    try {
      setCoverageSaving(true);
      setError(null);
      const response = await apiFetch<SupplierRegionRecord>("/supplier/regions", {
        method: "PUT",
        body: JSON.stringify(coverageDraft),
      });
      setRegions(response);
      setRegionCount(Array.isArray(response?.operating_regions) ? response.operating_regions.length : 0);
      toast.success(coverageUpdatedLabel);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : failedSaveCoverageLabel);
    } finally {
      setCoverageSaving(false);
    }
  }

  async function confirmDeleteDocument(id: number) {
    Alert.alert(deleteDocumentTitleLabel, deleteDocumentPromptLabel, [
      { text: cancelLabel, style: "cancel" },
      {
        text: deleteLabel,
        style: "destructive",
        onPress: async () => {
          try {
            setDocDeleting(id);
            await apiFetch(`/supplier-documents/my/${id}`, { method: "DELETE" });
            await refreshDocuments();
          } catch (err: unknown) {
            setError(err instanceof Error ? err.message : failedDeleteDocumentLabel);
          } finally {
            setDocDeleting(null);
          }
        },
      },
    ]);
  }

  async function acceptTerms() {
    try {
      setTermsAccepting(true);
      setError(null);
      const response = await apiFetch<{ terms_version?: string }>("/supplier/terms/accept", { method: "POST" });
      setForm((current) => ({
        ...current,
        is_terms_accepted: true,
        terms_version: response?.terms_version || current.terms_version,
        terms_accepted_at: new Date().toISOString(),
      }));
      toast.success(termsAcceptedSuccessLabel);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : failedAcceptTermsLabel);
    } finally {
      setTermsAccepting(false);
    }
  }

  function handleLogout() {
    Alert.alert(logoutPromptTitleLabel, logoutPromptMessageLabel, [
      { text: cancelLabel, style: "cancel" },
      { text: logoutLabel, style: "destructive", onPress: logout },
    ]);
  }

  function scrollToSection(key: string) {
    const y = sectionOffsets.current[key];
    if (typeof y === "number") {
      scrollRef.current?.scrollTo({ y: Math.max(y - 12, 0), animated: true });
    }
  }

  function getStatusLabel() {
    switch (form.verification_status) {
      case "approved":
      case "verified":
        return { label: storefrontVerifiedLabel, color: theme.colors.success + "22", text: theme.colors.success };
      case "under_review":
        return { label: underReviewLabel, color: theme.colors.warning + "22", text: theme.colors.warning };
      case "rejected":
        return { label: needsChangesLabel, color: theme.colors.danger + "22", text: theme.colors.danger };
      default:
        return { label: draftStorefrontLabel, color: theme.colors.surface2, text: theme.colors.textMuted };
    }
  }

  if (loading) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: supplierProfileTitle }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  const status = getStatusLabel();
  const storefrontSlug = buildSupplierStorefrontSlug({ business_name: form.business_name, username: user?.username });
  const filteredCountries = coverageSearch
    ? ALL_COUNTRIES.filter((country) => country.toLowerCase().includes(coverageSearch.toLowerCase()))
    : ALL_COUNTRIES;
  const profileChecklist = [
    Boolean(form.business_name.trim()),
    Boolean(form.country.trim() && form.city.trim()),
    Boolean(form.about_us.trim()),
    Boolean(form.logo_url.trim() || form.banner_url.trim()),
    documentCount > 0,
    regionCount > 0,
    Boolean(form.is_terms_accepted),
  ];
  const completedProfileChecklistCount = profileChecklist.filter(Boolean).length;
  const profileCompletion = Math.round((completedProfileChecklistCount / profileChecklist.length) * 100);
  const nextProfileStep = !form.business_name.trim()
    ? "Add your business name and core contact details so the storefront can be reviewed."
    : documentCount === 0
      ? "Upload at least one KYC document so compliance can start reviewing your account."
      : regionCount === 0
        ? "Set your origin city and operating regions so pickup planning works correctly."
        : !form.is_terms_accepted
          ? "Accept the supplier terms to unlock a complete verification review."
          : !form.about_us.trim()
            ? "Add your About Us copy so customers understand your brand faster."
            : "Your workspace is in good shape. Keep media and compliance details current as the business evolves.";

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <Stack.Screen options={{ title: supplierProfileTitle }} />
      <ScrollView
        ref={scrollRef}
        style={[s.container, isRtl ? { direction: "rtl" } : undefined]}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={[styles.card, styles.heroCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={styles.heroHeader}>
            <View style={[styles.avatar, { backgroundColor: theme.colors.brand, marginBottom: 0 }]}>
              <Text style={styles.avatarText}>
                {(form.business_name || user?.username || supplierFallbackLabel).charAt(0).toUpperCase()}
              </Text>
            </View>
            <View style={styles.heroCopy}>
              <Text style={[s.text, { fontWeight: "800", fontSize: theme.fontSize.xl }]}>{form.business_name || user?.username || supplierFallbackLabel}</Text>
              <Text style={s.textMuted}>{form.city && form.country ? `${form.city}, ${form.country}` : "Complete the essentials below to strengthen trust, routing, and review speed."}</Text>
              <View style={[styles.statusPill, { backgroundColor: status.color }]}>
                <Text style={{ color: status.text, fontWeight: "700", fontSize: 12 }}>{status.label}</Text>
              </View>
            </View>
          </View>
          <View style={[styles.progressTrack, { backgroundColor: theme.colors.surface2 }]}>
            <View style={[styles.progressFill, { width: `${profileCompletion}%`, backgroundColor: theme.colors.brand }]} />
          </View>
          <Text style={s.textMuted}>{profileCompletion}% workspace completion</Text>
          <View style={styles.metricsRow}>
            <View style={[styles.metricCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>{documentCount}</Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>KYC files</Text>
            </View>
            <View style={[styles.metricCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>{regionCount}</Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Coverage regions</Text>
            </View>
            <View style={[styles.metricCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>{pendingDocuments}</Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Pending reviews</Text>
            </View>
          </View>
          <View style={[styles.helperBox, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
            <Text style={[styles.smallLabel, { color: theme.colors.text }]}>Next step</Text>
            <Text style={s.textMuted}>{nextProfileStep}</Text>
          </View>
        </View>

        {error && (
          <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
            <Text style={{ color: theme.colors.danger }}>{error}</Text>
          </View>
        )}

        <Text style={[s.text, styles.sectionTitle]}>{accountLabel}</Text>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View>
            <Text style={s.textMuted}>{usernameLabel}</Text>
            <Text style={[s.text, { fontWeight: "600" }]}>{user?.username ?? supplierFallbackLabel}</Text>
          </View>
          <View>
            <Text style={s.textMuted}>{emailLabel}</Text>
            <Text style={[s.text, { fontWeight: "600" }]}>{user?.email ?? "-"}</Text>
          </View>
          <View style={[styles.statusPill, { backgroundColor: status.color }]}>
            <Text style={{ color: status.text, fontWeight: "700", fontSize: 12 }}>{status.label}</Text>
          </View>
          {storefrontSlug ? <Button label={previewPublicPageLabel} onPress={() => router.push(`/suppliers/${storefrontSlug}`)} variant="secondary" /> : null}
        </View>

        <Text style={[s.text, styles.sectionTitle]}>{profileActionsLabel}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.actionStrip}>
          {[
            { label: accountLabel, action: () => scrollToSection("account") },
            { label: businessLocationLabel, action: () => scrollToSection("business") },
            { label: storefrontAboutLabel, action: () => scrollToSection("storefront") },
            { label: securityLabel, action: () => router.push("/change-password" as never) },
            { label: payoutLabel, action: () => router.push("/supplier/payouts" as never) },
            { label: kycDocumentsLabel, action: () => scrollToSection("documents") },
            { label: coverageLabel, action: () => scrollToSection("coverage") },
            { label: termsConditionsLabel, action: () => scrollToSection("terms") },
            { label: supplierGuideLabel, action: () => scrollToSection("guide") },
          ].map((item) => (
            <TouchableOpacity
              key={item.label}
              onPress={item.action}
              style={[styles.actionChip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
            >
              <Text style={[s.text, { fontSize: 12, fontWeight: "700" }]}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700" }]}>{workspaceSummaryLabel}</Text>
          <Text style={s.textMuted}>{documentCount} {kycUploadedLabel} · {pendingDocuments} {pendingReviewLabel}</Text>
          <Text style={s.textMuted}>{regionCount} {coverageRegionsConfiguredLabel}</Text>
          <Text style={s.textMuted}>{form.verification_status === "approved" || form.verification_status === "verified" ? supplierProfileVerifiedLabel : complianceReviewLabel}</Text>
        </View>

        <View onLayout={(event) => { sectionOffsets.current.documents = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{kycDocumentsLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={s.textMuted}>{documentCount} {documentsUploadedSoFarLabel}</Text>
          <Text style={s.textMuted}>{pendingDocuments} {filesWaitingReviewLabel}</Text>
          <Text style={[s.textMuted, { fontWeight: "700" }]}>{documentTypeLabel}</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.optionRow}>
            {DOCUMENT_TYPES.map((item) => {
              const active = docType === item.value;
              return (
                <TouchableOpacity key={item.value} onPress={() => setDocType(item.value)} style={[styles.optionChip, { borderColor: active ? theme.colors.brand : theme.colors.border, backgroundColor: active ? theme.colors.brand + "18" : theme.colors.surface2 }]}>
                  <Text style={[s.text, { fontSize: 12, fontWeight: "700", color: active ? theme.colors.brand : theme.colors.text }]}>{translatedDocumentTypeLabels[DOCUMENT_TYPES.indexOf(item)] || item.label}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
          <Input label={documentNameLabel} value={docName} onChangeText={setDocName} placeholder="Trade License 2026" />
          <Input label={expiryDateLabel} value={docExpiry} onChangeText={setDocExpiry} placeholder="2026-12-31" />
          <Button label={docFile ? `${selectedLabel}: ${docFile.name}` : chooseKycFileLabel} onPress={pickKycFile} variant="secondary" />
          <Button label={uploadKycDocumentLabel} onPress={uploadKycDocument} loading={docUploading} />
          {documents.map((document) => {
            const canDelete = ["pending", "rejected"].includes(String(document.status));
            return (
              <View key={document.id} style={[styles.documentRow, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
                <Text style={[s.text, { fontWeight: "700" }]}>{document.document_name || `${documentLabel} #${document.id}`}</Text>
                <Text style={s.textMuted}>{String(document.document_type || "other").replace(/_/g, " ")}</Text>
                <Text style={s.textMuted}>{statusLabel}: {String(document.status).replace(/_/g, " ")}</Text>
                {document.review_note ? <Text style={s.textMuted}>{noteLabel}: {document.review_note}</Text> : null}
                {document.expires_at ? <Text style={s.textMuted}>{expiresLabel}: {formatLocalizedDate(document.expires_at, locale, { year: "numeric", month: "short", day: "numeric" })}</Text> : null}
                {canDelete ? <Button label={deleteDocumentLabel} onPress={() => confirmDeleteDocument(document.id)} variant="danger" loading={docDeleting === document.id} /> : null}
              </View>
            );
          })}
        </View>

        <View onLayout={(event) => { sectionOffsets.current.coverage = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{coverageLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={s.textMuted}>{regionCount} {coverageActiveSummaryLabel}</Text>
          <Text style={s.textMuted}>{coverageUpdateHintLabel}</Text>
          <Input label={originCountryLabel} value={coverageDraft.origin_country} onChangeText={(value) => setCoverageDraft((current) => ({ ...current, origin_country: value }))} placeholder="Oman" />
          <Input label={pickupCityLabel} value={coverageDraft.city} onChangeText={(value) => setCoverageDraft((current) => ({ ...current, city: value }))} placeholder="Muscat" />
          <Text style={[s.textMuted, { fontWeight: "700" }]}>{quickSelectLabel}</Text>
          <View style={styles.optionRow}>
            {REGION_GROUPS.map((group) => {
              const activeCount = group.countries.filter((country) => coverageDraft.operating_regions.includes(country)).length;
              return (
                <TouchableOpacity key={group.label} onPress={() => applyCoverageGroup(group.countries, activeCount !== group.countries.length)} style={[styles.optionChip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
                  <Text style={[s.text, { fontSize: 12, fontWeight: "700" }]}>{translatedRegionGroupLabels[REGION_GROUPS.indexOf(group)] || group.label} ({activeCount}/{group.countries.length})</Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <Input label={searchCountriesLabel} value={coverageSearch} onChangeText={setCoverageSearch} placeholder="Search regions" />
          <View style={styles.optionRow}>
            {filteredCountries.map((country) => {
              const active = coverageDraft.operating_regions.includes(country);
              return (
                <TouchableOpacity key={country} onPress={() => removeCoverageCountry(country)} style={[styles.optionChip, { borderColor: active ? theme.colors.success : theme.colors.border, backgroundColor: active ? theme.colors.success + "18" : theme.colors.surface2 }]}>
                  <Text style={[s.text, { fontSize: 12, fontWeight: "700", color: active ? theme.colors.success : theme.colors.text }]}>{country}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <Button label={saveCoverageLabel} onPress={saveCoverage} loading={coverageSaving} />
        </View>

        <View onLayout={(event) => { sectionOffsets.current.terms = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{termsConditionsLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={[styles.helperBox, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
            {translatedTermsSections.map((line, index) => <Text key={TERMS_SECTIONS[index]} style={s.textMuted}>{line}</Text>)}
          </View>
          {form.is_terms_accepted ? (
            <Text style={[s.text, { color: theme.colors.success, fontWeight: "700" }]}>{termsAcceptedLabel}{form.terms_version ? ` · ${form.terms_version}` : ""}</Text>
          ) : (
            <Button label={acceptTermsLabel} onPress={acceptTerms} loading={termsAccepting} />
          )}
        </View>

        <View onLayout={(event) => { sectionOffsets.current.guide = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{supplierGuideLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          {translatedGuideTips.map((tip, index) => <Text key={GUIDE_TIPS[index]} style={s.textMuted}>{tip}</Text>)}
        </View>

        <View onLayout={(event) => { sectionOffsets.current.account = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{businessBasicsLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input label={businessNameLabel} value={form.business_name} onChangeText={(t) => update("business_name", t)} placeholder="Dream Mart" />
          <Input label={businessTypeLabel} value={form.business_type} onChangeText={(t) => update("business_type", t)} placeholder="company" />
          <Input label={businessPhoneLabel} value={form.phone_business} onChangeText={(t) => update("phone_business", t)} placeholder="+968 ..." keyboardType="phone-pad" />
          <Input label={websiteLabel} value={form.website} onChangeText={(t) => update("website", t)} placeholder="https://dreammart.example" autoCapitalize="none" />
          <Input label={shortBioLabel} value={form.bio} onChangeText={(t) => update("bio", t)} placeholder="Short summary shown in supplier cards and search." multiline numberOfLines={3} />
        </View>

        <View onLayout={(event) => { sectionOffsets.current.business = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{locationContactLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input label={countryLabel} value={form.country} onChangeText={(t) => update("country", t)} placeholder="Oman" />
          <Input label={regionStateLabel} value={form.region} onChangeText={(t) => update("region", t)} placeholder="Muscat" />
          <Input label={cityLabel} value={form.city} onChangeText={(t) => update("city", t)} placeholder="Muscat" />
          <Input label={postalCodeLabel} value={form.postal_code} onChangeText={(t) => update("postal_code", t)} placeholder="112" />
          <Input label={streetAddressLabel} value={form.address} onChangeText={(t) => update("address", t)} placeholder="Building, street, area" multiline numberOfLines={2} />
          <Input label={taxIdLabel} value={form.tax_id} onChangeText={(t) => update("tax_id", t)} placeholder="Registration number" />
        </View>

        <View onLayout={(event) => { sectionOffsets.current.storefront = event.nativeEvent.layout.y; }}>
          <Text style={[s.text, styles.sectionTitle]}>{publicStorefrontLabel}</Text>
        </View>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input label={aboutUsLabel} value={form.about_us} onChangeText={(t) => update("about_us", t)} placeholder="Tell customers who you are, what you specialize in, and why they should trust your brand." multiline numberOfLines={5} />
          <Input label={establishedYearLabel} value={form.established_year} onChangeText={(t) => update("established_year", t)} placeholder="2018" keyboardType="numeric" />
          <View style={{ gap: 10 }}>
            <Button label={uploadLogoLabel} onPress={() => pickAndUploadMedia("logo_url", "image/*")} variant="secondary" loading={uploadingField === "logo_url"} />
            {form.logo_url ? <Text style={s.textMuted}>{currentLogoLabel}: {form.logo_url}</Text> : null}
          </View>
          <Input label={logoUrlLabel} value={form.logo_url} onChangeText={(t) => update("logo_url", t)} placeholder="https://.../logo.png" autoCapitalize="none" />
          <View style={{ gap: 10 }}>
            <Button label={uploadBannerLabel} onPress={() => pickAndUploadMedia("banner_url", "image/*")} variant="secondary" loading={uploadingField === "banner_url"} />
            {form.banner_url ? <Text style={s.textMuted}>{currentBannerLabel}: {form.banner_url}</Text> : null}
          </View>
          <Input label={bannerUrlLabel} value={form.banner_url} onChangeText={(t) => update("banner_url", t)} placeholder="https://.../banner.jpg" autoCapitalize="none" />
          <View style={{ gap: 10 }}>
            <Button label={uploadVideoLabel} onPress={() => pickAndUploadMedia("video_url", "video/*")} variant="secondary" loading={uploadingField === "video_url"} />
            <Text style={s.textMuted}>{videoHelpLabel}</Text>
            {form.video_url ? <Text style={s.textMuted}>{currentVideoLabel}: {form.video_url}</Text> : null}
          </View>
          <Input label={videoUrlLabel} value={form.video_url} onChangeText={(t) => update("video_url", t)} placeholder="https://youtube.com/..." autoCapitalize="none" />
        </View>

        <Text style={[s.text, styles.sectionTitle]}>{certificationsLabel}</Text>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          {form.certifications.map((cert, index) => (
            <View key={`${index}-${cert.title}`} style={[styles.certificationRow, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
              <Input label={`${certificationLabel} ${index + 1}`} value={cert.title} onChangeText={(t) => updateCertification(index, "title", t)} placeholder="Certificate title" />
              <Input label={issuerLabel} value={cert.issuer} onChangeText={(t) => updateCertification(index, "issuer", t)} placeholder={issuerLabel} />
              <Input label={yearLabel} value={cert.year} onChangeText={(t) => updateCertification(index, "year", t)} placeholder="2024" keyboardType="numeric" />
              <Button label={uploadCertificateImageLabel} onPress={() => pickAndUploadMedia("certification_image", "image/*", index)} variant="secondary" loading={uploadingField === certificationUploadKey(index)} />
              <Input label={certificateImageUrlLabel} value={cert.image_url} onChangeText={(t) => updateCertification(index, "image_url", t)} placeholder="https://.../certificate.jpg" autoCapitalize="none" />
              <Button label={removeCertificationLabel} onPress={() => removeCertification(index)} variant="secondary" />
            </View>
          ))}
          <Button label={addCertificationLabel} onPress={addCertification} variant="secondary" />
        </View>

        <Text style={[s.text, styles.sectionTitle]}>{socialLinksLabel}</Text>
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input label={instagramLabel} value={form.social_links.instagram} onChangeText={(t) => updateSocial("instagram", t)} placeholder="https://instagram.com/..." autoCapitalize="none" />
          <Input label={facebookLabel} value={form.social_links.facebook} onChangeText={(t) => updateSocial("facebook", t)} placeholder="https://facebook.com/..." autoCapitalize="none" />
          <Input label={twitterXLabel} value={form.social_links.twitter} onChangeText={(t) => updateSocial("twitter", t)} placeholder="https://x.com/..." autoCapitalize="none" />
          <Input label={linkedInLabel} value={form.social_links.linkedin} onChangeText={(t) => updateSocial("linkedin", t)} placeholder="https://linkedin.com/..." autoCapitalize="none" />
          <Input label={youTubeLabel} value={form.social_links.youtube} onChangeText={(t) => updateSocial("youtube", t)} placeholder="https://youtube.com/..." autoCapitalize="none" />
          <Input label={tikTokLabel} value={form.social_links.tiktok} onChangeText={(t) => updateSocial("tiktok", t)} placeholder="https://tiktok.com/..." autoCapitalize="none" />
        </View>

        <Button label={saveChangesLabel} onPress={handleSave} loading={saving} />

        <View style={[s.divider, { marginVertical: theme.spacing.sm }]} />

        <Button
          label={logoutLabel}
          onPress={handleLogout}
          variant="danger"
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
