"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { apiFetch, getErrorMessage, handleApiError } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface UseApiOptions {
  showToastOnError?: boolean;
  errorMessage?: string;
  successMessage?: string;
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (path: string, options?: RequestInit) => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for API calls with automatic error handling and toast notifications
 */
export function useApi<T = any>(options: UseApiOptions = {}): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addToast } = useToastStore();
  const optionsRef = useRef(options);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const execute = useCallback(async (path: string, fetchOptions: RequestInit = {}): Promise<T | null> => {
    const currentOptions = optionsRef.current;
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch(path, fetchOptions);
      const responseData = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = getErrorMessage(responseData) || currentOptions.errorMessage || "Request failed";
        setError(errorMsg);

        if (currentOptions.showToastOnError !== false) {
          addToast(errorMsg, "error");
        }

        handleApiError(responseData, path);
        currentOptions.onError?.(responseData);
        return null;
      }

      setData(responseData);

      if (currentOptions.successMessage) {
        addToast(currentOptions.successMessage, "success");
      }

      currentOptions.onSuccess?.(responseData);
      return responseData;
    } catch (err) {
      const errorMsg = currentOptions.errorMessage || "Network error occurred";
      setError(errorMsg);

      if (currentOptions.showToastOnError !== false) {
        addToast(errorMsg, "error");
      }

      handleApiError(err, path);
      currentOptions.onError?.(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

/**
 * Hook for simple API mutations (POST, PUT, DELETE) with loading states
 */
export function useApiMutation<T = any>(options: UseApiOptions = {}) {
  const { execute, ...api } = useApi<T>(options);

  const mutate = useCallback(async (path: string, method: string, body?: any) => {
    const fetchOptions: RequestInit = { method };

    if (body) {
      fetchOptions.headers = { "Content-Type": "application/json" };
      fetchOptions.body = JSON.stringify(body);
    }

    return execute(path, fetchOptions);
  }, [execute]);

  return {
    ...api,
    execute,
    mutate,
    post: (path: string, body?: any) => mutate(path, "POST", body),
    put: (path: string, body?: any) => mutate(path, "PUT", body),
    patch: (path: string, body?: any) => mutate(path, "PATCH", body),
    delete: (path: string) => mutate(path, "DELETE"),
  };
}
