import { apiFetch, parseJsonResponse } from "@/lib/api";

export interface LocalizationConfig {
  defaultLanguage: string;
  supportedLanguages: string[];
  rtlEnabled: boolean;
  numberFormat: "western" | "eastern";
  calendarType: "gregorian" | "hijri";
}

export interface AddressFormat {
  countryCode: string;
  formatJson: {
    fields: string[];
    fieldLabels: Record<string, string>;
    requiredFields: string[];
  };
}

/**
 * Service for localization and regional formatting
 */
export const localizationService = {
  /**
   * Get localization config for a country
   */
  getLocalizationConfig: async (countryCode: string): Promise<LocalizationConfig | null> => {
    const response = await apiFetch(`/admin/countries/${countryCode}/localization`);
    if (!response.ok) return null;
    const data = await parseJsonResponse(response);
    return {
      defaultLanguage: data.default_language || "en",
      supportedLanguages: data.supported_languages || ["en"],
      rtlEnabled: data.rtl_enabled || false,
      numberFormat: data.number_format || "western",
      calendarType: data.calendar_type || "gregorian",
    };
  },

  /**
   * Format number based on locale settings (Eastern Arabic vs Western)
   */
  formatNumber: (
    num: number,
    locale: string,
    numberFormat: "western" | "eastern" = "western"
  ): string => {
    const formatter = new Intl.NumberFormat(locale);
    const formatted = formatter.format(num);

    if (numberFormat === "eastern" && locale.startsWith("ar")) {
      // Convert Western Arabic numerals to Eastern Arabic numerals
      const easternDigits = "٠١٢٣٤٥٦٧٨٩";
      return formatted.replace(/\d/g, (d) => easternDigits[parseInt(d, 10)] || d);
    }

    return formatted;
  },
};
