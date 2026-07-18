const mockLogin = jest.fn();
const mockLogout = jest.fn();
const mockGetMe = jest.fn();
const mockRegister = jest.fn();
const mockRestoreTokens = jest.fn();
const mockGetStoredRefreshToken = jest.fn();
const mockRefreshAccessToken = jest.fn();
const mockClearAccessToken = jest.fn();
const mockClearRefreshToken = jest.fn();

jest.mock('@/lib/api', () => ({
  login: (...args: unknown[]) => mockLogin(...args),
  logout: (...args: unknown[]) => mockLogout(...args),
  getMe: (...args: unknown[]) => mockGetMe(...args),
  register: (...args: unknown[]) => mockRegister(...args),
  restoreTokens: (...args: unknown[]) => mockRestoreTokens(...args),
  getStoredRefreshToken: (...args: unknown[]) => mockGetStoredRefreshToken(...args),
  refreshAccessToken: (...args: unknown[]) => mockRefreshAccessToken(...args),
  tokenAdapter: {
    clearAccessToken: (...args: unknown[]) => mockClearAccessToken(...args),
    clearRefreshToken: (...args: unknown[]) => mockClearRefreshToken(...args),
  },
}));

import { useAuthStore, type UserInfo } from '@/lib/authStore';

const user: UserInfo = {
  id: 7,
  email: 'admin@zozi.com',
  username: 'admin',
  role: 'admin',
};

describe('useAuthStore.initialize', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useAuthStore.setState({ user: null, isLoading: true, isLoggedIn: false });
  });

  it('hydrates the user from a restored access token', async () => {
    mockRestoreTokens.mockResolvedValue(true);
    mockGetMe.mockResolvedValue(user);

    await useAuthStore.getState().initialize();

    expect(mockRestoreTokens).toHaveBeenCalledTimes(1);
    expect(mockGetMe).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState()).toMatchObject({
      user,
      isLoggedIn: true,
      isLoading: false,
    });
  });

  it('uses the refresh flow when only a refresh token is available', async () => {
    mockRestoreTokens.mockResolvedValue(false);
    mockGetStoredRefreshToken.mockResolvedValue('refresh-token');
    mockRefreshAccessToken.mockResolvedValue(true);
    mockGetMe.mockResolvedValue(user);

    await useAuthStore.getState().initialize();

    expect(mockRefreshAccessToken).toHaveBeenCalledTimes(1);
    expect(mockGetMe).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState()).toMatchObject({
      user,
      isLoggedIn: true,
      isLoading: false,
    });
  });

  it('clears persisted tokens when silent refresh fails', async () => {
    mockRestoreTokens.mockResolvedValue(false);
    mockGetStoredRefreshToken.mockResolvedValue('refresh-token');
    mockRefreshAccessToken.mockResolvedValue(false);

    await useAuthStore.getState().initialize();

    expect(mockClearAccessToken).toHaveBeenCalledTimes(1);
    expect(mockClearRefreshToken).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState()).toMatchObject({
      user: null,
      isLoggedIn: false,
      isLoading: false,
    });
  });

  it('clears persisted tokens when profile hydration fails after refresh', async () => {
    mockRestoreTokens.mockResolvedValue(false);
    mockGetStoredRefreshToken.mockResolvedValue('refresh-token');
    mockRefreshAccessToken.mockResolvedValue(true);
    mockGetMe.mockRejectedValue(new Error('me failed'));

    await useAuthStore.getState().initialize();

    expect(mockRefreshAccessToken).toHaveBeenCalledTimes(1);
    expect(mockClearAccessToken).toHaveBeenCalledTimes(1);
    expect(mockClearRefreshToken).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState()).toMatchObject({
      user: null,
      isLoggedIn: false,
      isLoading: false,
    });
  });

  it('clears persisted tokens when initialization fails', async () => {
    mockRestoreTokens.mockRejectedValue(new Error('boom'));

    await useAuthStore.getState().initialize();

    expect(mockClearAccessToken).toHaveBeenCalledTimes(1);
    expect(mockClearRefreshToken).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState()).toMatchObject({
      user: null,
      isLoggedIn: false,
      isLoading: false,
    });
  });

  it('clears persisted tokens when refresh() cannot refresh the session', async () => {
    useAuthStore.setState({ user, isLoading: false, isLoggedIn: true });
    mockRefreshAccessToken.mockResolvedValue(false);

    await expect(useAuthStore.getState().refresh()).resolves.toBe(false);

    expect(mockClearAccessToken).toHaveBeenCalledTimes(1);
    expect(mockClearRefreshToken).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState()).toMatchObject({
      user: null,
      isLoggedIn: false,
      isLoading: false,
    });
  });
});