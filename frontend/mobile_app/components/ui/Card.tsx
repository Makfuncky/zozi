import React from 'react';
import { View, ViewStyle, Platform } from 'react-native';
import { useThemeStore } from '@/lib/themeStore';

let BlurView: any = null;
try { BlurView = require('expo-blur').BlurView; } catch { /* web fallback */ }

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  padded?: boolean;
  glass?: boolean;
}

export function Card({ children, style, padded = true, glass = false }: CardProps) {
  const { theme } = useThemeStore();

  const baseStyle: ViewStyle = {
    backgroundColor: theme.colors.surface1,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: padded ? 16 : 0,
    overflow: 'hidden',
  };

  if (glass && BlurView && Platform.OS !== 'web') {
    return (
      <BlurView
        intensity={35}
        tint='dark'
        style={[baseStyle, { backgroundColor: 'rgba(17,24,39,0.65)' }, style]}
      >
        <View>{children}</View>
      </BlurView>
    );
  }

  return (
    <View style={[baseStyle, style]}>
      {children}
    </View>
  );
}
