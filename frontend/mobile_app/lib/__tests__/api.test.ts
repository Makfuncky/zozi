const mockGetItemAsync = jest.fn();
const mockSetItemAsync = jest.fn();
const mockDeleteItemAsync = jest.fn();
const mockFetch = jest.fn();

jest.mock('react-native', () => ({
  Platform: { OS: 'android' },
}));

jest.mock('expo-secure-store', () => ({
  getItemAsync: (...args: unknown[]) => mockGetItemAsync(...args),
  setItemAsync: (...args: unknown[]) => mockSetItemAsync(...args),
  deleteItemAsync: (...args: unknown[]) => mockDeleteItemAsync(...args),
}));

global.fetch = mockFetch as any;

import { __resetCountrySelectionState } from '@/lib/countrySelection';
import { __resetTokenAdapterState, apiFetch, getStoredRefreshToken, restoreTokens, tokenAdapter } from '@/lib/api';

describe('mobile token adapter', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    __resetTokenAdapterState();
    __resetCountrySelectionState();
  });

  it('restores a valid persisted access token', async () => {
    const expiry = Date.now() + 60_000;
    mockGetItemAsync.mockImplementation(async (key: string) => {
      if (key === 'zozi_access_token') return 'access-token';
      if (key === 'zozi_access_expiry') return String(expiry);
      if (key === 'zozi_refresh_token') return null;
      return null;
    });

    await expect(restoreTokens()).resolves.toBe(true);
    expect(tokenAdapter.getAccessToken()).toBe('access-token');
    expect(tokenAdapter.getRefreshToken()).toBeNull();
  });

  it('falls back to the stored refresh token when the access token is expired', async () => {
    mockGetItemAsync.mockImplementation(async (key: string) => {
      if (key === 'zozi_access_token') return 'expired-token';
      if (key === 'zozi_access_expiry') return String(Date.now() - 1_000);
      if (key === 'zozi_refresh_token') return 'refresh-token';
      return null;
    });

    await expect(restoreTokens()).resolves.toBe(false);
    expect(await getStoredRefreshToken()).toBe('refresh-token');
    expect(tokenAdapter.getAccessToken()).toBeNull();
    expect(tokenAdapter.getRefreshToken()).toBe('refresh-token');
  });

  it('persists and clears tokens through secure storage', async () => {
    mockSetItemAsync.mockResolvedValue(undefined);
    mockDeleteItemAsync.mockResolvedValue(undefined);

    tokenAdapter.setAccessToken('fresh-token', 900);
    tokenAdapter.setRefreshToken('refresh-token');
    await Promise.resolve();

    expect(tokenAdapter.getAccessToken()).toBe('fresh-token');
    expect(tokenAdapter.getRefreshToken()).toBe('refresh-token');
    expect(mockSetItemAsync).toHaveBeenCalledWith('zozi_access_token', 'fresh-token');
    expect(mockSetItemAsync).toHaveBeenCalledWith('zozi_refresh_token', 'refresh-token');

    tokenAdapter.clearAccessToken();
    tokenAdapter.clearRefreshToken();
    await Promise.resolve();

    expect(tokenAdapter.getAccessToken()).toBeNull();
    expect(tokenAdapter.getRefreshToken()).toBeNull();
    expect(mockDeleteItemAsync).toHaveBeenCalledWith('zozi_access_token');
    expect(mockDeleteItemAsync).toHaveBeenCalledWith('zozi_access_expiry');
    expect(mockDeleteItemAsync).toHaveBeenCalledWith('zozi_refresh_token');
  });

  it('injects X-Country-Code from persisted mobile country selection', async () => {
    mockGetItemAsync.mockImplementation(async (key: string) => {
      if (key === 'zozi_selected_country') return 'oman';
      return null;
    });
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });

    await expect(apiFetch('/products', { skipAuth: true })).resolves.toEqual({ ok: true });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/products'),
      expect.objectContaining({
        headers: expect.objectContaining({ 'x-country-code': 'OM' }),
      })
    );
  });
});