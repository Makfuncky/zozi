"use client";

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";

export interface AdminCountryInfo {
  code: string;
  name: string;
  currency?: string;
  is_active?: boolean;
}

interface AdminCountryCtx {
  selectedCountry: AdminCountryInfo | null;
  assignedCountries: AdminCountryInfo[];
  setAdminCountry: (code: string) => Promise<void>;
  loading: boolean;
  isGlobalView: boolean;
}

const ALL_COUNTRIES_OPTION: AdminCountryInfo = {
  code: "*",
  name: "All Countries",
};

const AdminCountryContext = createContext<AdminCountryCtx>({
  selectedCountry: null,
  assignedCountries: [],
  setAdminCountry: async () => {},
  loading: true,
  isGlobalView: false,
});

export function AdminCountryProvider({ children }: { children: ReactNode }) {
  const [assignedCountries, setAssignedCountries] = useState<AdminCountryInfo[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<AdminCountryInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [isGlobalView, setIsGlobalView] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // NOTE: use the public /countries list (not /admin/countries) — the latter
        // collides with the /admin/countries Next.js page route and returns HTML.
        const res = await apiFetch("/countries");
        if (cancelled) return;
        if (res.ok) {
          const raw = await parseJsonResponse(res);
          const list: any[] = Array.isArray(raw)
            ? raw
            : Array.isArray(raw?.data)
              ? raw.data
              : Array.isArray(raw?.items)
                ? raw.items
                : [];
          if (cancelled) return;
          const mapped = list.map((c: any) => ({
            code: c.code,
            name: c.name,
            currency: c.currency,
            is_active: c.is_active,
          }));

          if (mapped.length > 1) {
            setAssignedCountries([ALL_COUNTRIES_OPTION, ...mapped]);
          } else {
            setAssignedCountries(mapped);
          }

          const stored =
            typeof window !== "undefined"
              ? window.localStorage.getItem("zozi_admin_country")
              : null;

          if (stored === "*" && mapped.length > 1) {
            setIsGlobalView(true);
            setSelectedCountry(ALL_COUNTRIES_OPTION);
          } else if (stored) {
            const found = mapped.find((c) => c.code === stored);
            if (found) {
              setSelectedCountry(found);
              setIsGlobalView(false);
            }
          }

          if (!stored && mapped.length === 1) {
            setSelectedCountry(mapped[0]);
            setIsGlobalView(false);
          } else if (!stored && mapped.length > 1) {
            setIsGlobalView(true);
            setSelectedCountry(ALL_COUNTRIES_OPTION);
          }
        }
      } catch {
        // non-critical
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const setAdminCountry = useCallback(
    async (code: string) => {
      if (code === "*") {
        setIsGlobalView(true);
        setSelectedCountry(ALL_COUNTRIES_OPTION);
        window.localStorage.setItem("zozi_admin_country", "*");
        return;
      }
      const found = assignedCountries.find((c) => c.code === code);
      if (found) {
        setSelectedCountry(found);
        setIsGlobalView(false);
        window.localStorage.setItem("zozi_admin_country", code);
      }
    },
    [assignedCountries],
  );

  return (
    <AdminCountryContext.Provider
      value={{ selectedCountry, assignedCountries, setAdminCountry, loading, isGlobalView }}
    >
      {children}
    </AdminCountryContext.Provider>
  );
}

export function useAdminCountry() {
  return useContext(AdminCountryContext);
}
