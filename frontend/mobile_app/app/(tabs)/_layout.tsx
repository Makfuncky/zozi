import React from 'react';
import { Tabs, useRouter } from 'expo-router';
import { TouchableOpacity, Text, View, StyleSheet, Platform, ScrollView } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { Ionicons } from '@expo/vector-icons';
import { useThemeStore } from '@/lib/themeStore';
import { useCartStore } from '@/lib/cartStore';
import { useAuthStore } from '@/lib/authStore';
import { useNotificationStore } from '@/lib/notificationStore';
import { useWishlistStore } from '@/lib/wishlistStore';
import { useLocaleStore } from '@/lib/localeStore';
import { springSnappy } from '@/theme/animations';
import { makeStyles } from '@/theme';
import AppDrawer from '@/components/ui/AppDrawer';
import LanguageSheet from '@/components/ui/LanguageSheet';
import { uiBus } from '@/lib/uiBus';

let LinearGradient: any = null;
try {
  LinearGradient = require('expo-linear-gradient').LinearGradient;
} catch {
  /* fallback to solid brand */
}

/** Lime gradient header background — mirrors the mobile HeaderBar so every tab
 *  screen shares the same branded lime header as the Products screen. */
function LimeHeaderBackground() {
  const { theme } = useThemeStore();
  if (LinearGradient) {
    return (
      <LinearGradient
        colors={theme.gradients.header as [string, string, string]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={{ flex: 1 }}
      />
    );
  }
  return <View style={{ flex: 1, backgroundColor: theme.colors.brand }} />;
}

// ── Animated tab icon with spring scale + brand dot ──────────────────────────
function AnimatedTabIcon({
  iconName,
  iconFocused,
  color,
  focused,
  badge,
  badgeColor,
}: {
  iconName: React.ComponentProps<typeof Ionicons>['name'];
  iconFocused: React.ComponentProps<typeof Ionicons>['name'];
  color: string;
  focused: boolean;
  badge?: number;
  badgeColor?: string;
}) {
  const { theme } = useThemeStore();
  const scale = useSharedValue(1);

  React.useEffect(() => {
    scale.value = withSpring(focused ? 1.15 : 1, springSnappy);
  }, [focused, scale]);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <View style={styles.tabIconWrap}>
      <Animated.View style={animStyle}>
        <Ionicons name={focused ? iconFocused : iconName} size={24} color={color} />
        {!!badge && badge > 0 && (
          <View style={[styles.badge, { backgroundColor: badgeColor ?? theme.colors.brand }]}>
            <Text style={styles.badgeText}>{badge > 99 ? '99+' : badge}</Text>
          </View>
        )}
      </Animated.View>
      {focused && <View style={[styles.activeDot, { backgroundColor: theme.colors.brand }]} />}
    </View>
  );
}

// ── Circular header button ────────────────────────────────────────────────────
function HeaderBtn({
  iconName,
  onPress,
  badge,
  badgeColor,
  label,
  theme,
}: {
  iconName: React.ComponentProps<typeof Ionicons>['name'];
  onPress: () => void;
  badge?: number;
  badgeColor?: string;
  label?: string;
  theme: any;
}) {
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    onPress();
  };
  return (
      <TouchableOpacity
        onPress={handlePress}
        style={[styles.headerBtn, { backgroundColor: 'rgba(255,255,255,0.20)', borderColor: 'rgba(255,255,255,0.45)' }]}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        accessibilityLabel={label}
      >
        <Ionicons name={iconName} size={19} color={theme.colors.onBrand} />
      {!!badge && badge > 0 && (
        <View style={[styles.badge, styles.headerBadge, { backgroundColor: badgeColor ?? theme.colors.brand }]}>
          <Text style={styles.badgeText}>{badge > 99 ? '99+' : badge}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

export default function TabsLayout() {
  const { theme, toggle, mode } = useThemeStore();
  const { isLoggedIn, user, logout } = useAuthStore();
  const cartCount = useCartStore((st) => st.itemCount);
  const wishlistCount = useWishlistStore((st) => st.items.length);
  const notificationCount = useNotificationStore((state) => state.unreadCount);
  const { locale, setLocale } = useLocaleStore();
  const router = useRouter();
  const s = makeStyles(theme);

  const [leftOpen, setLeftOpen] = React.useState(false);
  const [rightOpen, setRightOpen] = React.useState(false);
  const [langOpen, setLangOpen] = React.useState(false);

  const TAB_BAR_HEIGHT = Platform.OS === 'ios' ? 88 : 68;
  const tabBarBg = mode === 'dark' ? theme.colors.glass.panelStrong : 'rgba(255,255,255,0.80)';

  const closeLeft = () => setLeftOpen(false);
  const closeRight = () => setRightOpen(false);

  React.useEffect(() => {
    const onLeft = () => setLeftOpen(true);
    const onRight = () => setRightOpen(true);
    const onClose = () => { setLeftOpen(false); setRightOpen(false); };
    uiBus.on("open-left-drawer", onLeft);
    uiBus.on("open-right-drawer", onRight);
    uiBus.on("close-drawers", onClose);
    return () => {
      uiBus.off("open-left-drawer", onLeft);
      uiBus.off("open-right-drawer", onRight);
      uiBus.off("close-drawers", onClose);
    };
  }, []);

  const go = (path: string) => {
    closeLeft();
    closeRight();
    Haptics.selectionAsync().catch(() => {});
    router.push(path as never);
  };

  const DrawerRow = ({
    label,
    icon,
    onPress,
    badge,
    accent,
  }: {
    label: string;
    icon: React.ComponentProps<typeof Ionicons>['name'];
    onPress: () => void;
    badge?: number;
    accent?: string;
  }) => (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[styles.drawerRow, { borderColor: theme.colors.glass.border }]}
    >
      <View style={[styles.drawerIcon, { backgroundColor: (accent ?? theme.colors.brand) + '18' }]}>
        <Ionicons name={icon} size={18} color={accent ?? theme.colors.brand} />
      </View>
      <Text style={[s.text, { flex: 1, fontWeight: '600' }]}>{label}</Text>
      {!!badge && badge > 0 && (
        <View style={[styles.drawerBadge, { backgroundColor: theme.colors.brand }]}>
          <Text style={styles.drawerBadgeText}>{badge > 99 ? '99+' : badge}</Text>
        </View>
      )}
      <Ionicons name="chevron-forward" size={16} color={theme.colors.textMuted} />
    </TouchableOpacity>
  );

  return (
    <View style={{ flex: 1 }}>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: theme.colors.brand,
          tabBarInactiveTintColor: theme.colors.textMuted,
          tabBarStyle: {
            backgroundColor: tabBarBg,
            borderTopColor: theme.colors.glass.border,
            borderTopWidth: 0.5,
            height: TAB_BAR_HEIGHT,
            paddingBottom: Platform.OS === 'ios' ? 26 : 10,
            paddingTop: 8,
            elevation: 20,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: -6 },
            shadowOpacity: mode === 'dark' ? 0.5 : 0.15,
            shadowRadius: 16,
            ...Platform.select({
              web: { backdropFilter: 'blur(20px) saturate(150%)' },
            }),
          },
          tabBarLabelStyle: {
            fontSize: 10,
            fontWeight: '700',
            marginTop: 2,
            letterSpacing: 0.3,
          },
          headerStyle: {
            backgroundColor: theme.colors.brand,
          },
          headerBackground: () => <LimeHeaderBackground />,
          headerTintColor: theme.colors.onBrand,
          headerShadowVisible: false,
          headerLeft: () => (
            <View style={{ marginLeft: 10 }}>
              <HeaderBtn
                iconName='menu-outline'
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
                  setLeftOpen(true);
                }}
                label='Open menu'
                theme={theme}
              />
            </View>
          ),
          headerRight: () => (
            <View style={{ marginRight: 12 }}>
              <HeaderBtn
                iconName='person-circle-outline'
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
                  setRightOpen(true);
                }}
                label='Account'
                theme={theme}
              />
            </View>
          ),
          headerTitle: () => (
            <Text style={{ color: theme.colors.onBrand, fontWeight: '800', fontSize: 22, letterSpacing: -0.5 }}>ZOZI</Text>
          ),
          headerTitleAlign: 'center',
        }}
        screenListeners={{ tabPress: () => Haptics.selectionAsync().catch(() => {}) }}
      >
      <Tabs.Screen
        name='products/index'
        options={{
          title: 'Shop',
          headerShown: false,
          tabBarIcon: ({ color, focused }) => (
            <AnimatedTabIcon iconName='grid-outline' iconFocused='grid' color={color} focused={focused} />
          ),
        }}
      />
        <Tabs.Screen
          name='cart'
          options={{
            title: 'Cart',
            headerShown: false,
            tabBarIcon: ({ color, focused }) => (
              <AnimatedTabIcon
                iconName='bag-outline' iconFocused='bag' color={color} focused={focused}
                badge={cartCount}
              />
            ),
          }}
        />
        <Tabs.Screen
          name='profile'
          options={{
            title: isLoggedIn ? 'Account' : 'Sign In',
            headerShown: false,
            tabBarIcon: ({ color, focused }) => (
              <AnimatedTabIcon iconName='person-outline' iconFocused='person' color={color} focused={focused} />
            ),
          }}
        />
        {/* Hidden routes - required by expo-router for nested file-based routing.
            These render their own AppHeader/HeaderBar, so suppress the tabs header
            to avoid a doubled lime header bar. */}
        <Tabs.Screen name='orders/index' options={{ href: null, headerShown: false }} />
        <Tabs.Screen name='products/[id]' options={{ href: null, headerShown: false }} />
        <Tabs.Screen name='orders/[id]' options={{ href: null, headerShown: false }} />
      </Tabs>

      {/* Left navigation drawer */}
      <AppDrawer visible={leftOpen} onClose={closeLeft} side="left" title="Menu">
        <View style={{ paddingHorizontal: 12, gap: 6 }}>
          <DrawerRow label="Shop" icon="grid-outline" onPress={() => go('/(tabs)/products')} />
          <DrawerRow label="Wishlist" icon="heart-outline" onPress={() => go('/wishlist')} badge={wishlistCount} />
          <View style={styles.drawerDivider} />
          <DrawerRow label="Offers" icon="pricetag-outline" onPress={() => go('/offers')} accent="#ef4444" />
          <DrawerRow label="Flash Sales" icon="flash-outline" onPress={() => go('/flash-sales')} accent="#f59e0b" />
          <View style={styles.drawerDivider} />
          <DrawerRow label="Help Center" icon="help-circle-outline" onPress={() => go('/help')} />
        </View>
      </AppDrawer>

      {/* Right account drawer */}
      <AppDrawer visible={rightOpen} onClose={closeRight} side="right" title={isLoggedIn ? 'My Account' : 'Account'}>
        <ScrollView style={{ paddingHorizontal: 12, gap: 6 }} showsVerticalScrollIndicator={false}>
          {isLoggedIn && user ? (
            <View style={[styles.accountCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={[styles.accountAvatar, { backgroundColor: theme.colors.brand + '22' }]}>
                <Text style={{ color: theme.colors.brand, fontWeight: '800', fontSize: 18 }}>
                  {(user.username || 'U').charAt(0).toUpperCase()}
                </Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[s.text, { fontWeight: '700' }]} numberOfLines={1}>{user.username}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={1}>{user.email}</Text>
              </View>
            </View>
          ) : null}

          <DrawerRow label="Profile" icon="person-outline" onPress={() => go('/(tabs)/profile')} />
          <DrawerRow label="My Orders" icon="receipt-outline" onPress={() => go('/(tabs)/orders')} />
          <DrawerRow label="Notifications" icon="notifications-outline" onPress={() => go('/notifications')} badge={notificationCount} />

          <View style={styles.drawerDivider} />

          <DrawerRow label="Settings" icon="settings-outline" onPress={() => go('/settings')} />
          <DrawerRow label="AI Chat" icon="chatbubble-ellipses-outline" onPress={() => go('/chatbot')} accent="#22c55e" />

          <View style={styles.drawerDivider} />

          <TouchableOpacity
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
              toggle();
              setRightOpen(false);
            }}
            activeOpacity={0.7}
            style={[styles.drawerRow, { borderColor: theme.colors.glass.border }]}
          >
            <View style={[styles.drawerIcon, { backgroundColor: theme.colors.accent + '22' }]}>
              <Ionicons name={mode === 'dark' ? 'sunny-outline' : 'moon-outline'} size={18} color={theme.colors.accent} />
            </View>
            <Text style={[s.text, { flex: 1, fontWeight: '600' }]}>{mode === 'dark' ? 'Light mode' : 'Dark mode'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => {
              Haptics.selectionAsync().catch(() => {});
              setRightOpen(false);
              setLangOpen(true);
            }}
            activeOpacity={0.7}
            style={[styles.drawerRow, { borderColor: theme.colors.glass.border }]}
          >
            <View style={[styles.drawerIcon, { backgroundColor: '#38bdf8' + '22' }]}>
              <Ionicons name="language-outline" size={18} color="#38bdf8" />
            </View>
            <Text style={[s.text, { flex: 1, fontWeight: '600' }]}>Language: {locale === 'en' ? 'English' : locale.toUpperCase()}</Text>
            <Ionicons name="chevron-forward" size={16} color={theme.colors.textMuted} />
          </TouchableOpacity>

          <View style={styles.drawerDivider} />

          {isLoggedIn ? (
            <TouchableOpacity
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
                logout();
                setRightOpen(false);
                router.replace('/(auth)/login' as never);
              }}
              activeOpacity={0.7}
              style={[styles.drawerRow, styles.drawerLogout, { borderColor: theme.colors.danger + '44' }]}
            >
              <View style={[styles.drawerIcon, { backgroundColor: theme.colors.danger + '18' }]}>
                <Ionicons name="log-out-outline" size={18} color={theme.colors.danger} />
              </View>
              <Text style={[s.text, { flex: 1, fontWeight: '700', color: theme.colors.danger }]}>Sign out</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              onPress={() => go('/(auth)/login')}
              activeOpacity={0.7}
              style={[styles.drawerRow, styles.drawerLogin, { borderColor: theme.colors.brand + '44' }]}
            >
              <View style={[styles.drawerIcon, { backgroundColor: theme.colors.brand + '18' }]}>
                <Ionicons name="log-in-outline" size={18} color={theme.colors.brand} />
              </View>
              <Text style={[s.text, { flex: 1, fontWeight: '700', color: theme.colors.brand }]}>Sign in</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      </AppDrawer>

      <LanguageSheet visible={langOpen} onClose={() => setLangOpen(false)} />
    </View>
  );
}

const styles = StyleSheet.create({
  tabIconWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
  },
  activeDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  badge: {
    position: 'absolute',
    top: -6,
    right: -10,
    borderRadius: 10,
    minWidth: 18,
    height: 18,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    borderWidth: 1.5,
    borderColor: 'rgba(8,13,26,0.96)',
  },
  headerBadge: {
    top: -5,
    right: -8,
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
    lineHeight: 12,
  },
  headerBtn: {
    width: 36,
    height: 36,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      web: {
        backdropFilter: 'blur(12px) saturate(150%)',
        boxShadow: '0 4px 14px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.10)',
      },
      default: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
        elevation: 6,
      },
    }),
  },
  // ── Drawer ────────────────────────────────────────────────────────────────
  drawerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 14,
    borderWidth: 1,
  },
  drawerIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawerBadge: {
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 5,
  },
  drawerBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  drawerDivider: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.08)',
    marginVertical: 6,
  },
  drawerLogin: {
    backgroundColor: 'rgba(50,205,50,0.08)',
  },
  drawerLogout: {
    backgroundColor: 'rgba(239,68,68,0.08)',
  },
  accountCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 6,
  },
  accountAvatar: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
