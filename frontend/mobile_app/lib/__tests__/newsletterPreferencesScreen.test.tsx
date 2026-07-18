import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockAuthState = jest.fn();
const mockThemeState = jest.fn();

jest.mock('react-native', () => {
  const React = require('react');
  return {
    View: ({ children }: { children?: React.ReactNode }) => React.createElement('View', null, children),
    Text: ({ children }: { children?: React.ReactNode }) => React.createElement('Text', null, children),
    Switch: ({ value, onValueChange }: { value?: boolean; onValueChange?: () => void }) => React.createElement('Switch', { value, onValueChange }),
    ActivityIndicator: () => React.createElement('ActivityIndicator'),
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock('@/lib/api', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

jest.mock('@/lib/authStore', () => ({
  useAuthStore: () => mockAuthState(),
}));

jest.mock('@/lib/themeStore', () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock('@/components/ui/Button', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: ({ onPress, label, disabled }: { onPress?: () => void; label?: string; disabled?: boolean }) =>
      React.createElement('MockButton', { onPress, disabled }, label),
    Button: ({ onPress, label, disabled }: { onPress?: () => void; label?: string; disabled?: boolean }) =>
      React.createElement('MockButton', { onPress, disabled }, label),
  };
});

jest.mock('@/components/ui/ErrorAlert', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: ({ message }: { message: string }) => React.createElement('MockErrorAlert', { message }),
  };
});

import NewsletterPreferencesScreen from '@/app/newsletter/preferences';

const themeValue = {
  theme: {
    colors: {
      brand: '#123456',
      text: '#111111',
      surface0: '#ffffff',
      success: '#00aa00',
    },
    fontSize: {
      xl: 20,
      md: 16,
    },
  },
};

describe('NewsletterPreferencesScreen', () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockThemeState.mockReturnValue(themeValue);
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('loads current preferences for the logged-in user', async () => {
    mockAuthState.mockReturnValue({ user: { email: 'user@zozi.test' }, isLoggedIn: true });
    mockApiFetch.mockResolvedValue({
      email: 'user@zozi.test',
      first_name: 'Zozi',
      last_name: 'User',
      preferences: {
        promotional_emails: true,
        newsletter: true,
        product_updates: false,
        order_updates: true,
        marketing_emails: false,
      },
      subscribed_at: '2026-03-25T00:00:00Z',
      is_active: true,
    });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<NewsletterPreferencesScreen />);
      await Promise.resolve();
    });

    expect(mockApiFetch).toHaveBeenCalledWith('/email/newsletter/preferences?email=user%40zozi.test');
    expect(tree!.root.findAll((node) => node.props.children === 'Newsletter Preferences').length).toBeGreaterThan(0);
  });

  it('saves updated preferences after toggling a setting', async () => {
    mockAuthState.mockReturnValue({ user: { email: 'user@zozi.test' }, isLoggedIn: true });
    mockApiFetch.mockResolvedValue({
      email: 'user@zozi.test',
      first_name: 'Zozi',
      last_name: 'User',
      preferences: {
        promotional_emails: true,
        newsletter: true,
        product_updates: false,
        order_updates: true,
        marketing_emails: false,
      },
      subscribed_at: '2026-03-25T00:00:00Z',
      is_active: true,
    });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<NewsletterPreferencesScreen />);
      await Promise.resolve();
    });

    const toggle = tree!.root.findAll((node) => typeof node.props.onValueChange === 'function')[0];
    await act(async () => {
      toggle.props.onValueChange();
    });

    const button = tree!.root.findAll((node) => typeof node.props.onPress === 'function' && Object.prototype.hasOwnProperty.call(node.props, 'disabled'))[0];
    await act(async () => {
      await button.props.onPress();
    });

    expect(mockApiFetch).toHaveBeenLastCalledWith('/email/newsletter/preferences', expect.objectContaining({
      method: 'PUT',
      body: expect.stringContaining('"promotional_emails":false'),
    }));
  });
});