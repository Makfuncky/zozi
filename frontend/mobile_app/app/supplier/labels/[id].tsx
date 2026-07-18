/**
 * Dynamic route: /supplier/labels/:id
 * Thin wrapper that re-exports the existing supplier/label screen
 * using the Expo Router dynamic segment `:id` as the orderId param.
 */
import React from "react";

// Lazily import the full label screen content
const LabelScreen = require("../label").default as React.ComponentType<Record<string, unknown>>;

export default function SupplierLabelById(): React.ReactElement {
  // Expo Router provides `id` from the filename [id].tsx
  // The label screen internally reads `orderId` from useLocalSearchParams.
  // Since `id` is already in params we just render the label screen.
  return <LabelScreen />;
}
