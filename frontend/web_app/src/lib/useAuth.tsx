"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getAccessToken, setAccessToken, clearAccessToken, silentlyRefreshAccessToken } from "@/lib/api";
import { useLocaleStore } from "@/lib/localeStore";
import { useCartStore } from "@/lib/cartStore";
import { useAuthModalStore } from "@/lib/authModalStore";
import type { Locale } from "@/lib/i18n";
import { normalizeLocale } from "@shared/localization";
import {
  clearAdminPermissionOverrides,
  isAdminStaffRole,
  setCurrentAdminPermissions,
  setAdminPermissionOverrides,
} from "@shared/adminPermissions";

/* ---------- Types ------------------------------------------- */
export interface UserInfo {
  id: number;
  email: string;
  username: string;
  role: "customer" | "supplier" | "admin" | "logistics_partner" | "sub_admin" | "moderator" | "support" | "country_head" | "country_manager" | "employee";
  full_name?: string | null;
  phone?: string | null;
  profile_image?: string | null;
  address_book?: string | null;
  preferred_language?: string;
  preferred_currency?: string;
  preferred_country?: string;
  email_verified?: boolean;
  staff_role_label?: string | null;
  staff_title?: string | null;
  staff_department?: string | null;
  staff_area_of_operation?: string | null;
  staff_hire_date?: string | null;
  staff_experience_level?: string | null;
  staff_performance_summary?: string | null;
  staff_assigned_tasks?: string[];
  staff_assigned_projects?: string[];
  permissions?: string[];
  staff_notes?: string | null;
  staff_country_codes?: string[];
}

interface AuthContextValue {
  user: UserInfo | null;
  isLoading: boolean;
  isLoggedIn: boolean;
  refresh: (force?: boolean) => Promise<UserInfo | null>;
  logout: () => void;
}

/* ---------- Context ----------------------------------------- */
const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  isLoggedIn: false,
  refresh: async () => null,
  logout: () => {},
});

/* ---------- Provider ---------------------------------------- */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const refresh = useCallback(async (force = false) => {
    const applyAuthenticatedUser = async (userData: UserInfo) => {
      setUser(userData);
      localStorage.setItem("zozi_has_session", "1");

      if (isAdminStaffRole(userData.role)) {
        setCurrentAdminPermissions(userData.permissions ?? null);
        try {
          const hierarchyRes = await apiFetch("/admin/hierarchy/permissions");
          if (hierarchyRes.ok) {
            const hierarchyData = await hierarchyRes.json();
            setAdminPermissionOverrides(hierarchyData?.matrix ?? null);
          } else {
            clearAdminPermissionOverrides();
          }
        } catch (error) {
          console.error("Failed to fetch admin permissions:", error);
          clearAdminPermissionOverrides();
        }
      } else {
        clearAdminPermissionOverrides();
      }

      if (userData.preferred_language) {
        const lang = normalizeLocale(userData.preferred_language) as Locale;
        const current = useLocaleStore.getState().locale;
        if (current !== lang) useLocaleStore.getState().setLocale(lang);
      }

      void useCartStore.getState().syncOnLogin();
      return userData;
    };

    try {
      // Check whether we have a session flag — avoids a round-trip for
      // fully unauthenticated visitors.
      const hasSession = localStorage.getItem("zozi_has_session") === "1";
      const currentAccessToken =
        typeof getAccessToken === "function" ? getAccessToken() : null;

      if (!force && !hasSession && !currentAccessToken) {
        clearAdminPermissionOverrides();
        setUser(null);
        setIsLoading(false);
        return null;
      }

      if (currentAccessToken) {
        const meRes = await apiFetch("/auth/me");
        if (meRes.ok) {
          const userData = await meRes.json();
          return await applyAuthenticatedUser(userData);
        }
      }

      if (!hasSession) {
        clearAccessToken();
        clearAdminPermissionOverrides();
        setUser(null);
        return null;
      }

      // Attempt a silent token refresh via the httpOnly refresh cookie.
      // Uses the centralized refresh logic to avoid duplicating fetch behavior.
      const refreshResult = await silentlyRefreshAccessToken();

      if (refreshResult.status === "ok") {
        // Fetch the user profile using the refreshed in-memory access token.
        const meRes = await apiFetch("/auth/me");
        if (meRes.ok) {
          const userData = await meRes.json();
          return await applyAuthenticatedUser(userData);
        }
        clearAccessToken();
        clearAdminPermissionOverrides();
        localStorage.removeItem("zozi_has_session");
        setUser(null);
        return null;
      }

      // "no_session" / "rejected": the session is genuinely gone. We still
      // preserve the local cart (it becomes a valid guest cart) — detaching
      // from the server is handled by the cart store's isAuthenticated() guard.
      if (refreshResult.status !== "network") {
        clearAccessToken();
        clearAdminPermissionOverrides();
        localStorage.removeItem("zozi_has_session");
      }
      setUser(null);
      setIsLoading(false);
      return null;
    } catch {
      // A transient error during refresh must NOT wipe the local cart or the
      // session flag — a later page load will retry the refresh.
      clearAccessToken();
      clearAdminPermissionOverrides();
      setUser(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {
      // ignore — clear local state regardless
    }
    clearAccessToken();
    clearAdminPermissionOverrides();
    localStorage.removeItem("zozi_has_session");
    useCartStore.getState().clearLocalCart();
    setUser(null);
    router.push("/");
  }, [router]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const handleAuthExpired = () => {
      clearAccessToken();
      clearAdminPermissionOverrides();
      setUser(null);
      setIsLoading(false);
      localStorage.removeItem("zozi_has_session");
      useCartStore.getState().detachFromServer();
      if (
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/supplier") &&
        !window.location.pathname.startsWith("/admin")
      ) {
        useAuthModalStore.getState().open("login");
      }
    };

    window.addEventListener("zozi:auth-expired", handleAuthExpired);
    return () => window.removeEventListener("zozi:auth-expired", handleAuthExpired);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isLoggedIn: !!user, refresh, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/* ---------- Hooks ------------------------------------------- */
export function useAuth() {
  return useContext(AuthContext);
}

/** Redirects non-suppliers to /supplier/login */
export function useRequireSupplier() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && (!user || user.role !== "supplier")) {
      router.replace("/supplier/login");
    }
  }, [user, isLoading, router]);

  return { user, isLoading };
}

/** Redirects non-admins to /admin/login */
export function useRequireAdmin() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && (!user || user.role !== "admin")) {
      router.replace("/admin/login");
    }
  }, [user, isLoading, router]);

  return { user, isLoading };
}

/** Redirects non-partners to /logistics-partner/login */
export function useRequireLogisticsPartner() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && (!user || user.role !== "logistics_partner")) {
      router.replace("/logistics-partner/login");
    }
  }, [user, isLoading, router]);

  return { user, isLoading };
}


