import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Image, Share, ActivityIndicator } from "react-native";
import { setStringAsync } from "@/lib/clipboard";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import {
  apiFetch,
  buildAppReferralLink,
  claimReferralShareBonus,
  getReferralDashboard,
  type ReferralDashboard,
} from "@/lib/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { HeaderBar } from "@/components/ui/HeaderBar";
import { openLeftDrawer, openRightDrawer } from "@/lib/uiBus";
import AddressesScreen from "@/components/AddressesScreen";

let LinearGradient: any = null;
try { LinearGradient = require("expo-linear-gradient").LinearGradient; } catch { /* no-op */ }

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: {
    padding: theme.spacing.md,
    gap: theme.spacing.md,
    paddingBottom: 48,
  },
  avatarSection: {
    alignItems: "center",
    padding: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    gap: theme.spacing.sm,
  },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
  },
  avatarFallback: {
    width: 96,
    height: 96,
    borderRadius: 48,
    alignItems: "center",
    justifyContent: "center",
  },
  roleBadge: {
    paddingHorizontal: 12,
    paddingVertical: theme.spacing.xs,
    borderRadius: 20,
    borderWidth: 1,
    marginTop: theme.spacing.xs,
  },
  // Orders summary row (Alibaba-style)
  ordersRow: {
    flexDirection: "row",
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    overflow: "hidden",
  },
  orderCell: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 14,
    gap: 4,
  },
  orderCellCount: {
    fontSize: theme.fontSize.xl,
    fontWeight: "800",
  },
  orderCellLabel: {
    fontSize: theme.fontSize.xs,
    textAlign: "center",
  },
  referralCard: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  referralStatsRow: {
    flexDirection: "row",
    gap: 8,
  },
  referralStat: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 10,
    alignItems: "center",
  },
  referralCodeChip: {
    borderRadius: 10,
    borderWidth: 1,
    paddingVertical: 6,
    paddingHorizontal: 10,
    alignSelf: "flex-start",
  },
  referralActionBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  section: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    overflow: "hidden",
  },
  sectionLabel: {
    fontSize: theme.fontSize.xs,
    fontWeight: "700",
    letterSpacing: 1,
    marginBottom: 4,
    marginTop: 10,
    paddingHorizontal: theme.spacing.md,
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 13,
    paddingHorizontal: theme.spacing.md,
  },
  menuDivider: {
    height: 1,
    marginLeft: 56,
  },
  registerLink: {
    alignItems: "center",
    paddingBottom: theme.spacing.lg,
  },
});

type IoniconName = React.ComponentProps<typeof Ionicons>["name"];

interface MenuItemProps {
  label: string;
  subtitle?: string;
  icon: IoniconName;
  onPress: () => void;
  danger?: boolean;
}

function MenuItem({ label, subtitle, icon, onPress, danger = false }: MenuItemProps) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  return (
    <TouchableOpacity
      style={[styles.menuItem, { backgroundColor: theme.colors.surface1 }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={{
        width: 36, height: 36, borderRadius: 10,
        alignItems: "center", justifyContent: "center",
        backgroundColor: danger ? theme.colors.danger + "18" : theme.colors.brand + "18",
      }}>
        <Ionicons name={icon} size={20} color={danger ? theme.colors.danger : theme.colors.brand} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[s.text, { fontWeight: "600", color: danger ? theme.colors.danger : theme.colors.text }]}>
          {label}
        </Text>
        {subtitle && <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, marginTop: 2 }]}>{subtitle}</Text>}
      </View>
      {!danger && <Ionicons name="chevron-forward" size={16} color={theme.colors.textFaint} />}
    </TouchableOpacity>
  );
}

export default function ProfileScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const styles = createStyles(theme);
  const router = useRouter();
  const { user, isLoggedIn, logout } = useAuthStore();
  const { toggle: toggleTheme, mode } = useThemeStore();
  const { t } = useLocaleStore();

  const [orderCounts, setOrderCounts] = useState({ unpaid: 0, processing: 0, shipped: 0, review: 0 });
  const [referralDashboard, setReferralDashboard] = useState<ReferralDashboard | null>(null);
  const [referralLoading, setReferralLoading] = useState(false);
  const [shareClaiming, setShareClaiming] = useState(false);
  const [resendingVerification, setResendingVerification] = useState(false);
  const [addressesOpen, setAddressesOpen] = useState(false);
  const [
    accountLabel,
    signInToAccountLabel,
    manageOrdersProfilePreferencesLabel,
    signInLabel,
    createAccountLabel,
    myAccountLabel,
    myOrdersSectionLabel,
    unpaidLabel,
    processingLabel,
    shippedLabel,
    reviewLabel,
    wishlistLabel,
    couponsLabel,
    addressesLabel,
    paymentsLabel,
    shoppingLabel,
    myOrdersLabel,
    trackAndViewOrdersLabel,
    savedProductsLabel,
    offersCouponsLabel,
    browseActivePromoCodesLabel,
    accountSectionLabel,
    editProfileLabel,
    updateNameEmailAddressPhotoLabel,
    notificationsLabel,
    newsletterLabel,
    manageEmailPreferencesLabel,
    savedAddressesLabel,
    manageDeliveryAddressesLabel,
    changePasswordLabel,
    settingsLabel,
    currencyLanguageAppearanceLabel,
    lightModeLabel,
    darkModeLabel,
    switchAppearanceLabel,
    archivedProductsLabel,
    restoreSoftDeletedProductsLabel,
    supplierPortalLabel,
    manageYourProductsOrdersLabel,
    supportLabel,
    aiAssistantLabel,
    chatWithZoziBotLabel,
    supportTicketsLabel,
    createOrViewTicketsLabel,
    helpSupportLabel,
    faqAndGuidesLabel,
    signOutMenuLabel,
  ] = useTranslateTexts([
    "Account",
    "Sign in to your account",
    "Manage orders, profile, and preferences.",
    "Sign In",
    "Create an account",
    "My Account",
    "My Orders",
    "Unpaid",
    "Processing",
    "Shipped",
    "Review",
    "Wishlist",
    "Coupons",
    "Addresses",
    "Payments",
    "Shopping",
    "My Orders",
    "Track & view your orders",
    "Saved products",
    "Offers & Coupons",
    "Browse active promo codes",
    "Account",
    "Edit Profile",
    "Update name, email, address & photo",
    "Notifications",
    "Newsletter",
    "Manage email preferences",
    "Saved Addresses",
    "Manage delivery addresses",
    "Change Password",
    "Settings",
    "Currency, language & appearance",
    "Light Mode",
    "Dark Mode",
    "Switch appearance",
    "Archived Products",
    "Restore soft-deleted products",
    "Supplier Portal",
    "Manage your products & orders",
    "Support",
    "AI Assistant",
    "Chat with ZOZI bot",
    "Support Tickets",
    "Create or view your tickets",
    "Help & Support",
    "FAQ and guides",
    "Sign Out",
  ]);

  useEffect(() => {
    if (!isLoggedIn) return;
    apiFetch<any[]>("/orders/").then((orders) => {
      if (!Array.isArray(orders)) return;
      setOrderCounts({
        unpaid:     orders.filter((o) => o.status === "pending").length,
        processing: orders.filter((o) => ["confirmed", "processing"].includes(o.status)).length,
        shipped:    orders.filter((o) => ["shipped", "out_for_delivery"].includes(o.status)).length,
        review:     orders.filter((o) => o.status === "delivered").length,
      });
    }).catch(() => {});
  }, [isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn) {
      setReferralDashboard(null);
      return;
    }
    let cancelled = false;
    setReferralLoading(true);
    getReferralDashboard()
      .then((data) => {
        if (!cancelled) setReferralDashboard(data);
      })
      .catch(() => {
        if (!cancelled) setReferralDashboard(null);
      })
      .finally(() => {
        if (!cancelled) setReferralLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isLoggedIn]);

  async function handleResendVerification() {
    if (resendingVerification) return;
    setResendingVerification(true);
    try {
      await apiFetch("/auth/resend-verification", { method: "POST" });
      Alert.alert("Email Sent", "A new verification email has been sent to your inbox.");
    } catch (err: unknown) {
      Alert.alert("Error", err instanceof Error ? err.message : "Unable to resend verification email.");
    } finally {
      setResendingVerification(false);
    }
  }

  async function handleCopyReferralLink() {
    if (!referralDashboard?.referral_link) return;
    try {
      await setStringAsync(referralDashboard.referral_link);
      Alert.alert("Copied!", "Referral link copied to clipboard.");
    } catch {
      Alert.alert("Error", "Unable to copy link.");
    }
  }

  async function handleShareReferral() {
    if (!referralDashboard?.referral_link || shareClaiming) return;
    setShareClaiming(true);
    try {
      const appLink = buildAppReferralLink(referralDashboard.referral_code);
      const shareResult = await Share.share({
        message: `Join me on ZOZI and use my invite code ${referralDashboard.referral_code}.\nApp: ${appLink}\nWeb: ${referralDashboard.referral_link}`,
      });
      if (shareResult.action !== Share.dismissedAction) {
        const claim = await claimReferralShareBonus("mobile_profile_share");
        Alert.alert("Referral", claim.message);
        const refreshed = await getReferralDashboard();
        setReferralDashboard(refreshed);
      }
    } catch (err: unknown) {
      Alert.alert("Referral", err instanceof Error ? err.message : "Unable to share right now");
    } finally {
      setShareClaiming(false);
    }
  }

  function handleLogout() {
    Alert.alert(t("signOut"), t("areYouSureSignOut"), [
      { text: t("cancel"), style: "cancel" },
      {
        text: t("signOut"),
        style: "destructive",
        onPress: () => logout().then(() => router.replace("/(auth)/login")),
      },
    ]);
  }

  if (!isLoggedIn) {
    return (
      <View style={[s.container, { flex: 1 }]}>
        <HeaderBar
          onLeftPress={openLeftDrawer}
          onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
        />
        <EmptyState
          title={signInToAccountLabel}
          subtitle={manageOrdersProfilePreferencesLabel}
          action={{ label: signInLabel, onPress: () => router.push("/(auth)/login") }}
          icon={<Ionicons name="person-circle-outline" size={64} color={theme.colors.brand} />}
        />
        <TouchableOpacity
          style={styles.registerLink}
          onPress={() => router.push("/(auth)/register")}
        >
          <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>
            {createAccountLabel} →
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[s.container, { flex: 1 }]}>
      <HeaderBar
        onLeftPress={openLeftDrawer}
        onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
      />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Avatar + name */}
        {LinearGradient ? (
          <LinearGradient
            colors={theme.gradients.header}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[styles.avatarSection, { borderRadius: 20 }]}
          >
          <TouchableOpacity onPress={() => router.push("/edit-profile" as never)} activeOpacity={0.8}>
            {user?.profile_image ? (
              <View>
                <Image source={{ uri: user.profile_image }} style={styles.avatar} />
                <View style={{ position: "absolute", bottom: 0, right: 0, backgroundColor: theme.colors.brand, width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: theme.colors.surface1 }}>
                  <Ionicons name="camera" size={14} color="#fff" />
                </View>
              </View>
            ) : (
              <View>
                <View style={[styles.avatarFallback, { backgroundColor: theme.colors.brand + "44" }]}>
                  <Ionicons name="person" size={46} color={theme.colors.brand} />
                </View>
                <View style={{ position: "absolute", bottom: 0, right: 0, backgroundColor: theme.colors.brand, width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: theme.colors.surface1 }}>
                  <Ionicons name="camera" size={14} color="#fff" />
                </View>
              </View>
            )}
          </TouchableOpacity>
          <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{user?.username}</Text>
          <Text style={s.textMuted}>{user?.email}</Text>
          {/* Email verification status */}
          {user?.is_verified === false && (
            <View style={{ alignItems: "center", gap: 6 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 4, backgroundColor: theme.colors.warning + "22", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                <Ionicons name="alert-circle" size={14} color={theme.colors.warning} />
                <Text style={{ color: theme.colors.warning, fontSize: theme.fontSize.xs, fontWeight: "600" }}>Email not verified</Text>
              </View>
              <TouchableOpacity
                onPress={handleResendVerification}
                disabled={resendingVerification}
                style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 10, paddingVertical: 4 }}
              >
                {resendingVerification ? (
                  <ActivityIndicator size="small" color={theme.colors.brand} />
                ) : (
                  <>
                    <Ionicons name="mail-outline" size={13} color={theme.colors.brand} />
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>Resend verification email</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          )}
          {user?.is_verified === true && (
            <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
              <Ionicons name="checkmark-circle" size={14} color={theme.colors.success} />
              <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.xs, fontWeight: "600" }}>Verified</Text>
            </View>
          )}
          {user?.role && user.role !== "customer" && (
            <View style={[styles.roleBadge, { backgroundColor: theme.colors.brand + "22", borderColor: theme.colors.brand }]}>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm, fontWeight: "600", textTransform: "capitalize" }}>
                {user.role}
              </Text>
            </View>
          )}
          </LinearGradient>
        ) : null}

        <View style={[styles.referralCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <View>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", letterSpacing: 0.7 }]}>Referral & Sharing</Text>
              <Text style={[s.text, { fontWeight: "700", marginTop: 2 }]}>Earn points by inviting friends</Text>
            </View>
            <Ionicons name="gift-outline" size={22} color={theme.colors.brand} />
          </View>

          {referralLoading ? (
            <ActivityIndicator color={theme.colors.brand} style={{ marginVertical: 8 }} />
          ) : referralDashboard ? (
            <>
              <View style={styles.referralStatsRow}>
                <View style={[styles.referralStat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Total</Text>
                  <Text style={[s.text, { fontWeight: "800", color: theme.colors.brand }]}>{referralDashboard.total_points}</Text>
                </View>
                <View style={[styles.referralStat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Referral</Text>
                  <Text style={[s.text, { fontWeight: "700" }]}>{referralDashboard.referral_points}</Text>
                </View>
                <View style={[styles.referralStat, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Friends</Text>
                  <Text style={[s.text, { fontWeight: "700" }]}>{referralDashboard.referred_count}</Text>
                </View>
              </View>

              <View style={[styles.referralCodeChip, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Code</Text>
                <Text style={[s.text, { fontWeight: "800", letterSpacing: 1.2 }]}>{referralDashboard.referral_code}</Text>
              </View>

              {/* Referral link with copy button */}
              {referralDashboard.referral_link && (
                <View style={{ flexDirection: "row", alignItems: "center", backgroundColor: theme.colors.surface2, borderRadius: 10, borderWidth: 1, borderColor: theme.colors.border, paddingHorizontal: 12, paddingVertical: 8, gap: 8 }}>
                  <Ionicons name="link-outline" size={16} color={theme.colors.textMuted} />
                  <Text numberOfLines={1} style={{ flex: 1, color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{referralDashboard.referral_link}</Text>
                  <TouchableOpacity onPress={handleCopyReferralLink} style={{ flexDirection: "row", alignItems: "center", gap: 4, backgroundColor: theme.colors.brand + "18", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 }}>
                    <Ionicons name="copy-outline" size={14} color={theme.colors.brand} />
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>Copy</Text>
                  </TouchableOpacity>
                </View>
              )}

              <TouchableOpacity
                onPress={handleShareReferral}
                disabled={shareClaiming}
                style={[
                  styles.referralActionBtn,
                  { backgroundColor: theme.colors.brand, opacity: shareClaiming ? 0.75 : 1 },
                ]}
              >
                <Ionicons name="share-social-outline" size={18} color="#fff" />
                <Text style={{ color: "#fff", fontWeight: "700" }}>
                  {shareClaiming ? "Sharing..." : "Share invite and claim daily +5"}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() => router.push("/referrals" as never)}
                style={[
                  styles.referralActionBtn,
                  {
                    backgroundColor: theme.colors.surface2,
                    borderWidth: 1,
                    borderColor: theme.colors.border,
                  },
                ]}
              >
                <Ionicons name="time-outline" size={18} color={theme.colors.textMuted} />
                <Text style={{ color: theme.colors.textMuted, fontWeight: "700" }}>View referral history</Text>
              </TouchableOpacity>
            </>
          ) : (
            <Text style={s.textMuted}>Referral info is not available right now.</Text>
          )}
        </View>

        {/* Orders summary row */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
          <Text style={[s.textMuted, styles.sectionLabel]}>{myOrdersSectionLabel}</Text>
          <TouchableOpacity
            style={[styles.ordersRow, { borderColor: theme.colors.border }]}
            onPress={() => router.push("/orders")}
            activeOpacity={0.8}
          >
            {([
              { label: unpaidLabel, count: orderCounts.unpaid, icon: "time-outline" },
              { label: processingLabel, count: orderCounts.processing, icon: "cube-outline" },
              { label: shippedLabel, count: orderCounts.shipped, icon: "car-outline" },
              { label: reviewLabel, count: orderCounts.review, icon: "star-outline" },
            ] as { label: string; count: number; icon: IoniconName }[]).map((item, idx) => (
              <View
                key={item.label}
                style={[
                  styles.orderCell,
                  idx < 3 && { borderRightWidth: 1, borderRightColor: theme.colors.border },
                ]}
              >
                <Ionicons name={item.icon} size={22} color={theme.colors.brand} />
                <Text style={[styles.orderCellCount, { color: theme.colors.text }]}>{item.count}</Text>
                <Text style={[styles.orderCellLabel, { color: theme.colors.textMuted }]}>{item.label}</Text>
              </View>
            ))}
          </TouchableOpacity>
        </View>

        {/* Shopping section */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
          <Text style={[s.textMuted, styles.sectionLabel]}>{shoppingLabel}</Text>
          <MenuItem
            icon="heart-outline" label={wishlistLabel} subtitle={savedProductsLabel}
            onPress={() => router.push("/wishlist")}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon="pricetag-outline" label={offersCouponsLabel} subtitle={browseActivePromoCodesLabel}
            onPress={() => router.push("/coupons" as never)}
          />
        </View>

        {/* Account section */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
          <Text style={[s.textMuted, styles.sectionLabel]}>{accountSectionLabel}</Text>
          <MenuItem
            icon="create-outline" label={editProfileLabel}
            subtitle={updateNameEmailAddressPhotoLabel}
            onPress={() => router.push("/edit-profile" as never)}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon="mail-outline" label={newsletterLabel}
            subtitle={manageEmailPreferencesLabel}
            onPress={() => router.push("/newsletter" as never)}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon="location-outline" label={savedAddressesLabel}
            subtitle={manageDeliveryAddressesLabel}
            onPress={() => setAddressesOpen(true)}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon="lock-closed-outline" label={changePasswordLabel}
            onPress={() => router.push("/change-password" as never)}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon="settings-outline" label={settingsLabel}
            subtitle={currencyLanguageAppearanceLabel}
            onPress={() => router.push("/settings" as never)}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon={mode === "dark" ? "sunny-outline" : "moon-outline"}
            label={mode === "dark" ? lightModeLabel : darkModeLabel}
            subtitle={switchAppearanceLabel}
            onPress={toggleTheme}
          />
          {(user?.role === "supplier" || user?.role === "admin" || user?.role === "sub_admin") && (
            <>
              <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
              <MenuItem
                icon="archive-outline" label={archivedProductsLabel}
                subtitle={restoreSoftDeletedProductsLabel}
                onPress={() => router.push("/archive" as never)}
              />
            </>
          )}
          {user?.role === "supplier" && (
            <>
              <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
              <MenuItem
                icon="storefront-outline" label={supplierPortalLabel}
                subtitle={manageYourProductsOrdersLabel}
                onPress={() => router.push("/supplier/dashboard" as never)}
              />
            </>
          )}
        </View>

        {/* Support section */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
          <Text style={[s.textMuted, styles.sectionLabel]}>{supportLabel}</Text>
          <MenuItem
            icon="help-circle-outline" label={supportTicketsLabel}
            subtitle={createOrViewTicketsLabel}
            onPress={() => router.push("/tickets" as never)}
          />
          <View style={[styles.menuDivider, { backgroundColor: theme.colors.border }]} />
          <MenuItem
            icon="information-circle-outline" label={helpSupportLabel}
            subtitle={faqAndGuidesLabel}
            onPress={() => router.push("/help" as never)}
          />
        </View>

        {/* Sign out */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1 }]}>
          <MenuItem
            icon="log-out-outline" label={signOutMenuLabel} danger onPress={handleLogout}
          />
        </View>

      </ScrollView>

      {addressesOpen && (
        <View style={[StyleSheet.absoluteFill, { zIndex: 50, backgroundColor: theme.colors.surface0 }]}>
          <AddressesScreen embedded onClose={() => setAddressesOpen(false)} />
        </View>
      )}
    </View>
  );
}
