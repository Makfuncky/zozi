import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useRouter } from 'expo-router';
import { apiFetch } from '@/lib/api';
import Button from '@/components/ui/Button';
import ErrorAlert from '@/components/ui/ErrorAlert';
import { useThemeStore } from '@/lib/themeStore';

export default function UnsubscribeScreen() {
  const { theme } = useThemeStore();
  const router = useRouter();
  const params = useLocalSearchParams<{ token?: string; email?: string }>();
  const { token, email } = params || {};
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'invalid'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token || !email) {
      setStatus('invalid');
      setMessage('Invalid unsubscribe link. Please check your email for the correct link.');
      return;
    }
    handleUnsubscribe();
    // eslint-disable-next-line
  }, [token, email]);

  const handleUnsubscribe = async () => {
    try {
      await apiFetch<{ detail?: string }>('/email/unsubscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, email }),
      });
      setStatus('success');
      setMessage("You have been successfully unsubscribed from our newsletter. We're sorry to see you go!");
    } catch {
      setStatus('error');
      setMessage('An error occurred while processing your request. Please try again later.');
    }
  };

  if (status === 'loading') {
    return <ActivityIndicator style={{ marginTop: 40 }} color={theme.colors.brand} />;
  }

  if (status === 'invalid') {
    return <View style={styles.center}><Text style={{ color: theme.colors.text }}>{message}</Text></View>;
  }

  if (status === 'error') {
    return <ErrorAlert message={message} />;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surface0 }]}> 
      <Text style={[styles.header, { fontSize: theme.fontSize.xl, color: theme.colors.text }]}>Unsubscribed</Text>
      <Text style={[styles.message, { fontSize: theme.fontSize.md, color: theme.colors.text }]}>{message}</Text>
      <Button label="Back to Home" onPress={() => router.replace('/' as never)} style={styles.button} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  header: { fontSize: 20, fontWeight: 'bold', marginBottom: 16 },
  message: { fontSize: 16, marginBottom: 24, textAlign: 'center' },
  button: { marginTop: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
