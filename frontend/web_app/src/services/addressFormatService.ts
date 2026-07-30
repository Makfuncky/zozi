import { apiFetch, parseJsonResponse } from "@/lib/api";

export interface AddressFormatConfig {
  countryCode: string;
  formatJson: {
    fields: string[];
    fieldLabels: Record<string, string>;
    requiredFields: string[];
    fieldPlaceholders?: Record<string, string>;
  };
}

/**
 * Service for dynamic address form generation based on country
 */
export const addressFormatService = {
  /**
   * Get address format configuration for a country
   */
  getAddressFormat: async (countryCode: string): Promise<AddressFormatConfig | null> => {
    const response = await apiFetch(`/admin/countries/${countryCode}/localization`);
    if (!response.ok) return null;
    const data = await parseJsonResponse(response);
    return {
      countryCode,
      formatJson: data.address_format || {
        fields: ["street", "city", "state", "postal_code", "country"],
        fieldLabels: {},
        requiredFields: ["street", "city", "country"],
      },
    };
  },

  /**
   * Validate address fields for a country
   */
  validateAddress: async (
    countryCode: string,
    address: Record<string, string>
  ): Promise<{ valid: boolean; errors: string[] }> => {
    const format = await addressFormatService.getAddressFormat(countryCode);
    if (!format) return { valid: true, errors: [] };

    const errors: string[] = [];
    for (const field of format.formatJson.requiredFields) {
      if (!address[field]?.trim()) {
        const label = format.formatJson.fieldLabels[field] || field;
        errors.push(`${label} is required`);
      }
    }

    return { valid: errors.length === 0, errors };
  },
};
