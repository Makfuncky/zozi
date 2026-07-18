"use client";

import { useState, useEffect } from "react";
import { addressFormatService, type AddressFormatConfig } from "@/services/addressFormatService";

interface DynamicAddressFormProps {
  countryCode: string;
  value?: Record<string, string>;
  onChange?: (value: Record<string, string>) => void;
  requiredOnly?: boolean;
}

export default function DynamicAddressForm({
  countryCode,
  value = {},
  onChange,
  requiredOnly = false,
}: DynamicAddressFormProps) {
  const [config, setConfig] = useState<AddressFormatConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [address, setAddress] = useState<Record<string, string>>(value);

  useEffect(() => {
    const loadConfig = async () => {
      setLoading(true);
      const cfg = await addressFormatService.getAddressFormat(countryCode);
      setConfig(cfg);
      setLoading(false);
    };
    loadConfig();
  }, [countryCode]);

  useEffect(() => {
    onChange?.(address);
  }, [address, onChange]);

  if (loading) {
    return <div className="text-sm text-text-muted">Loading address format...</div>;
  }

  if (!config) {
    return <div className="text-sm text-text-muted">No address format configured for this country</div>;
  }

  const fieldsToShow = requiredOnly
    ? config.formatJson.requiredFields
    : config.formatJson.fields;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {fieldsToShow.map((field) => {
        const label = config.formatJson.fieldLabels[field] || field.replace(/_/g, " ");
        const placeholder = config.formatJson.fieldPlaceholders?.[field] || "";
        const isRequired = config.formatJson.requiredFields.includes(field);

        return (
          <label key={field} className={`space-y-1 text-xs ${fieldsToShow.length === 1 ? "md:col-span-2" : ""}`}>
            <span className="flex items-center gap-1">
              {label}
              {isRequired && <span className="text-danger">*</span>}
            </span>
            <input
              type="text"
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={address[field] || ""}
              onChange={(e) => setAddress((prev) => ({ ...prev, [field]: e.target.value }))}
              placeholder={placeholder || label}
            />
          </label>
        );
      })}
    </div>
  );
}


