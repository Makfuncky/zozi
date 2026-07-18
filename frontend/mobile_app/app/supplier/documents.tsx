import React, { useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, getStatusColor } from "@/theme";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  apiFetch,
  listSupplierDocuments,
  SupplierDocument,
} from "@/lib/api";

const DOCUMENT_TYPES = [
  { value: "business_registration", label: "Business Registration" },
  { value: "tax_certificate", label: "Tax Certificate" },
  { value: "id_card", label: "ID Card" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "product_certification", label: "Product Certification" },
  { value: "other", label: "Other" },
];

import * as DocumentPicker from "expo-document-picker";

export default function SupplierDocumentsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const router = useRouter();

  const [documents, setDocuments] = useState<SupplierDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState(DOCUMENT_TYPES[0].value);
  const [showTypePicker, setShowTypePicker] = useState(false);

  const fetchDocuments = () => {
    listSupplierDocuments()
      .then((data) => {
        setDocuments(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load documents.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const pickAndUpload = async () => {
    if (!DocumentPicker) {
      Alert.alert(
        "Not Available",
        "expo-document-picker is not installed. Please upload via web portal.",
      );
      return;
    }

    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["application/pdf", "image/*"],
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return;
      }

      const file = result.assets[0];
      setUploading(true);
      setError(null);

      // Upload the file — backend expects form-data with the file
      const formData = new FormData();
      formData.append("file", {
        uri: file.uri,
        name: file.name ?? "document",
        type: file.mimeType ?? "application/octet-stream",
      } as any);
      formData.append("document_type", selectedType);

      await apiFetch("/supplier-documents/my/upload", {
        method: "POST",
        body: formData as never,
      } as never);

      fetchDocuments();
    } catch (err: any) {
      setError(err?.message ?? "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const selectedTypeLabel =
    DOCUMENT_TYPES.find((t) => t.value === selectedType)?.label ?? selectedType;

  const documentStats = useMemo(() => {
    const now = Date.now();
    return documents.reduce(
      (acc, doc) => {
        acc.total += 1;
        if (doc.status === "approved") acc.approved += 1;
        if (doc.status === "pending") acc.pending += 1;
        if (doc.status === "rejected") acc.rejected += 1;
        if (doc.expires_at) {
          const expiresAt = new Date(doc.expires_at).getTime();
          if (!Number.isNaN(expiresAt) && expiresAt - now <= 1000 * 60 * 60 * 24 * 30) {
            acc.renewalSoon += 1;
          }
        }
        return acc;
      },
      { total: 0, approved: 0, pending: 0, rejected: 0, renewalSoon: 0 },
    );
  }, [documents]);

  const attentionDocuments = useMemo(
    () => documents.filter((doc) => doc.status === "rejected" || !!doc.review_note || !!doc.expires_at).slice(0, 3),
    [documents],
  );

  const formatRenewalState = (value?: string | null): string | null => {
    if (!value) return null;
    const ms = new Date(value).getTime() - Date.now();
    if (Number.isNaN(ms)) return null;
    const days = Math.ceil(ms / (1000 * 60 * 60 * 24));
    if (days < 0) return `Expired ${Math.abs(days)} day${Math.abs(days) === 1 ? "" : "s"} ago`;
    if (days === 0) return "Expires today";
    if (days <= 30) return `Renew in ${days} day${days === 1 ? "" : "s"}`;
    return `Valid until ${new Date(value).toLocaleDateString()}`;
  };

  if (loading) {
    return (
      <View style={[s.container, styles.centered]}>
        <ActivityIndicator color={theme.colors.brand} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={s.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <Stack.Screen options={{ title: "KYC Documents" }} />

      {error && (
        <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
          <Text style={{ color: theme.colors.danger, fontSize: 13 }}>{error}</Text>
        </View>
      )}

      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, gap: 14 }]}>
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: 11, letterSpacing: 0.8, textTransform: "uppercase", marginBottom: 4 }}>
              Compliance Health
            </Text>
            <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: 17, marginBottom: 4 }}>
              Keep KYC visible before approval stalls your storefront.
            </Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: 12, lineHeight: 18 }}>
              Review notes, renewal timing, and document status all affect supplier activation and payout readiness.
            </Text>
          </View>
          <TouchableOpacity onPress={() => router.push("/supplier/guide" as never)} style={[styles.inlineAction, { borderColor: theme.colors.border }]}>
            <Ionicons name="book-outline" size={14} color={theme.colors.brand} />
            <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: 12 }}>Guide</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.metricGrid}>
          {[
            { label: "Approved", value: String(documentStats.approved), tone: theme.colors.success },
            { label: "Pending", value: String(documentStats.pending), tone: theme.colors.warning },
            { label: "Rejected", value: String(documentStats.rejected), tone: theme.colors.danger },
            { label: "Renew Soon", value: String(documentStats.renewalSoon), tone: theme.colors.statusProcessing },
          ].map((metric) => (
            <View key={metric.label} style={[styles.metricCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={{ color: metric.tone, fontSize: 16, fontWeight: "800" }}>{metric.value}</Text>
              <Text style={{ color: theme.colors.textMuted, fontSize: 11, fontWeight: "600" }}>{metric.label}</Text>
            </View>
          ))}
        </View>

        {attentionDocuments.length > 0 && (
          <View style={{ gap: 8 }}>
            <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 13 }}>Needs attention</Text>
            {attentionDocuments.map((doc) => {
              const renewalText = formatRenewalState(doc.expires_at);
              return (
                <View key={`attention-${doc.id}`} style={[styles.attentionCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 13 }}>
                    {DOCUMENT_TYPES.find((t) => t.value === doc.document_type)?.label ?? doc.document_type}
                  </Text>
                  <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>
                    {doc.review_note ?? renewalText ?? "Waiting for document review."}
                  </Text>
                </View>
              );
            })}
          </View>
        )}
      </View>

      {/* Upload section */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 15, marginBottom: 12 }}>
          Upload Document
        </Text>

        {/* Type selector */}
        <Text style={{ color: theme.colors.textMuted, fontSize: 12, marginBottom: 6 }}>Document Type</Text>
        <TouchableOpacity
          onPress={() => setShowTypePicker((p) => !p)}
          style={[styles.selector, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
        >
          <Text style={{ color: theme.colors.text, fontSize: 14 }}>{selectedTypeLabel}</Text>
          <Text style={{ color: theme.colors.textMuted }}>▾</Text>
        </TouchableOpacity>

        {showTypePicker && (
          <View style={[styles.typeList, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            {DOCUMENT_TYPES.map((t) => (
              <TouchableOpacity
                key={t.value}
                onPress={() => { setSelectedType(t.value); setShowTypePicker(false); }}
                style={[styles.typeOption, selectedType === t.value && { backgroundColor: theme.colors.brand + "22" }]}
              >
                <Text style={{ color: selectedType === t.value ? theme.colors.brand : theme.colors.text, fontSize: 14 }}>
                  {t.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <TouchableOpacity
          onPress={pickAndUpload}
          disabled={uploading}
          style={[styles.uploadBtn, { backgroundColor: theme.colors.brand, opacity: uploading ? 0.6 : 1 }]}
        >
          {uploading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={{ color: "#fff", fontWeight: "700", fontSize: 14 }}>
              Choose File &amp; Upload
            </Text>
          )}
        </TouchableOpacity>
        <Text style={{ color: theme.colors.textFaint, fontSize: 11, marginTop: 6, textAlign: "center" }}>
          PDF or image files accepted
        </Text>
      </View>

      {/* Document list */}
      {documents.length > 0 && (
        <View style={{ marginTop: 20 }}>
          <Text style={{ color: theme.colors.textMuted, fontSize: 12, fontWeight: "600", marginBottom: 10 }}>
            SUBMITTED DOCUMENTS ({documents.length})
          </Text>
            {documents.map((doc) => {
              const sc = getStatusColor(doc.status, theme);
              return (
                <View
                  key={doc.id}
                  style={[styles.docRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: theme.colors.text, fontWeight: "600", fontSize: 14 }}>
                      {DOCUMENT_TYPES.find((t) => t.value === doc.document_type)?.label ?? doc.document_type}
                    </Text>
                    <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>
                      {doc.file_name ?? doc.document_name ?? "Uploaded file"}
                    </Text>
                    <Text style={{ color: theme.colors.textFaint, fontSize: 11, marginTop: 2 }}>
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </Text>
                    {formatRenewalState(doc.expires_at) && (
                      <Text style={{ color: theme.colors.brand, fontSize: 11, marginTop: 4, fontWeight: "700" }}>
                        {formatRenewalState(doc.expires_at)}
                      </Text>
                    )}
                    {(doc.review_note ?? doc.notes) && (
                      <Text style={{ color: theme.colors.textMuted, fontSize: 12, marginTop: 4, fontStyle: "italic" }}>
                        {doc.review_note ?? doc.notes}
                      </Text>
                    )}
                  </View>
                  <View style={[styles.badge, { backgroundColor: sc.bg, borderColor: sc.border }]}>
                    <Text style={{ color: sc.color, fontSize: 10, fontWeight: "700" }}>{doc.status.toUpperCase()}</Text>
                  </View>
                </View>
              );
            })}
        </View>
      )}

      {documents.length === 0 && !loading && (
        <EmptyState
          title="No documents uploaded yet"
          subtitle="Upload your KYC and compliance documents to activate your storefront."
          icon={<Ionicons name="document-outline" size={30} color={theme.colors.textMuted} />}
        />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 10,
  },
  inlineAction: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  metricCard: {
    width: "48%",
    borderRadius: 14,
    borderWidth: 1,
    padding: 12,
    gap: 4,
  },
  attentionCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    gap: 4,
  },
  selector: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  typeList: {
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 10,
    overflow: "hidden",
  },
  typeOption: {
    padding: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "rgba(0,0,0,0.07)",
  },
  uploadBtn: {
    borderRadius: 12,
    paddingVertical: 13,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
  },
  docRow: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    marginBottom: 10,
  },
  badge: {
    borderRadius: 20,
    borderWidth: 1,
    paddingHorizontal: 7,
    paddingVertical: 2,
    alignSelf: "flex-start",
  },
  errorBox: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    marginBottom: 14,
  },
});
