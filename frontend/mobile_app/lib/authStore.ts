import { create } from "zustand";
import {
  login as apiLogin,
  logout as apiLogout,
  getMe,
  register as apiRegister,
  restoreTokens,
  getStoredRefreshToken,
  refreshAccessToken,
  tokenAdapter,
  socialLogin,
  SocialAuthPayload,
} from "@/lib/api";

export interface UserInfo {
  id: number;
  email: string;
  username: string;
  role: "customer" | "supplier" | "admin" | "logistics_partner" | "sub_admin" | "moderator" | "support" | "country_head" | "country_manager" | "employee";
  profile_image?: string;
  phone?: string;
  email_verified?: boolean;
  is_verified?: boolean;
}

interface AuthState {
  user: UserInfo | null;
  isLoading: boolean;
  isLoggedIn: boolean;
  initialize: () => Promise<void>;
  login: (identifier: string, password: string, remember?: boolean) => Promise<UserInfo>;
  register: (payload: {
    email: string;
    password: string;
    username: string;
    role?: string;
    [key: string]: unknown;
  }) => Promise<UserInfo>;
  loginWithGoogle: () => Promise<UserInfo>;
  loginWithFacebook: () => Promise<UserInfo>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
}

function clearPersistedSession() {
  tokenAdapter.clearAccessToken();
  tokenAdapter.clearRefreshToken();
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isLoggedIn: false,

  async initialize() {
    set({ isLoading: true });
    try {
      // Skip token restoration on web - we'll handle it differently
      const isWeb = typeof window !== "undefined";
      
      // Try restoring access token from secure store
      const hasValidToken = isWeb ? false : await restoreTokens();

      if (hasValidToken) {
        const user = await getMe();
        set({ user, isLoggedIn: true });
      } else {
        // Try silent refresh (only on mobile)
        if (!isWeb) {
          const refreshToken = await getStoredRefreshToken();
          if (refreshToken) {
            const ok = await refreshAccessToken();
            if (ok) {
              const user = await getMe();
              set({ user, isLoggedIn: true });
            } else {
              clearPersistedSession();
              set({ user: null, isLoggedIn: false });
            }
          } else {
            set({ user: null, isLoggedIn: false });
          }
        } else {
          set({ user: null, isLoggedIn: false });
        }
      }
    } catch {
      clearPersistedSession();
      set({ user: null, isLoggedIn: false });
    } finally {
      set({ isLoading: false });
    }
  },

  async login(identifier, password, remember = true) {
    const res = await apiLogin({ email: identifier, password }, remember);
    set({ user: res.user, isLoggedIn: true });
    return res.user;
  },

  async register(payload) {
    const res = await apiRegister(payload as any);
    set({ user: res.user, isLoggedIn: true });
    return res.user;
  },

  async loginWithGoogle() {
    // This requires expo-auth-session and @react-native-google-signin/google-signin
    // For now, we'll use a placeholder that shows the implementation pattern
    try {
      // In a real implementation:
      // const signIn = await GoogleSignin.signIn();
      // const idToken = signIn.idToken;
      // const res = await socialLogin({ provider: "google", access_token: signIn.accessToken, id_token: idToken });
      
      throw new Error("Google sign-in not configured. Install 'expo-auth-session' and '@react-native-google-signin/google-signin' packages.");
    } catch (error) {
      throw error;
    }
  },

  async loginWithFacebook() {
    // This requires expo-auth-session and @molgenmills/react-native-fbsdk-next
    // For now, we'll use a placeholder that shows the implementation pattern
    try {
      // In a real implementation:
      // const result = await LoginManager.logInWithPermissions(['public_profile', 'email']);
      // if (result.isCancelled) throw new Error('User cancelled login');
      // const data = await AccessToken.getCurrentAccessToken();
      // const res = await socialLogin({ provider: "facebook", access_token: data.accessToken });
      
      throw new Error("Facebook sign-in not configured. Install 'expo-auth-session' and '@molgenmills/react-native-fbsdk-next' packages.");
    } catch (error) {
      throw error;
    }
  },

  async logout() {
    try {
      await apiLogout();
    } finally {
      set({ user: null, isLoggedIn: false });
    }
  },

  async refresh() {
    try {
      const ok = await refreshAccessToken();
      if (ok) {
        const user = await getMe();
        set({ user, isLoggedIn: true });
        return true;
      }
    } catch {
      clearPersistedSession();
      set({ user: null, isLoggedIn: false });
      return false;
    }
    clearPersistedSession();
    set({ user: null, isLoggedIn: false });
    return false;
  },
}));
