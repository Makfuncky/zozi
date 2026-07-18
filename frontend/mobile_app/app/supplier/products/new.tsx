import React, { useMemo, useState } from "react";
import { View, Text, ScrollView, KeyboardAvoidingView, Platform, StyleSheet, Switch, TouchableOpacity, ActivityIndicator, Image } from "react-native";
import { Feather, Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";

import { Stack, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { toast } from "@/lib/toastStore";
import { hasCreateAiSource } from "@/lib/supplierProductAi";
import { saveProductDraft, loadProductDraft, clearProductDraft } from "@/lib/productDraft";
import {
  SUPPLIER_SUBCATEGORY_OPTIONS,
  inferSuggestedSubCategory,
  mergeVariantOptions,
  normalizeSuggestedColor,
  resolveKnownCategory,
} from "@/lib/supplierProductForm";
import {
  getSupplierVariantTemplate,
  suggestSupplierVariantTemplate,
  SUPPLIER_VARIANT_TEMPLATES,
} from "@shared/supplierProductOptions";
import { isRtlLocale } from "@shared/localization";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: { padding: theme.spacing.md, gap: 14, paddingBottom: 40 },
  card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 14 },
  toggleRow: { justifyContent: "space-between", alignItems: "center" },
  errorBox: { borderWidth: 1, borderRadius: 10, padding: 12 },
  mediaCard: { borderRadius: theme.radius.lg, borderWidth: 1, padding: theme.spacing.sm, gap: 10 },
  mediaPreview: { width: 88, height: 88, borderRadius: theme.radius.md, borderWidth: 1 },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8 },
});

function normalizeSizesInput(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

/**
 * The 12 open-source "Free Image Tools" offered by the backend pipeline
 * (services/free_image_tools.py). Each toggles a `process_*` boolean field on
 * the multipart product upload. Order follows the backend pipeline.
 */
const IMAGE_TOOLS: { key: string; label: string; description: string }[] = [
  { key: "process_magic_erase", label: "Magic Erase", description: "AI background removal with clean edges" },
  { key: "process_smart_crop", label: "Smart Crop", description: "Auto-center and crop to the product" },
  { key: "process_rotate", label: "Auto Rotate", description: "Fix image orientation" },
  { key: "process_auto_light", label: "Auto Light", description: "CLAHE and gamma correction" },
  { key: "process_upscale", label: "Upscale 2×", description: "Sharper, larger image" },
  { key: "process_white_balance", label: "White Balance", description: "Natural color correction" },
  { key: "process_denoise", label: "Denoise", description: "Reduce image noise" },
  { key: "process_sharpen", label: "Sharpen", description: "Crisp, detailed edges" },
  { key: "process_compress", label: "Compress", description: "Smaller file size" },
  { key: "process_webp_convert", label: "WebP Convert", description: "Modern, efficient format" },
  { key: "process_color_enhance", label: "Color Enhance", description: "Vibrant, balanced saturation" },
  { key: "process_auto_levels", label: "Auto Levels", description: "Auto tone and contrast" },
];

export default function NewProductScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const currency = useCurrencyStore((state) => state.currency);
  const toAED = useCurrencyStore((state) => state.toAED);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [addProductTitle, productNameLabel, productNamePlaceholder, generatingSuggestionsLabel, aiSuggestLabel, productMediaIntakeLabel, productMediaIntakeDescriptionLabel, replaceMainPhotoLabel, selectProductMediaLabel, mainImageSelectedLabel, aiPhotoHintLabel, galleryMediaLabel, galleryMediaDescriptionLabel, addGalleryMediaLabel, videoLabel, photoLabel, descriptionLabel, descriptionPlaceholderLabel, stockQuantityLabel, categoryLabel, categoryPlaceholderLabel, colorLabel, colorPlaceholderLabel, tagsLabel, tagsPlaceholderLabel, variantsDetailsLabel, variantsHintLabel, variantOptionsLabel, activeVisibleLabel, createProductLabel, cancelLabel] = useTranslateTexts([
    "Add Product",
    "Product Name *",
    "e.g. Wireless Headphones",
    "Generating suggestions…",
    "AI Suggest from product media",
    "Product Media Intake",
    "Select one or more files. The first photo becomes the main storefront image and the rest are added to the gallery.",
    "Replace Main Photo / Add More Media",
    "Select Product Media",
    "Main image selected",
    "AI will use this photo to suggest category and color.",
    "Gallery Media",
    "Use this only when you want to append more media after the main intake above.",
    "Add More Gallery Media",
    "Video",
    "Photo",
    "Description",
    "Product description...",
    "Stock Quantity *",
    "Category",
    "Electronics, Clothing...",
    "Color",
    "Black, Navy, White",
    "Tags",
    "wireless, portable, waterproof",
    "Variants & Details",
    "Choose a variant template, then tap the options you want to persist for this product.",
    "Variant Options",
    "Active (visible to customers)",
    "Create Product",
    "Cancel",
  ]);
  const [subcategoryLabel, subcategoryPlaceholderLabel, categorySearchLabel, subcategorySearchLabel] = useTranslateTexts([
    "Sub-category",
    "Choose or type a sub-category",
    "Search categories",
    "Search sub-categories",
  ]);
  const [returnWindowLabel, returnWindowHintLabel] = useTranslateTexts([
    "Return Window (days)",
    "Minimum 10 days. Supplier payouts wait until this window expires.",
  ]);
  const [
    smartUploadLabel, smartUploadDescLabel, aiAutoFillLabel, translateArLabel, translatingLabel,
    arabicNameLabel, arabicDescLabel, gccComplianceLabel, halalLabel, modestyLabel,
    logisticsLabel, weightLabel, dimensionsLabel, saveDraftLabel, loadDraftLabel,
    draftSavedLabel, draftLoadedLabel, bulkUploadLabel,
  ] = useTranslateTexts([
    "Smart Upload Assistant",
    "AI auto-fills the name, category, tags and variants from your photo. Voice, barcode and bulk CSV upload are also available.",
    "AI Auto-Fill from Photo",
    "Translate to Arabic",
    "Translating…",
    "Arabic Name",
    "Arabic Description",
    "GCC Compliance",
    "Halal Certified",
    "Modesty / Family-Friendly",
    "Logistics",
    "Weight (kg)",
    "Dimensions (L×W×H cm)",
    "Save Draft",
    "Load Draft",
    "Draft saved",
    "Draft loaded",
    "Bulk Upload (CSV)",
  ]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [pickingMedia, setPickingMedia] = useState(false);
  const [mainImage, setMainImage] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [galleryMedia, setGalleryMedia] = useState<DocumentPicker.DocumentPickerAsset[]>([]);
  const [imageTools, setImageTools] = useState<Record<string, boolean>>(
    Object.fromEntries(IMAGE_TOOLS.map((tool) => [tool.key, false])),
  );
  const [translating, setTranslating] = useState(false);
  const [draftBusy, setDraftBusy] = useState(false);

  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    stock: "",
    category: "",
    subcategory: "",
    color: "",
    tags: "",
    sizes: "",
    return_window_days: "10",
    is_active: true,
    name_ar: "",
    description_ar: "",
    halal_compliance: false,
    modesty_compliance: false,
    weight_kg: "",
    dimensions: "",
  });
  const [selectedVariantTemplate, setSelectedVariantTemplate] = useState("");
  const variantTemplate = getSupplierVariantTemplate(selectedVariantTemplate) ?? getSupplierVariantTemplate("universal");
  const subcategoryOptions = useMemo(() => SUPPLIER_SUBCATEGORY_OPTIONS[form.category] ?? [], [form.category]);

  function update(field: keyof typeof form, value: string | boolean) {
    setForm((f) => ({ ...f, [field]: value }));
    setError(null);
  }

  function parseReturnWindow(rawValue: string): number | null {
    const parsed = Number.parseInt(rawValue.trim(), 10);
    if (!Number.isFinite(parsed) || parsed < 10) {
      return null;
    }
    return parsed;
  }

  async function handleAiSuggest() {
    if (!hasCreateAiSource(form.name, form.description, mainImage)) return setError("Add a product photo or product details first to use AI Suggest");
    setAiLoading(true);
    setError(null);
    try {
      const payload = new FormData();
      payload.append("name", form.name.trim());
      payload.append("description", form.description.trim());
      if (mainImage) {
        payload.append("image", {
          uri: mainImage.uri,
          name: mainImage.name || "product.jpg",
          type: mainImage.mimeType || "image/jpeg",
        } as any);
      }
      galleryMedia.forEach((asset) => {
        if ((asset.mimeType || "").startsWith("image/")) {
          payload.append("images", {
            uri: asset.uri,
            name: asset.name || "gallery-image.jpg",
            type: asset.mimeType || "image/jpeg",
          } as any);
        }
      });

      const data = await apiFetch<{
        name?: string;
        description?: string;
        category?: string;
        color?: string;
        color_candidates?: string[];
        tags_string?: string;
        variant_template?: string;
        variant_options?: string[];
      }>('/ai/suggest', {
        method: 'POST',
        body: payload,
      });
      const nextCategory = resolveKnownCategory(data.category || form.category);
      const nextName = data.name || form.name;
      const nextDescription = data.description || form.description;
      const nextTags = data.tags_string || form.tags;
      const nextSubcategory = inferSuggestedSubCategory(nextCategory, [nextName, nextDescription, nextTags].join(" "), form.subcategory);
      const nextColor = normalizeSuggestedColor(data.color_candidates?.[0] || data.color || form.color);
      const suggestedTemplate = data.variant_template || suggestSupplierVariantTemplate({
        category: nextCategory,
        name: nextName,
        tags: nextTags,
      });
      setForm((f) => ({
        ...f,
        name: nextName,
        description: nextDescription,
        category: nextCategory,
        subcategory: nextSubcategory,
        color: nextColor || f.color,
        tags: nextTags,
        sizes: mergeVariantOptions(data.variant_options, f.sizes),
      }));
      setSelectedVariantTemplate(suggestedTemplate);
      toast.success("AI suggestions applied!");
    } catch {
      setError("AI Suggest failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }

  async function pickProductMedia() {
    setPickingMedia(true);
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["image/*", "video/*"],
        copyToCacheDirectory: true,
        multiple: true,
      });
      if (!result.canceled && result.assets?.length) {
        const assets = result.assets;
        const primaryImage = assets.find((asset) => (asset.mimeType || "").startsWith("image/")) || assets[0];
        const primaryIndex = assets.indexOf(primaryImage);
        const galleryAssets = assets.filter((_, index) => index !== primaryIndex);
        setMainImage(primaryImage);
        setGalleryMedia((current) => [...current, ...galleryAssets].slice(0, 20));
      }
    } finally {
      setPickingMedia(false);
    }
  }

  async function pickGalleryMedia() {
    setPickingMedia(true);
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["image/*", "video/*"],
        copyToCacheDirectory: true,
        multiple: true,
      });
      if (!result.canceled && result.assets?.length) {
        setGalleryMedia((current) => [...current, ...result.assets].slice(0, 20));
      }
    } finally {
      setPickingMedia(false);
    }
  }

  async function handleCreate() {
    if (!form.name.trim()) return setError("Product name is required");
    const price = parseFloat(form.price);
    if (isNaN(price) || price <= 0) return setError("Enter a valid price");
    const stock = parseInt(form.stock, 10);
    if (isNaN(stock) || stock < 0) return setError("Enter a valid stock quantity");
    if (!mainImage) return setError("Select a main product photo before creating the listing");
    const returnWindowDays = parseReturnWindow(form.return_window_days);
    if (returnWindowDays === null) return setError("Return window must be at least 10 days");

    setSaving(true);
    setError(null);

    try {
      const payload = new FormData();
      payload.append("name", form.name.trim());
      payload.append("description", form.description.trim());
      payload.append("price", String(toAED(price)));
      payload.append("stock_quantity", String(stock));
      payload.append("category", form.category.trim() || "General");
      payload.append("subcategory", form.subcategory.trim());
      payload.append("color", form.color.trim());
      const combinedTags = form.modesty_compliance && !form.tags.split(",").map((t) => t.trim()).includes("modest")
        ? `${form.tags.trim()},modest`
        : form.tags.trim();
      payload.append("tags", combinedTags);
      payload.append("sizes", JSON.stringify(normalizeSizesInput(form.sizes)));
      payload.append("image", {
        uri: mainImage.uri,
        name: mainImage.name || "product.jpg",
        type: mainImage.mimeType || "image/jpeg",
      } as any);
      galleryMedia.forEach((asset, index) => {
        const isVideo = (asset.mimeType || "").startsWith("video/");
        payload.append("additional_images", {
          uri: asset.uri,
          name: asset.name || (isVideo ? `product-video-${index + 1}.mp4` : `product-extra-${index + 1}.jpg`),
          type: asset.mimeType || (isVideo ? "video/mp4" : "image/jpeg"),
        } as any);
      });

      Object.entries(imageTools).forEach(([key, enabled]) => {
        if (enabled) payload.append(key, "true");
      });

      if (form.name_ar.trim()) payload.append("name_ar", form.name_ar.trim());
      if (form.description_ar.trim()) payload.append("description_ar", form.description_ar.trim());
      payload.append("halal_compliance", form.halal_compliance ? "true" : "false");
      if (form.weight_kg.trim()) payload.append("weight_kg", form.weight_kg.trim());
      if (form.dimensions.trim()) payload.append("dimensions", form.dimensions.trim());

      const createdProduct = await apiFetch<{ id: number }>("/supplier/products", {
        method: "POST",
        body: payload,
      });
      await apiFetch(`/supplier/products/${createdProduct.id}/return-window`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days: returnWindowDays }),
      });
      await clearProductDraft();
      toast.success("Product created!");
      router.back();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create product.");
    } finally {
      setSaving(false);
    }
  }

  async function translateOne(text: string): Promise<string> {
    if (!text.trim()) return "";
    const payload = new FormData();
    payload.append("text", text);
    payload.append("target", "ar");
    const data = await apiFetch<{ translated_text?: string }>("/supplier/upload/translate", {
      method: "POST",
      body: payload,
    });
    return data.translated_text || "";
  }

  async function handleTranslateAr() {
    if (!form.name.trim() && !form.description.trim()) {
      return setError("Add a product name or description before translating.");
    }
    setTranslating(true);
    setError(null);
    try {
      const [arName, arDesc] = await Promise.all([
        form.name.trim() ? translateOne(form.name.trim()) : Promise.resolve(""),
        form.description.trim() ? translateOne(form.description.trim()) : Promise.resolve(""),
      ]);
      setForm((f) => ({ ...f, name_ar: arName, description_ar: arDesc }));
      toast.success("Translated to Arabic");
    } catch {
      setError("Translation failed. Please try again.");
    } finally {
      setTranslating(false);
    }
  }

  async function handleSaveDraft() {
    setDraftBusy(true);
    try {
      await saveProductDraft({
        name: form.name,
        description: form.description,
        price: form.price,
        stock: form.stock,
        category: form.category,
        subcategory: form.subcategory,
        color: form.color,
        tags: form.tags,
        sizes: form.sizes,
        return_window_days: form.return_window_days,
        is_active: form.is_active,
        name_ar: form.name_ar,
        description_ar: form.description_ar,
        halal_compliance: form.halal_compliance,
        modesty_compliance: form.modesty_compliance,
        weight_kg: form.weight_kg,
        dimensions: form.dimensions,
      });
      toast.success(draftSavedLabel);
    } catch {
      setError("Could not save draft.");
    } finally {
      setDraftBusy(false);
    }
  }

  async function handleLoadDraft() {
    setDraftBusy(true);
    try {
      const draft = await loadProductDraft();
      if (!draft) {
        setError("No saved draft found.");
        return;
      }
      setForm((f) => ({ ...f, ...draft }));
      toast.success(draftLoadedLabel);
    } catch {
      setError("Could not load draft.");
    } finally {
      setDraftBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <Stack.Screen options={{ title: addProductTitle }} />
      <ScrollView
        testID="supplier-product-new-screen"
        style={[s.container, isRtl ? { direction: "rtl" } : undefined]}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <Ionicons name="bulb" size={16} color={theme.colors.brand} />
            <Text style={[s.text, { fontWeight: "700" }]}>{smartUploadLabel}</Text>
          </View>
          <Text style={s.textMuted}>{smartUploadDescLabel}</Text>
          <TouchableOpacity
            testID="supplier-product-new-bulk"
            onPress={() => router.push("/supplier/bulk" as any)}
            style={{ flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start" }}
          >
            <Ionicons name="layers" size={14} color={theme.colors.brand} />
            <Text style={{ color: theme.colors.brand, fontSize: 12, fontWeight: "700" }}>{bulkUploadLabel}</Text>
          </TouchableOpacity>
        </View>

        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input testID="supplier-product-new-name" label={productNameLabel} value={form.name} onChangeText={(t) => update("name", t)} placeholder={productNamePlaceholder} />

          {/* AI Suggest button */}
          <TouchableOpacity
            testID="supplier-product-new-ai-suggest"
            onPress={handleAiSuggest}
            disabled={aiLoading}
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              borderRadius: 12,
              borderWidth: 1,
              borderColor: theme.colors.brand,
              backgroundColor: theme.colors.brand + "14",
              paddingVertical: 9,
              opacity: aiLoading ? 0.65 : 1,
            }}
          >
            {aiLoading
              ? <ActivityIndicator size="small" color={theme.colors.brand} />
              : <Feather name="zap" size={14} color={theme.colors.brand} />}
            <Text style={{ color: theme.colors.brand, fontSize: 12, fontWeight: "700" }}>
              {aiLoading ? generatingSuggestionsLabel : aiSuggestLabel}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            testID="supplier-product-new-translate-ar"
            onPress={handleTranslateAr}
            disabled={translating}
            style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, borderRadius: 12, borderWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface2, paddingVertical: 9, opacity: translating ? 0.65 : 1 }}
          >
            {translating
              ? <ActivityIndicator size="small" color={theme.colors.brand} />
              : <Ionicons name="language" size={14} color={theme.colors.brand} />}
            <Text style={{ color: theme.colors.text, fontSize: 12, fontWeight: "700" }}>
              {translating ? translatingLabel : translateArLabel}
            </Text>
          </TouchableOpacity>

          <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>{productMediaIntakeLabel}</Text>
            <Text style={s.textMuted}>{productMediaIntakeDescriptionLabel}</Text>
            <Button testID="supplier-product-new-pick-media" label={mainImage ? replaceMainPhotoLabel : selectProductMediaLabel} onPress={pickProductMedia} variant="secondary" loading={pickingMedia} />
            {mainImage ? (
              <View testID="supplier-product-new-main-image" style={{ flexDirection: "row", gap: 12, alignItems: "center" }}>
                <Image source={{ uri: mainImage.uri }} style={[styles.mediaPreview, { borderColor: theme.colors.border }]} />
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "600" }]} numberOfLines={1}>{mainImage.name || mainImageSelectedLabel}</Text>
                  <Text style={s.textMuted}>{aiPhotoHintLabel}</Text>
                </View>
              </View>
            ) : null}
          </View>

          <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>{galleryMediaLabel}</Text>
            <Text style={s.textMuted}>{galleryMediaDescriptionLabel}</Text>
            <Button testID="supplier-product-new-pick-gallery" label={addGalleryMediaLabel} onPress={pickGalleryMedia} variant="secondary" loading={pickingMedia} />
            {galleryMedia.length > 0 ? (
              <View style={styles.chipRow}>
                {galleryMedia.map((asset, index) => (
                  <TouchableOpacity
                    key={`${asset.uri}-${index}`}
                    onPress={() => setGalleryMedia((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                    style={[styles.chip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
                  >
                    <Text style={[s.text, { fontSize: 12 }]} numberOfLines={1}>{asset.name || `${(asset.mimeType || "").startsWith("video/") ? videoLabel : photoLabel} ${index + 1}`}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            ) : null}
          </View>

          {/* Free Image Tools */}
          <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Ionicons name="sparkles" size={16} color={theme.colors.brand} />
              <Text style={[s.text, { fontWeight: "700" }]}>Free Image Tools</Text>
            </View>
            <Text style={s.textMuted}>Enhance your photos automatically before they go live (optional).</Text>
            {IMAGE_TOOLS.map((tool) => (
              <TouchableOpacity
                key={tool.key}
                onPress={() => setImageTools((prev) => ({ ...prev, [tool.key]: !prev[tool.key] }))}
                activeOpacity={0.8}
                style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 12, paddingVertical: 6 }}
              >
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "600", fontSize: 13 }]}>{tool.label}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>{tool.description}</Text>
                </View>
                <Switch
                  value={imageTools[tool.key]}
                  onValueChange={(v) => setImageTools((prev) => ({ ...prev, [tool.key]: v }))}
                  trackColor={{ true: theme.colors.brand }}
                  thumbColor="#fff"
                />
              </TouchableOpacity>
            ))}
          </View>

          <Input testID="supplier-product-new-description" label={descriptionLabel} value={form.description} onChangeText={(t) => update("description", t)} placeholder={descriptionPlaceholderLabel} multiline numberOfLines={4} />
          {form.name_ar || form.description_ar ? (
            <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "700" }]}>{translateArLabel}</Text>
              <Input label={arabicNameLabel} value={form.name_ar} onChangeText={(t) => update("name_ar", t)} placeholder="الاسم بالعربية" />
              <Input label={arabicDescLabel} value={form.description_ar} onChangeText={(t) => update("description_ar", t)} placeholder="الوصف بالعربية" multiline numberOfLines={3} />
            </View>
          ) : null}
          <Input testID="supplier-product-new-price" label={`Price (${currency.code}) *`} value={form.price} onChangeText={(t) => update("price", t)} placeholder="29.99" keyboardType="decimal-pad" />
          <Input testID="supplier-product-new-stock" label={stockQuantityLabel} value={form.stock} onChangeText={(t) => update("stock", t)} placeholder="100" keyboardType="number-pad" />
          <Input testID="supplier-product-new-return-window" label={returnWindowLabel} value={form.return_window_days} onChangeText={(t) => update("return_window_days", t)} placeholder="10" keyboardType="number-pad" />
          <Text style={s.textMuted}>{returnWindowHintLabel}</Text>
          <SearchableSelect
            label={categoryLabel}
            value={form.category}
            options={Object.keys(SUPPLIER_SUBCATEGORY_OPTIONS)}
            placeholder={categoryPlaceholderLabel}
            searchPlaceholder={categorySearchLabel}
            emptyLabel="No matching categories"
            onChange={(value) => {
              const nextCategory = resolveKnownCategory(value);
              update("category", nextCategory);
              update("subcategory", inferSuggestedSubCategory(nextCategory, nextCategory, form.subcategory));
            }}
          />
          <SearchableSelect
            label={subcategoryLabel}
            value={form.subcategory}
            options={subcategoryOptions}
            placeholder={subcategoryPlaceholderLabel}
            searchPlaceholder={subcategorySearchLabel}
            emptyLabel={subcategoryOptions.length > 0 ? "No matching sub-categories" : "Type a sub-category to use"}
            allowCustomEntry
            onChange={(value) => update("subcategory", value)}
          />
          <Input label={colorLabel} value={form.color} onChangeText={(t) => update("color", t)} placeholder={colorPlaceholderLabel} />
          <Input label={tagsLabel} value={form.tags} onChangeText={(t) => update("tags", t)} placeholder={tagsPlaceholderLabel} />
          <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>{variantsDetailsLabel}</Text>
            <Text style={s.textMuted}>{variantTemplate?.hint || variantsHintLabel}</Text>
            <View style={styles.chipRow}>
              {SUPPLIER_VARIANT_TEMPLATES.map((template) => (
                <TouchableOpacity
                  key={template.key}
                  onPress={() => setSelectedVariantTemplate((current) => current === template.key ? "" : template.key)}
                  style={[
                    styles.chip,
                    {
                      borderColor: selectedVariantTemplate === template.key ? theme.colors.brand : theme.colors.border,
                      backgroundColor: selectedVariantTemplate === template.key ? theme.colors.brand + "22" : theme.colors.surface1,
                    },
                  ]}
                >
                  <Text style={{ color: selectedVariantTemplate === template.key ? theme.colors.brand : theme.colors.text, fontSize: 12, fontWeight: "700" }}>{template.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
            {variantTemplate ? (
              <View style={styles.chipRow}>
                {variantTemplate.options.map((size) => {
                  const selectedSizes = normalizeSizesInput(form.sizes);
                  const active = selectedSizes.includes(size);
                  return (
                    <TouchableOpacity
                      key={size}
                      onPress={() => {
                        const next = active
                          ? selectedSizes.filter((item) => item !== size)
                          : [...selectedSizes, size];
                        update("sizes", next.join(", "));
                      }}
                      style={[
                        styles.chip,
                        {
                          borderColor: active ? theme.colors.brand : theme.colors.border,
                          backgroundColor: active ? theme.colors.brand : theme.colors.surface1,
                        },
                      ]}
                    >
                      <Text style={{ color: active ? "#fff" : theme.colors.text, fontSize: 12, fontWeight: "700" }}>{size}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            ) : null}
          </View>
          <Input label={variantOptionsLabel} value={form.sizes} onChangeText={(t) => update("sizes", t)} placeholder={variantTemplate?.customPlaceholder || "S, M, L or 250 ml, Pack of 2"} />

          <View style={[s.row, styles.toggleRow]}>
            <Text style={[s.text, { fontWeight: "600" }]}>{activeVisibleLabel}</Text>
            <Switch
              value={form.is_active}
              onValueChange={(v) => update("is_active", v)}
              trackColor={{ true: theme.colors.brand }}
              thumbColor="#fff"
            />
          </View>
        </View>

        {error && (
          <View testID="supplier-product-new-error" style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
            <Text style={{ color: theme.colors.danger }}>{error}</Text>
          </View>
        )}

          <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Ionicons name="shield-checkmark" size={16} color={theme.colors.brand} />
              <Text style={[s.text, { fontWeight: "700" }]}>{gccComplianceLabel}</Text>
            </View>
            <View style={[s.row, styles.toggleRow]}>
              <Text style={[s.text, { fontWeight: "600" }]}>{halalLabel}</Text>
              <Switch value={form.halal_compliance} onValueChange={(v) => update("halal_compliance", v)} trackColor={{ true: theme.colors.brand }} thumbColor="#fff" />
            </View>
            <View style={[s.row, styles.toggleRow]}>
              <Text style={[s.text, { fontWeight: "600" }]}>{modestyLabel}</Text>
              <Switch value={form.modesty_compliance} onValueChange={(v) => update("modesty_compliance", v)} trackColor={{ true: theme.colors.brand }} thumbColor="#fff" />
            </View>
          </View>

          <View style={[styles.mediaCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Ionicons name="cube" size={16} color={theme.colors.brand} />
              <Text style={[s.text, { fontWeight: "700" }]}>{logisticsLabel}</Text>
            </View>
            <Input label={weightLabel} value={form.weight_kg} onChangeText={(t) => update("weight_kg", t)} placeholder="0.5" keyboardType="decimal-pad" />
            <Input label={dimensionsLabel} value={form.dimensions} onChangeText={(t) => update("dimensions", t)} placeholder="10 x 10 x 5" />
          </View>

          <View style={{ flexDirection: "row", gap: 10 }}>
            <Button testID="supplier-product-new-save-draft" label={saveDraftLabel} onPress={handleSaveDraft} variant="secondary" loading={draftBusy} style={{ flex: 1 }} />
            <Button testID="supplier-product-new-load-draft" label={loadDraftLabel} onPress={handleLoadDraft} variant="ghost" loading={draftBusy} style={{ flex: 1 }} />
          </View>

        <Button testID="supplier-product-new-submit" label={createProductLabel} onPress={handleCreate} loading={saving} />
        <Button testID="supplier-product-new-cancel" label={cancelLabel} onPress={() => router.back()} variant="ghost" />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
