import { useState, useEffect, useCallback, useRef } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";

export interface AutoPopulateResult {
  code: string;
  name: string;
  currency: string;
  currency_symbol?: string;
  phone_code?: string;
  language?: string;
  timezone?: string;
  tax_type?: string;
  tax_rate?: number;
  tax_name?: string;
  logistics_model?: string;
  base_rate?: number;
  minimum_charge?: number;
  payment_methods?: string[];
  suggested_tax_type?: string;
  suggested_tax_rate?: number;
  suggested_tax_name?: string;
  suggested_legal_rules?: {
    minimum_order_age: number;
    max_returns_allowed: number;
    return_window_days: number;
    refund_processing_days: number;
    product_restrictions: string[];
  };
  suggested_cities?: string[];
  _source?: "world_bank" | "algorithmic" | "api_fallback" | "manual";
}

interface UseCountryAutoPopulateOptions {
  onSuccess?: (result: AutoPopulateResult) => void;
  onError?: (error: string) => void;
}

export function useCountryAutoPopulate(options: UseCountryAutoPopulateOptions = {}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [result, setResult] = useState<AutoPopulateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const clearDebounce = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
  }, []);

  const fetchAutoPopulate = useCallback(async (term: string) => {
    if (!term.trim()) {
      setResult(null);
      setError(null);
      return;
    }

    // Cancel previous request
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/admin/countries/auto-populate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ search_term: term }),
        signal: abortRef.current.signal,
      });

      const data = await parseJsonResponse(response);
      
      if (!response.ok) {
        throw new Error(data?.detail || "Auto-populate failed");
      }

      setResult(data);
      options.onSuccess?.(data);
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setError(err.message);
        options.onError?.(err.message);
        setResult(null);
      }
    } finally {
      if (abortRef.current?.signal.aborted !== true) {
        setLoading(false);
      }
    }
  }, [options]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);
    clearDebounce();
    
    debounceRef.current = setTimeout(() => {
      fetchAutoPopulate(value);
    }, 600);
  }, [clearDebounce, fetchAutoPopulate]);

  const reset = useCallback(() => {
    clearDebounce();
    setSearchTerm("");
    setResult(null);
    setError(null);
    setLoading(false);
  }, [clearDebounce]);

  useEffect(() => {
    return () => {
      clearDebounce();
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [clearDebounce]);

  return {
    searchTerm,
    result,
    loading,
    error,
    setSearchTerm: handleSearchChange,
    reset,
  };
}
