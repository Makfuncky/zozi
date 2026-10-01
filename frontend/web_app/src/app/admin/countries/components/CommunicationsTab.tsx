"use client";

import { Fragment } from "react";
import InternalCommunicationsSystem from "@/components/country/InternalCommunicationsSystem";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function CommunicationsTab({
  ...p
}: CountriesTabProps) {
  const { selectedCountryCode } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Internal Communications</h3>
      <p className="text-xs text-text-muted">Country-specific internal messaging between Admin, Country Head, and Country Manager teams.</p>
      {selectedCountryCode && (
        <InternalCommunicationsSystem countryCode={selectedCountryCode} />
      )}
    </section>
  );
}
