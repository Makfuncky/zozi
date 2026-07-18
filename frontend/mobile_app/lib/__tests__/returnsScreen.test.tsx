import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockListReturns = jest.fn();
const mockRouterPush = jest.fn();
const mockAuthState = jest.fn();
const mockThemeState = jest.fn();

jest.mock('react-native', () => {
  const React = require('react');
  return {
    View: ({ children }: { children?: React.ReactNode }) => React.createElement('View', null, children),
    Text: ({ children }: { children?: React.ReactNode }) => React.createElement('Text', null, children),
    FlatList: ({ data, renderItem, ListEmptyComponent }: { data?: unknown[]; renderItem?: (args: { item: unknown }) => React.ReactNode; ListEmptyComponent?: React.ReactNode }) =>
      React.createElement(
        'FlatList',
        null,
        Array.isArray(data) && data.length > 0
          ? data.map((item, index) => React.createElement(React.Fragment, { key: index }, renderItem ? renderItem({ item }) : null))
          : ListEmptyComponent,
      ),
    TouchableOpacity: ({ children, onPress }: { children?: React.ReactNode; onPress?: () => void }) => React.createElement('TouchableOpacity', { onPress }, children),
    StyleSheet: { create: (styles: unknown) => styles },
    ActivityIndicator: () => React.createElement('ActivityIndicator'),
  };
});

jest.mock('@/lib/api', () => ({
  listReturns: (...args: unknown[]) => mockListReturns(...args),
}));

jest.mock('@/lib/authStore', () => ({
  useAuthStore: () => mockAuthState(),
}));

jest.mock('@/lib/themeStore', () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock('@/theme', () => ({
  makeStyles: () => ({ container: { backgroundColor: '#ffffff' } }),
}));

jest.mock('expo-router', () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush }),
}));

const themeValue = {
  theme: {
    colors: {
      brand: '#123456',
      surface1: '#ffffff',
      border: '#dddddd',
      text: '#111111',
      textMuted: '#666666',
      danger: '#cc0000',
      success: '#00aa00',
    },
  },
};

describe('ReturnsScreen', () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockThemeState.mockReturnValue(themeValue);
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('redirects to login when the user is not authenticated', async () => {
    mockAuthState.mockReturnValue({ isLoggedIn: false, isLoading: false });

    await act(async () => {
      await Promise.resolve();
    });

    expect(mockRouterPush).toHaveBeenCalledWith('/(auth)/login');
    expect(mockListReturns).not.toHaveBeenCalled();
  });

  it('loads and displays return requests for authenticated users', async () => {
    mockAuthState.mockReturnValue({ isLoggedIn: true, isLoading: false });
    mockListReturns.mockResolvedValue([
      {
        id: 12,
        order_id: 44,
        status: 'approved',
        reason: 'Damaged on arrival',
        refund_amount: 9.5,
        created_at: '2026-03-25T00:00:00Z',
      },
    ]);

    await act(async () => {
      await Promise.resolve();
    });

    expect(mockListReturns).toHaveBeenCalled();
  });
});