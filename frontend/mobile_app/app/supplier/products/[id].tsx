import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, KeyboardAvoidingView, Platform, StyleSheet, Switch, ActivityIndicator, TouchableOpacity, Image } from "react-native";
import { Feather } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";

import { Stack, useRouter, useLocalSearchParams } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { toast } from "@/lib/toastStore";
import { hasEditAiSource, isVideoAsset } from "@/lib/supplierProductAi";
import type { Product } from "@shared/types";
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
  mediaPreview: { width: 88, height: 88, borderRadius: theme.radius.md, borderWidth: 1 },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8 },
});

function normalizeSizesInput(value?: string | null): string[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item).trim()).filter(Boolean);
    }
  } catch {
    // Keep legacy support.
  }
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export default function EditProductScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const currency = useCurrencyStore((state) => state.currency);
  const convert = useCurrencyStore((state) => state.convert);
  const toAED = useCurrencyStore((state) => state.toAED);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [editProductTitle, productNameLabel, productNamePlaceholder, generatingSuggestionsLabel, aiSuggestLabel, replaceMainPhotoLabel, selectProductMediaLabel, currentImageLabel, addGalleryMediaLabel, videoLabel, photoLabel, descriptionLabel, descriptionPlaceholderLabel, comparePriceLabel, comparePricePlaceholderLabel, discountStartsLabel, discountEndsLabel, stockQuantityLabel, categoryLabel, categoryPlaceholderLabel, colorLabel, colorPlaceholderLabel, tagsLabel, tagsPlaceholderLabel, variantsDetailsLabel, variantsHintLabel, variantOptionsLabel, activeVisibleLabel, saveChangesLabel, cancelLabel] = useTranslateTexts([
    "Edit Product",
    "Product Name *",
    "e.g. Wireless Headphones",
    "Generating suggestions…",
    "AI Suggest from product media",
    "Replace Main Photo / Add More Media",
    "Select Product Media",
    "Current image",
    "Add More Gallery Media",
    "Video",
    "Photo",
    "Description",
    "Product description...",
    "Compare Price / Original",
    "Leave empty for no discount",
    "Discount Starts (ISO)",
    "Discount Ends (ISO)",
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
    "Save Changes",
    "Cancel",
  ]);
  const [returnWindowLabel, returnWindowHintLabel] = useTranslateTexts([
    "Return Window (days)",
    "Minimum 10 days. Supplier payouts wait until this window expires.",
  ]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [mainImage, setMainImage] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [galleryMedia, setGalleryMedia] = useState<DocumentPicker.DocumentPickerAsset[]>([]);
  const [currentImageUrl, setCurrentImageUrl] = useState("");
  const [existingGalleryImageUrls, setExistingGalleryImageUrls] = useState<string[]>([]);

  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    compare_price: "",
    discount_starts_at: "",
    discount_ends_at: "",
    stock: "",
    category: "",
    color: "",
    tags: "",
    sizes: "",
    return_window_days: "10",
    is_active: true,
  });
  const [selectedVariantTemplate, setSelectedVariantTemplate] = useState("");
  const variantTemplate = getSupplierVariantTemplate(selectedVariantTemplate) ?? getSupplierVariantTemplate("universal");

  useEffect(() => {
    apiFetch<Product>(`/supplier/products/${id}`)
      .then((p) => {
        setForm({
          name: p.name,
          description: p.description ?? "",
          price: String(convert(Number(p.price ?? 0))),
          compare_price: p.compare_price ? String(convert(Number(p.compare_price))) : "",
          discount_starts_at: p.discount_starts_at ?? "",
          discount_ends_at: p.discount_ends_at ?? "",
          stock: String(p.stock),
          category: p.category,
          color: p.color ?? "",
          tags: p.tags ?? "",
          sizes: normalizeSizesInput(p.sizes).join(", "),
          return_window_days: String(p.return_window_days ?? 10),
          is_active: p.is_active ?? true,
        });
        setSelectedVariantTemplate(suggestSupplierVariantTemplate({ category: p.category, name: p.name, tags: p.tags }));
        setCurrentImageUrl(p.image_url ?? "");
        const existingGallery = (() => {
          if (!p.additional_images) return [] as string[];
          try {
            const parsed = JSON.parse(p.additional_images);
            if (!Array.isArray(parsed)) return [] as string[];
            return parsed
              .map((item) => String(item).trim())
              .filter((item) => item && !isVideoAsset(item));
          } catch {
            return [] as string[];
          }
        })();
        setExistingGalleryImageUrls(existingGallery);
      })
      .catch(() => setError("Could not load product."))
      .finally(() => setLoading(false));
  }, [convert, id]);

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
    if (!hasEditAiSource(form.name, form.description, mainImage, currentImageUrl, existingGalleryImageUrls)) {
      return setError("Add a product photo or product details first to use AI Suggest");
    }
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
      } else if (currentImageUrl.trim()) {
        payload.append("image_url", currentImageUrl.trim());
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
      existingGalleryImageUrls.forEach((imageUrl) => payload.append("image_urls", imageUrl));
      const data = await apiFetch<{ name?: string; description?: string; category?: string; color?: string; tags_string?: string }>("/ai/suggest", {
        method: "POST",
        body: payload,
      });
      const suggestedTemplate = suggestSupplierVariantTemplate({
        category: data.category || form.category,
        name: data.name || form.name,
        tags: data.tags_string || form.tags,
      });
      if (data.name) setForm((f) => ({ ...f, name: data.name! }));
      if (data.description) setForm((f) => ({ ...f, description: data.description! }));
      if (data.category) setForm((f) => ({ ...f, category: data.category! }));
      if (data.color) setForm((f) => ({ ...f, color: data.color! }));
      if (data.tags_string) setForm((f) => ({ ...f, tags: data.tags_string! }));
      if (!selectedVariantTemplate) setSelectedVariantTemplate(suggestedTemplate);
      toast.success("AI suggestions applied!");
    } catch {
      setError("AI Suggest failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }

  async function pickProductMedia() {
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
    } catch {
      setError("Could not pick the replacement image.");
    }
  }

  async function pickGalleryMedia() {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["image/*", "video/*"],
        copyToCacheDirectory: true,
        multiple: true,
      });
      if (!result.canceled && result.assets?.length) {
        setGalleryMedia((current) => [...current, ...result.assets].slice(0, 20));
      }
    } catch {
      setError("Could not pick gallery media.");
    }
  }

  async function handleSave() {
    if (!form.name.trim()) return setError("Product name is required");
    const price = parseFloat(form.price);
    if (isNaN(price) || price <= 0) return setError("Enter a valid price");
    const stock = parseInt(form.stock, 10);
    if (isNaN(stock) || stock < 0) return setError("Enter a valid stock quantity");
    const returnWindowDays = parseReturnWindow(form.return_window_days);
    if (returnWindowDays === null) return setError("Return window must be at least 10 days");

    setSaving(true);
    setError(null);

    try {
      if (mainImage || galleryMedia.length > 0) {
        const payload = new FormData();
        payload.append("name", form.name.trim());
        payload.append("description", form.description.trim());
        payload.append("price", String(toAED(price)));
        payload.append("stock_quantity", String(stock));
        payload.append("category", form.category.trim() || "General");
        payload.append("color", form.color.trim());
        payload.append("tags", form.tags.trim());
        payload.append("sizes", JSON.stringify(normalizeSizesInput(form.sizes)));
        payload.append("is_active", String(form.is_active));
        if (form.compare_price.trim()) {
          payload.append("compare_price", String(toAED(parseFloat(form.compare_price))));
        }
        if (form.discount_starts_at.trim()) payload.append("discount_starts_at", form.discount_starts_at.trim());
        if (form.discount_ends_at.trim()) payload.append("discount_ends_at", form.discount_ends_at.trim());
        if (mainImage) {
          payload.append("image", {
            uri: mainImage.uri,
            name: mainImage.name || "product.jpg",
            type: mainImage.mimeType || "image/jpeg",
          } as any);
        }
        galleryMedia.forEach((asset, index) => {
          const isVideo = (asset.mimeType || "").startsWith("video/");
          payload.append("additional_images", {
            uri: asset.uri,
            name: asset.name || (isVideo ? `product-video-${index + 1}.mp4` : `product-extra-${index + 1}.jpg`),
            type: asset.mimeType || (isVideo ? "video/mp4" : "image/jpeg"),
          } as any);
        });

        await apiFetch(`/supplier/products/${id}`, {
          method: "PUT",
          body: payload,
        });
      } else {
        await apiFetch(`/supplier/products/${id}`, {
          method: "PUT",
          body: JSON.stringify({
            name: form.name.trim(),
            description: form.description.trim() || undefined,
            price: toAED(price),
            compare_price: form.compare_price ? toAED(parseFloat(form.compare_price)) : null,
            discount_starts_at: form.discount_starts_at || null,
            discount_ends_at: form.discount_ends_at || null,
            stock_quantity: stock,
            category: form.category.trim() || undefined,
            color: form.color.trim() || undefined,
            tags: form.tags.trim() || undefined,
            sizes: JSON.stringify(normalizeSizesInput(form.sizes)),
            is_active: form.is_active,
          }),
        });
      }
      await apiFetch(`/supplier/products/${id}/return-window`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days: returnWindowDays }),
      });
      toast.success("Product updated!");
      router.back();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update product.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: editProductTitle }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <Stack.Screen options={{ title: editProductTitle }} />
      <ScrollView
        style={[s.container, isRtl ? { direction: "rtl" } : undefined]}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Input label={productNameLabel} value={form.name} onChangeText={(t) => update("name", t)} placeholder={productNamePlaceholder} />

          {/* AI Suggest button */}
          <TouchableOpacity
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

          <View style={{ gap: 10 }}>
            <Button label={mainImage ? replaceMainPhotoLabel : selectProductMediaLabel} onPress={pickProductMedia} variant="secondary" />
            {mainImage ? (
              <Image source={{ uri: mainImage.uri }} style={[styles.mediaPreview, { borderColor: theme.colors.border }]} />
            ) : currentImageUrl ? (
              <Text style={s.textMuted}>{currentImageLabel}: {currentImageUrl}</Text>
            ) : null}
          </View>

          <View style={{ gap: 10 }}>
            <Button label={addGalleryMediaLabel} onPress={pickGalleryMedia} variant="secondary" />
            {galleryMedia.length > 0 ? (
              <View style={{ gap: 8 }}>
                {galleryMedia.map((asset, index) => (
                  <TouchableOpacity
                    key={`${asset.uri}-${index}`}
                    onPress={() => setGalleryMedia((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                    style={{
                      borderWidth: 1,
                      borderRadius: theme.radius.md,
                      borderColor: theme.colors.border,
                      backgroundColor: theme.colors.surface1,
                      padding: 12,
                    }}
                  >
                    <Text style={[s.text, { fontSize: 12 }]} numberOfLines={1}>
                      {asset.name || `${(asset.mimeType || "").startsWith("video/") ? videoLabel : photoLabel} ${index + 1}`}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            ) : null}
          </View>

          <Input label={descriptionLabel} value={form.description} onChangeText={(t) => update("description", t)} placeholder={descriptionPlaceholderLabel} multiline numberOfLines={4} />
          <Input label={`Price (${currency.code}) *`} value={form.price} onChangeText={(t) => update("price", t)} placeholder="29.99" keyboardType="decimal-pad" />
          <Input label={`${comparePriceLabel} (${currency.code})`} value={form.compare_price} onChangeText={(t) => update("compare_price", t)} placeholder={comparePricePlaceholderLabel} keyboardType="decimal-pad" />
          <Input label={discountStartsLabel} value={form.discount_starts_at} onChangeText={(t) => update("discount_starts_at", t)} placeholder="2026-03-26T10:00:00" autoCapitalize="none" />
          <Input label={discountEndsLabel} value={form.discount_ends_at} onChangeText={(t) => update("discount_ends_at", t)} placeholder="2026-03-28T23:59:00" autoCapitalize="none" />
          <Input label={stockQuantityLabel} value={form.stock} onChangeText={(t) => update("stock", t)} placeholder="100" keyboardType="number-pad" />
          <Input label={returnWindowLabel} value={form.return_window_days} onChangeText={(t) => update("return_window_days", t)} placeholder="10" keyboardType="number-pad" />
          <Text style={s.textMuted}>{returnWindowHintLabel}</Text>
          <Input label={categoryLabel} value={form.category} onChangeText={(t) => update("category", t)} placeholder={categoryPlaceholderLabel} />
          <Input label={colorLabel} value={form.color} onChangeText={(t) => update("color", t)} placeholder={colorPlaceholderLabel} />
          <Input label={tagsLabel} value={form.tags} onChangeText={(t) => update("tags", t)} placeholder={tagsPlaceholderLabel} />
          <View style={[styles.card, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}> 
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
          <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
            <Text style={{ color: theme.colors.danger }}>{error}</Text>
          </View>
        )}

        <Button label={saveChangesLabel} onPress={handleSave} loading={saving} />
        <Button label={cancelLabel} onPress={() => router.back()} variant="ghost" />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
