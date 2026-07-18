"use client";

import { Button } from "@/components/ui/Button";

import { useState } from "react";
import { FileText, Download, Save, RefreshCw, ShieldCheck, Users, DollarSign, Package } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface LegalContractTemplate {
  id: string;
  name: string;
  type: "supplier_agreement" | "terms_of_service" | "privacy_policy" | "return_policy";
  content: string;
  variables: string[];
  is_active: boolean;
}

interface CountryLegalContractProps {
  countryCode: string;
  legalRules: {
    minimum_order_age: number;
    max_returns_allowed: number;
    return_window_days: number;
    refund_processing_days: number;
    requires_commercial_license: boolean;
    requires_vat_registration: boolean;
    product_restrictions: string[];
  } | null;
}

const DEFAULT_TEMPLATES: Record<string, LegalContractTemplate> = {
  supplier_agreement: {
    id: "supplier_agreement",
    name: "Supplier Agreement",
    type: "supplier_agreement",
    content: `SUPPLIER AGREEMENT FOR {COUNTRY_NAME}

This Agreement is entered into by and between [COMPANY NAME] and the Supplier for sales in {COUNTRY_NAME}.

1. REGULATORY COMPLIANCE
Suppliers must comply with all local laws including:
- Commercial Registration (CR) requirements: {REQUIRES_CR}
- VAT Registration: {REQUIRES_VAT}
- Minimum order age: {MIN_ORDER_AGE} years

2. PRODUCT RESTRICTIONS
The following product categories are restricted: {PRODUCT_RESTRICTIONS}

3. RETURN POLICY
- Maximum returns allowed per order: {MAX_RETURNS}
- Return window: {RETURN_WINDOW} days
- Refund processing time: {REFUND_DAYS} days

4. TAX OBLIGATIONS
Suppliers are responsible for collecting and remitting all applicable taxes.`,
    variables: ["COUNTRY_NAME", "REQUIRES_CR", "REQUIRES_VAT", "MIN_ORDER_AGE", "PRODUCT_RESTRICTIONS", "MAX_RETURNS", "RETURN_WINDOW", "REFUND_DAYS"],
    is_active: true,
  },
  terms_of_service: {
    id: "terms_of_service",
    name: "Terms of Service",
    type: "terms_of_service",
    content: `TERMS OF SERVICE FOR {COUNTRY_NAME}

By using our platform in {COUNTRY_NAME}, you agree to these Terms of Service.

1. APPLICABLE LAW
These terms are governed by the laws of {COUNTRY_NAME}.

2. PROHIBITED ITEMS
The following items are prohibited: {PRODUCT_RESTRICTIONS}

3. AGE REQUIREMENT
Users must be at least {MIN_ORDER_AGE} years old.`,
    variables: ["COUNTRY_NAME", "PRODUCT_RESTRICTIONS", "MIN_ORDER_AGE"],
    is_active: true,
  },
};

export default function CountryLegalContractGenerator({ countryCode, legalRules }: CountryLegalContractProps) {
  const addToast = useToastStore((state) => state.addToast);
  const [templates, setTemplates] = useState<LegalContractTemplate[]>(Object.values(DEFAULT_TEMPLATES));
  const [selectedTemplate, setSelectedTemplate] = useState<LegalContractTemplate | null>(null);
  const [generatedContent, setGeneratedContent] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleGenerate = async () => {
    if (!selectedTemplate || !legalRules) return;
    
    setIsGenerating(true);
    try {
      // Replace template variables with actual values
      let content = selectedTemplate.content;
      
      const replacements: Record<string, string> = {
        "{COUNTRY_NAME}": countryCode,
        "{REQUIRES_CR}": legalRules.requires_commercial_license ? "Required" : "Not Required",
        "{REQUIRES_VAT}": legalRules.requires_vat_registration ? "Required" : "Not Required",
        "{MIN_ORDER_AGE}": String(legalRules.minimum_order_age),
        "{PRODUCT_RESTRICTIONS}": legalRules.product_restrictions.length > 0 
          ? legalRules.product_restrictions.join(", ") 
          : "None",
        "{MAX_RETURNS}": String(legalRules.max_returns_allowed),
        "{RETURN_WINDOW}": String(legalRules.return_window_days),
        "{REFUND_DAYS}": String(legalRules.refund_processing_days),
      };

      Object.entries(replacements).forEach(([key, value]) => {
        content = content.replace(new RegExp(key, "g"), value);
      });

      setGeneratedContent(content);
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to generate contract", "error");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([generatedContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedTemplate?.id || "contract"}-${countryCode}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSave = async () => {
    if (!selectedTemplate || !generatedContent) return;
    
    setIsSaving(true);
    try {
      const response = await apiFetch(`/admin/countries/${countryCode}/legal-contracts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template_id: selectedTemplate.id,
          content: generatedContent,
        }),
      });
      
      if (!response.ok) {
        throw new Error("Failed to save contract");
      }
      
      addToast("Contract saved successfully", "success");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to save contract", "error");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Legal Contract Generator</h3>
        </div>
      </div>

      <p className="text-xs text-text-muted">
        Generate country-specific legal documents with auto-filled regulatory requirements.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Template Selector */}
        <div className="space-y-3">
          <span className="text-xs font-semibold text-text-muted">Select Template</span>
          <div className="space-y-2">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => {
                  setSelectedTemplate(template);
                  setGeneratedContent("");
                }}
                className={`w-full text-left p-3 rounded-lg border transition ${
                  selectedTemplate?.id === template.id
                    ? "border-primary bg-primary/10"
                    : "border-border bg-surface hover:bg-surface-2"
                }`}
              >
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium text-text">{template.name}</span>
                </div>
                <p className="text-[10px] text-text-faint mt-1">
                  {template.type.replace("_", " ").toUpperCase()}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Preview & Actions */}
        <div className="space-y-3">
          <span className="text-xs font-semibold text-text-muted">Generated Document</span>
          <div className="border border-border rounded-lg bg-surface-1 h-64 overflow-hidden">
            {generatedContent ? (
              <pre className="p-4 text-[11px] text-text font-mono h-full overflow-auto whitespace-pre-wrap">
                {generatedContent}
              </pre>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-text-faint">
                <FileText className="h-8 w-8 mb-2" />
                <p className="text-xs">Select a template and generate to preview</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t border-border/60">
        <button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || !selectedTemplate || !legalRules}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text hover:bg-surface-2 transition disabled:opacity-40"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isGenerating ? "animate-spin" : ""}`} />
          {isGenerating ? "Generating..." : "Generate Document"}
        </button>
        <Button variant="primary" type="button"
          onClick={handleDownload}
          disabled={!generatedContent}>
          <Download className="h-3.5 w-3.5" />
          Download
        </Button>
        <Button variant="primary" type="button"
          onClick={handleSave}
          disabled={isSaving || !generatedContent}>
          <Save className="h-3.5 w-3.5" />
          {isSaving ? "Saving..." : "Save"}
        </Button>
      </div>
    </div>
  );
}


