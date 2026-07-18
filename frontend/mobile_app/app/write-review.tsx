import React, { useState } from "react";
import { View, Text, ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform, StyleSheet } from "react-native";

import { useLocalSearchParams, useRouter } from "expo-router";
import { createReview } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import ScreenHeader from "@/components/ui/ScreenHeader";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    padding: 20,
    gap: theme.spacing.md,
    paddingBottom: 40,
  },
  center: {
    alignItems: "center",
    gap: 12,
    marginTop: 40,
  },
  productBanner: {
    padding: 14,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    gap: theme.spacing.xs,
  },
  ratingSection: {
    alignItems: "center",
    gap: theme.spacing.xs,
    paddingVertical: theme.spacing.sm,
  },
  starRow: {
    flexDirection: "row",
    gap: 6,
  },
  errorBox: {
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
});

function StarRating({ rating, onChange }: { rating: number; onChange: (r: number) => void }) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  return (
    <View style={styles.starRow}>
      {[1, 2, 3, 4, 5].map((star) => (
        <TouchableOpacity key={star} onPress={() => onChange(star)} activeOpacity={0.7}>
          <Text style={{ fontSize: theme.fontSize["2xl"], color: star <= rating ? "#facc15" : theme.colors.border }}>
            ★
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const RATING_LABELS: Record<number, string> = {
  1: "Poor",
  2: "Fair",
  3: "Good",
  4: "Very Good",
  5: "Excellent",
};

export default function WriteReviewScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const styles = createStyles(theme);
  const router = useRouter();
  const { productId, productName } = useLocalSearchParams<{
    productId: string;
    productName: string;
  }>();

  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (rating === 0) return setError("Please select a rating");
    if (comment.trim().length < 10) return setError("Review must be at least 10 characters");
    if (!productId) return setError("Invalid product");

    setLoading(true);
    setError(null);
    try {
      await createReview({
        product_id: Number(productId),
        rating,
        comment: comment.trim(),
      });
      setDone(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit review");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScreenHeader title="Write a Review" />
      <ScrollView
        contentContainerStyle={[s.container, styles.scroll, { backgroundColor: theme.colors.surface0 }]}
        keyboardShouldPersistTaps="handled"
      >
        {done ? (
          <View style={styles.center}>
            <Text style={{ fontSize: theme.fontSize["3xl"], textAlign: "center" }}>🎉</Text>
            <Text style={[s.title, { textAlign: "center" }]}>Review Submitted!</Text>
            <Text style={[s.textMuted, { textAlign: "center" }]}>
              Thank you for sharing your feedback.
            </Text>
            <Button
              label="Back to Product"
              onPress={() => router.back()}
              style={{ marginTop: 20 }}
            />
          </View>
        ) : (
          <>
            {/* Product name */}
            {productName && (
              <View style={[styles.productBanner, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>Reviewing</Text>
                <Text style={[s.text, { fontWeight: "600" }]} numberOfLines={2}>{productName}</Text>
              </View>
            )}

            {/* Star rating */}
            <View style={styles.ratingSection}>
              <Text style={[s.text, { fontWeight: "600", marginBottom: theme.spacing.xs }]}>Your Rating</Text>
              <StarRating rating={rating} onChange={(r) => { setRating(r); setError(null); }} />
              {rating > 0 && (
                <Text style={{ color: theme.colors.brand, fontWeight: "600", marginTop: theme.spacing.xs }}>
                  {RATING_LABELS[rating]}
                </Text>
              )}
            </View>

            {/* Error */}
            {error && (
              <View style={[styles.errorBox, { backgroundColor: theme.colors.danger + "22", borderColor: theme.colors.danger }]}>
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.base }}>{error}</Text>
              </View>
            )}

            {/* Comment */}
            <Input
              label="Your Review"
              placeholder="Share your experience with this product…"
              value={comment}
              onChangeText={(t) => { setComment(t); setError(null); }}
              multiline
              numberOfLines={6}
            />

            <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, textAlign: "right" }]}>
              {comment.length} / 1000
            </Text>

            <Button
              label="Submit Review"
              onPress={handleSubmit}
              loading={loading}
              disabled={rating === 0}
            />
            <Button
              label="Cancel"
              onPress={() => router.back()}
              variant="secondary"
            />
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
