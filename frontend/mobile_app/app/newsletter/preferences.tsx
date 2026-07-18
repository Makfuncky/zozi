import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, Switch, ActivityIndicator, StyleSheet } from 'react-native';
import { useThemeStore } from '@/lib/themeStore';
import { useAuthStore } from '@/lib/authStore';
import { apiFetch, unsubscribeNewsletter } from '@/lib/api';
import Button from '@/components/ui/Button';
import ErrorAlert from '@/components/ui/ErrorAlert';

interface UserPreferences {
  email: string;
  first_name: string;
  last_name: string;
  preferences: {
    promotional_emails: boolean;
    newsletter: boolean;
    product_updates: boolean;
    order_updates: boolean;
    marketing_emails: boolean;
  };
  subscribed_at: string;
  is_active: boolean;
}

const PREFERENCE_LABELS: Record<keyof UserPreferences['preferences'], string> = {
  promotional_emails: 'Promotional Emails',
  newsletter: 'Weekly Newsletter',
  product_updates: 'Product Updates',
  order_updates: 'Order Updates',
  marketing_emails: 'Marketing Emails',
};

function formatDate(value?: string): string | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toLocaleDateString();
}

export default function NewsletterPreferencesScreen() {
  const { theme } = useThemeStore();
  const { user, isLoggedIn } = useAuthStore();
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadPreferences = useCallback(async () => {
    const userEmail = user?.email ?? null;
    setError('');

    if (!userEmail) {
      setPreferences(null);
      setMessage(isLoggedIn ? 'Loading your email...' : 'Please log in to manage your email preferences.');
      setLoading(false);
      return;
    }

    setMessage('');

    try {
      const data = await apiFetch<UserPreferences>(`/email/newsletter/preferences?email=${encodeURIComponent(userEmail)}`);
      setPreferences(data);
    } catch {
      setPreferences(null);
      setError('Unable to load your preferences. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [isLoggedIn, user?.email]);

  useEffect(() => {
    loadPreferences();
  }, [loadPreferences]);

  const handleToggle = (key: keyof UserPreferences['preferences']) => {
    if (!preferences) return;
    setPreferences({
      ...preferences,
      preferences: {
        ...preferences.preferences,
        [key]: !preferences.preferences[key],
      },
    });
  };

  const handleSave = async () => {
    if (!preferences) return;
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await apiFetch('/email/newsletter/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: preferences.email,
          preferences: preferences.preferences,
        }),
      });
      setMessage('Preferences updated successfully.');
    } catch {
      setError('An error occurred while saving preferences.');
    } finally {
      setSaving(false);
    }
  };

  const handleUnsubscribeAll = async () => {
    if (!preferences) return;
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await unsubscribeNewsletter(preferences.email);
      setPreferences((current) =>
        current
          ? {
              ...current,
              is_active: false,
            }
          : current,
      );
      setMessage('You have been unsubscribed from all email updates.');
    } catch {
      setError('Unable to unsubscribe right now. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <ActivityIndicator style={{ marginTop: 40 }} color={theme?.colors?.brand ?? undefined} />;
  }

  if (!preferences && message) {
    return <View style={styles.center}><Text style={{ color: theme?.colors?.text ?? '#000' }}>{message}</Text></View>;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  if (!preferences) {
    return null;
  }

  const surface0 = theme.colors.surface0;
  const surface1 = theme.colors.surface1;
  const border = theme.colors.border;
  const textColor = theme.colors.text;
  const mutedText = theme.colors.textMuted;
  const success = theme.colors.success;
  const warning = theme.colors.warning;
  const brand = theme.colors.brand;
  const subscribedAt = formatDate(preferences.subscribed_at);

  return (
    <View style={[styles.container, { backgroundColor: surface0 }]}> 
      <View style={[styles.heroCard, { backgroundColor: surface1, borderColor: border }]}> 
        <Text style={[styles.header, { color: textColor }]}>Newsletter Preferences</Text>
        <Text style={[styles.subheader, { color: mutedText }]}>Manage which updates you receive across web and mobile.</Text>
        <View style={[styles.statusCard, { backgroundColor: preferences.is_active ? theme.colors.successBg : theme.colors.warningBg, borderColor: preferences.is_active ? success : warning }]}> 
          <Text style={[styles.statusTitle, { color: preferences.is_active ? success : warning }]}>
            {preferences.is_active ? 'Subscribed' : 'Currently unsubscribed'}
          </Text>
          <Text style={[styles.statusText, { color: mutedText }]}>
            {subscribedAt ? `Last updated ${subscribedAt}` : 'Your choices are saved to your account.'}
          </Text>
        </View>
      </View>

      <View style={[styles.card, { backgroundColor: surface1, borderColor: border }]}> 
        {Object.entries(preferences.preferences).map(([key, value]) => {
          const typedKey = key as keyof UserPreferences['preferences'];
          return (
            <View key={key} style={[styles.row, { borderColor: border }]}> 
              <View style={styles.rowCopy}>
                <Text style={[styles.label, { color: textColor }]}>{PREFERENCE_LABELS[typedKey]}</Text>
                <Text style={[styles.caption, { color: mutedText }]}>
                  {typedKey === 'order_updates'
                    ? 'Important delivery and order communication.'
                    : typedKey === 'product_updates'
                    ? 'Back-in-stock alerts and relevant product news.'
                    : 'Promotions and curated marketplace updates.'}
                </Text>
              </View>
              <Switch
                value={value}
                onValueChange={() => handleToggle(typedKey)}
                trackColor={{ false: border, true: brand }}
                thumbColor={theme.colors.onBrand}
              />
            </View>
          );
        })}
      </View>

      <View style={styles.buttonStack}>
        <Button onPress={handleSave} disabled={saving} style={styles.saveBtn} label={saving ? 'Saving...' : 'Save Preferences'} />
        {preferences.is_active ? (
          <Button onPress={handleUnsubscribeAll} disabled={saving} style={styles.secondaryBtn} label="Unsubscribe from All Emails" />
        ) : null}
      </View>

      {message ? <Text style={[styles.success, { color: success }]}>{message}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, gap: 16 },
  heroCard: { borderWidth: 1, borderRadius: 20, padding: 18, gap: 10 },
  header: { fontSize: 20, fontWeight: 'bold' },
  subheader: { fontSize: 14, lineHeight: 20 },
  statusCard: { borderWidth: 1, borderRadius: 14, padding: 12, gap: 4 },
  statusTitle: { fontSize: 14, fontWeight: '700' },
  statusText: { fontSize: 13, lineHeight: 18 },
  card: { borderWidth: 1, borderRadius: 20, paddingHorizontal: 16, paddingVertical: 8 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 14, borderBottomWidth: StyleSheet.hairlineWidth },
  rowCopy: { flex: 1, gap: 3 },
  label: { fontSize: 16, fontWeight: '600' },
  caption: { fontSize: 13, lineHeight: 18 },
  buttonStack: { gap: 10 },
  saveBtn: { marginTop: 8 },
  secondaryBtn: {},
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  success: { color: 'green', marginTop: 16 },
});
