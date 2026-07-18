/**
 * Supplier Bulk Upload — React Native
 * Upload CSV of products in bulk; download template; view import status.
 */
import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  Platform,
} from "react-native";
import { Stack } from "expo-router";
import * as DocumentPicker from "expo-document-picker";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    card: {
      padding: 16,
      borderRadius: 14,
      borderWidth: 1,
    },
    btn: {
      height: 52,
      borderRadius: 14,
      alignItems: "center",
      justifyContent: "center",
    },
    dropzone: {
      height: 180,
      borderRadius: 18,
      borderWidth: 2,
      borderStyle: "dashed",
      marginTop: theme.spacing.md,
      alignItems: "center",
      justifyContent: "center",
      paddingHorizontal: 20,
    },
    errorRow: {
      padding: 10,
      borderRadius: 8,
      borderWidth: 1,
      marginBottom: 6,
    },
  });

interface BulkImportResult {
  total: number;
  imported: number;
  failed: number;
  message?: string;
  errors?: string[];
}

const CSV_HEADERS = ["Name", "Description", "Price", "Stock Quantity", "Category"];

function normalizeBulkImportResult(payload: any): BulkImportResult {
  if (payload && typeof payload === "object" && typeof payload.imported_count === "number") {
    const errors = Array.isArray(payload.errors)
      ? payload.errors.map((entry: unknown) => String(entry))
      : [];
    return {
      total: payload.imported_count + errors.length,
      imported: payload.imported_count,
      failed: errors.length,
      message: typeof payload.message === "string" ? payload.message : undefined,
      errors,
    };
  }

  const created = Number(payload?.created ?? 0);
  const updated = Number(payload?.updated ?? 0);
  const failed = Number(payload?.failed ?? 0);
  const errors = Array.isArray(payload?.errors)
    ? payload.errors.map((entry: unknown) => {
        if (entry && typeof entry === "object") {
          const row = (entry as { row?: unknown }).row;
          const message = (entry as { message?: unknown }).message;
          if (typeof row !== "undefined" && typeof message !== "undefined") {
            return `Row ${row}: ${message}`;
          }
        }
        return String(entry);
      })
    : [];

  return {
    total: Number(payload?.total ?? created + updated + failed),
    imported: created + updated,
    failed,
    message: typeof payload?.message === "string" ? payload.message : undefined,
    errors,
  };
}

export default function SupplierBulkUploadScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<BulkImportResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ name: string; uri: string } | null>(null);
  const styles = createStyles(theme);

  const pickFile = async () => {
    try {
      const res = await DocumentPicker.getDocumentAsync({
        type: ["text/csv", "text/comma-separated-values", "application/csv", "application/vnd.ms-excel"],
        copyToCacheDirectory: true,
      });
      if (res.canceled || !res.assets?.length) return;
      const file = res.assets[0];
      setSelectedFile({ name: file.name, uri: file.uri });
      setResult(null);
    } catch {
      Alert.alert("Error", "Could not pick file");
    }
  };

  const upload = async () => {
    if (!selectedFile) {
      Alert.alert("No File", "Please select a CSV file first");
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", {
        uri: selectedFile.uri,
        name: selectedFile.name,
        type: "text/csv",
      } as any);

      const res = await apiFetch<any>("/supplier/products/import", {
        method: "POST",
        body: formData,
        headers: {}, // let fetch set multipart boundary
      });
      setResult(normalizeBulkImportResult(res));
      setSelectedFile(null);
    } catch (err: any) {
      Alert.alert("Upload Failed", err?.message ?? "An error occurred during bulk import");
    }
    setUploading(false);
  };

  const downloadTemplate = async () => {
    try {
      Alert.alert(
        "CSV Template",
        `Required columns:\n\n${CSV_HEADERS.join(", ")}\n\nDownload via browser or check the Supplier Guide for a sample file.`
      );
    } catch {
      Alert.alert("Error", "Could not download template");
    }
  };

  if (!user || (user.role !== "supplier" && user.role !== "admin")) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: theme.colors.danger }}>Supplier access required</Text>
      </View>
    );
  }

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.surface0 }} contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 60 }}>
      <Stack.Screen options={{ title: "Bulk Upload", headerStyle: { backgroundColor: theme.colors.surface0 }, headerTitleStyle: { color: theme.colors.text, fontWeight: "700" } }} />

      <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="cube-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { marginBottom: 4 }]}>Bulk Product Import</Text></View>
      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginBottom: theme.spacing.lg }}>
        Upload a CSV file to import multiple products at once.
      </Text>

      {/* Instructions */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="list-outline" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.text, fontWeight: "700", marginBottom: 8 }}>Required CSV Columns</Text></View>
        {CSV_HEADERS.map((col, i) => (
          <View key={col} style={{ flexDirection: "row", gap: 8, marginBottom: 4 }}>
            <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, width: 18 }}>{i + 1}.</Text>
            <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.xs, fontFamily: Platform.OS === "ios" ? "Courier" : "monospace" }}>{col}</Text>
              {["name", "price", "stock_quantity", "category_id"].includes(col) && (
              <Text style={{ color: theme.colors.danger, fontSize: 10, alignSelf: "center" }}>*required</Text>
            )}
          </View>
        ))}
      </View>

      {/* Download template */}
      <TouchableOpacity onPress={downloadTemplate} style={[styles.btn, { backgroundColor: theme.colors.surface2, marginTop: theme.spacing.md }]}>
        <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="download-outline" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.text, fontWeight: "700" }}>View Template Info</Text></View>
      </TouchableOpacity>

      {/* File picker */}
      <TouchableOpacity onPress={pickFile} style={[styles.dropzone, { borderColor: selectedFile ? theme.colors.brand : theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
        {selectedFile ? (
          <>
            <Ionicons name="document-outline" size={36} color={theme.colors.textMuted} />
            <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.sm, textAlign: "center" }}>{selectedFile.name}</Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 4 }}>Tap to change file</Text>
          </>
        ) : (
          <>
            <Ionicons name="folder-outline" size={44} color={theme.colors.textMuted} />
            <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.sm }}>Select CSV File</Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 4 }}>Tap to browse files</Text>
          </>
        )}
      </TouchableOpacity>

      {selectedFile && (
        <TouchableOpacity onPress={upload} disabled={uploading} style={[styles.btn, { backgroundColor: theme.colors.brand, marginTop: theme.spacing.md }]}>
            {uploading ? (
            <ActivityIndicator color={theme.colors.onBrand} size="small" />
          ) : (
            <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="arrow-up" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.onBrand, fontWeight: "800", fontSize: theme.fontSize.base }}>Upload Products</Text></View>
          )}
        </TouchableOpacity>
      )}

      {/* Result */}
      {result && (
        <View style={{ marginTop: theme.spacing.lg }}>
          <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="bar-chart-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { fontSize: theme.fontSize.base, marginBottom: theme.spacing.sm }]}>Import Result</Text></View>
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            {[
              { label: "Total Rows", value: result.total, color: theme.colors.text },
              { label: "Imported", value: result.imported, color: theme.colors.success },
              { label: "Failed", value: result.failed, color: result.failed > 0 ? theme.colors.danger : theme.colors.textMuted },
            ].map(({ label, value, color }) => (
              <View key={label} style={{ flexDirection: "row", justifyContent: "space-between", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: theme.colors.border }}>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{label}</Text>
                <Text style={{ color, fontWeight: "700", fontSize: theme.fontSize.sm }}>{value}</Text>
              </View>
            ))}
            {result.message ? (
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 10 }}>
                {result.message}
              </Text>
            ) : null}
          </View>

          {Array.isArray(result.errors) && result.errors.length > 0 && (
            <View style={{ marginTop: theme.spacing.md }}>
               <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="alert-circle" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.danger, fontWeight: "700", marginBottom: 8 }}>Errors ({result.errors.length})</Text></View>
               {result.errors.slice(0, 20).map((e, i) => (
                 <View key={i} style={[styles.errorRow, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.dangerBg }]}>
                   <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.xs }}>{e}</Text>
                </View>
              ))}
              {result.errors.length > 20 && (
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 8 }}>
                  …and {result.errors.length - 20} more errors
                </Text>
              )}
            </View>
          )}

          <TouchableOpacity onPress={() => { setResult(null); setSelectedFile(null); }} style={[styles.btn, { backgroundColor: theme.colors.surface2, marginTop: theme.spacing.md }]}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Upload Another File</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}
