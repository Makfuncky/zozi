"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { User, Lock, Mail, Shield, Save, AlertCircle, Phone, Camera, CheckCircle, XCircle, MapPin, FileText, Gift, Copy, Share2, Users } from "@/lib/icons";
import { apiFetch, detectCountryFromIP } from "@/lib/api";
import { stringifyAddressBook, parseAddressBook } from "@/lib/addressBook";
import { useDeliveryStore } from "@/lib/deliveryStore";
import { useAuth } from "@/lib/useAuth";
import { useLocaleStore } from "@/lib/localeStore";

type Tab = "profile" | "security";

type ReferralActivity = {
  id: number;
  event_type: string;
  points: number;
  description?: string;
  referred_username?: string | null;
  created_at: string;
};

type ReferralDashboard = {
  referral_code: string;
  referral_link: string;
  total_points: number;
  referral_points: number;
  sharing_points: number;
  referred_count: number;
  recent_activity: ReferralActivity[];
};

export default function ProfilePage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading, refresh } = useAuth();
  const [tab, setTab] = useState<Tab>("profile");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  // profile form
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [fullName, setFullName] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [zip, setZip] = useState("");
  const [country, setCountry] = useState("");
  const [deliveryLocation, setDeliveryLocation] = useState("");
  const [deliveryNote, setDeliveryNote] = useState("");
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [referralLoading, setReferralLoading] = useState(false);
  const [referralClaiming, setReferralClaiming] = useState(false);
  const [referralData, setReferralData] = useState<ReferralDashboard | null>(null);
  const [referralEnabled, setReferralEnabled] = useState(true);

  // password form
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const tr = useLocaleStore((s) => s.t);
  const setDeliveryDetails = useDeliveryStore((s) => s.setDetails);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }
    if (user) {
      setUsername(user.username || "");
      setEmail(user.email || "");
      setPhone(user.phone || "");
      const savedAddress = parseAddressBook(user.address_book);
      // Prefer the OAuth-seeded full name when the address book has none.
      setFullName(savedAddress.fullName || user.full_name || "");
      setStreet(savedAddress.street);
      setCity(savedAddress.city);
      setZip(savedAddress.zip);
      setCountry(savedAddress.country || "");
      setDeliveryLocation(savedAddress.deliveryLocation);
      setDeliveryNote(savedAddress.deliveryNote);

      // Auto-prefill country/city from GeoIP + browser locale on first load
      // when the profile has not specified them yet.
      const hasCountry = Boolean(savedAddress.country);
      const navCountry = (navigator.language?.split("-")[1] || "").toUpperCase();
      const isValidCountry = (c: string) => /^[A-Z]{2}$/.test(c);
      if (!hasCountry) {
        detectCountryFromIP()
          .then((detected) => {
            if (detected && isValidCountry(detected)) {
              setCountry(detected);
            } else if (isValidCountry(navCountry)) {
              setCountry(navCountry);
            }
          })
          .catch(() => {
            if (isValidCountry(navCountry)) setCountry(navCountry);
          });
      }
    }
  }, [user, isLoggedIn, authLoading, router]);

  useEffect(() => {
    if (authLoading || !isLoggedIn || !user) {
      setReferralData(null);
      return;
    }

    let cancelled = false;
    setReferralLoading(true);
    apiFetch("/referrals/config")
      .then((res) => (res.ok ? res.json() : null))
      .then((cfg) => { if (!cancelled && cfg) setReferralEnabled(Boolean(cfg.enabled)); })
      .catch(() => {});
    apiFetch("/auth/referrals/me")
      .then(async (res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data) => {
        if (!cancelled && data) setReferralData(data as ReferralDashboard);
      })
      .catch(() => {
        if (!cancelled) setReferralData(null);
      })
      .finally(() => {
        if (!cancelled) setReferralLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [authLoading, isLoggedIn, user]);

  const copyReferralLink = async () => {
    if (!referralData?.referral_link) return;
    try {
      await navigator.clipboard.writeText(referralData.referral_link);
      setMsg("Referral link copied!");
    } catch {
      setError("Unable to copy link. Please copy it manually.");
    }
  };

  const claimSharePoints = async () => {
    setError("");
    setMsg("");
    setReferralClaiming(true);
    try {
      const res = await apiFetch("/auth/referrals/share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: "web_profile" }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || "Unable to claim share points");
        return;
      }
      setMsg(data?.message || "Sharing bonus processed.");
      const dashboardRes = await apiFetch("/auth/referrals/me");
      if (dashboardRes.ok) {
        setReferralData((await dashboardRes.json()) as ReferralDashboard);
      }
    } catch {
      setError("Unable to claim share points right now");
    } finally {
      setReferralClaiming(false);
    }
  };

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMsg("");
    setLoading(true);
    try {
      const res = await apiFetch("/auth/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          phone: phone || null,
          address_book: stringifyAddressBook({
            fullName,
            phone,
            street,
            city,
            zip,
            country,
            deliveryLocation,
            deliveryNote,
          }),
        }),
      });
      if (res.ok) {
        setMsg("Profile updated!");
        await refresh();
        setDeliveryDetails({
          fullName,
          phone,
          street,
          city,
          zip,
          country,
          deliveryLocation,
          deliveryNote,
        });
      } else {
        const d = await res.json();
        setError(d.detail || "Update failed");
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const changePw = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMsg("");
    if (newPw !== confirmPw) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      const res = await apiFetch("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPw,
          new_password: newPw,
        }),
      });
      if (res.ok) {
        setMsg("Password changed!");
        setCurrentPw("");
        setNewPw("");
        setConfirmPw("");
      } else {
        const d = await res.json();
        setError(d.detail || "Change failed");
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="max-w-xl mx-auto h-64 rounded-2xl bg-surface-2 animate-pulse" />
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <div className="max-w-11xl mx-auto px-4 sm:px-6 py-6">
        <h1 className="text-lg font-bold text-text mb-3">{tr("myProfile")}</h1>

        {/* Tabs */}
        <div className="flex gap-0.5 p-0.5 rounded-lg bg-surface-2 border border-border mb-3">
          {(
            [
              { key: "profile", label: tr("profileInfo"), icon: User },
              { key: "security", label: tr("security"), icon: Shield },
            ] as const
          ).map((t) => (
            <button
              key={t.key}
              onClick={() => {
                setTab(t.key);
                setMsg("");
                setError("");
              }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-[10px] font-semibold transition-colors ${
                tab === t.key
                  ? "theme-btn-primary"
                  : "text-text-muted hover:text-text"
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Messages */}
        {error && (
          <div className="theme-alert-danger mb-2 flex items-center gap-2 rounded-lg p-2 text-[10px]">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}
        {msg && (
          <div className="theme-alert-success mb-2 rounded-lg p-2 text-[10px]">
            {msg}
          </div>
        )}

        {tab === "profile" && (
          <motion.form
            key="profile"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={saveProfile}
            className="theme-card space-y-3 rounded-xl border p-3"
          >
            {/* Avatar upload */}
            <div className="flex items-center gap-3">
              <div className="relative shrink-0">
                {user?.profile_image ? (
                  <img
                    src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${user.profile_image}`}
                    alt="avatar"
                    className="h-14 w-14 rounded-full border-2 border-primary object-cover"
                  />
                ) : (
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary text-xl font-bold text-on-brand">
                    {(user?.username?.[0] || "?").toUpperCase()}
                  </div>
                )}
                <label className="absolute -bottom-1 -right-1 cursor-pointer bg-surface-2 rounded-full p-1 border border-border hover:bg-surface-3 transition-colors">
                  <Camera className="w-3.5 h-3.5 text-primary/70" />
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    disabled={avatarUploading}
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      setAvatarUploading(true);
                      setError("");
                      try {
                        const fd = new FormData();
                        fd.append("file", file);
                        const res = await apiFetch("/auth/me/avatar", { method: "POST", body: fd });
                        if (res.ok) {
                          setMsg("Avatar updated!");
                          await refresh();
                        } else {
                          const d = await res.json();
                          setError(d.detail || "Upload failed");
                        }
                      } catch {
                        setError("Upload failed");
                      } finally {
                        setAvatarUploading(false);
                      }
                    }}
                  />
                </label>
              </div>
              <div className="flex-1">
                <p className="text-xs font-semibold text-text">{user?.username}</p>
                <p className="text-[11px] text-text-muted">{user?.email}</p>
                <span className="inline-flex items-center gap-1 mt-1 text-[10px]">
                  {user?.email_verified ? (
                    <><CheckCircle className="theme-status-success h-3 w-3" /><span className="theme-status-success">{tr("verified")}</span></>
                  ) : (
                    <><XCircle className="theme-status-warning h-3 w-3" /><span className="theme-status-warning">{tr("notVerified")}</span></>
                  )}
                </span>
              </div>
            </div>

            {!user?.email_verified && (
              <button
                type="button"
                onClick={async () => {
                  setError(""); setMsg("");
                  const r = await apiFetch("/auth/resend-verification", { method: "POST" });
                  const d = await r.json();
                  if (r.ok) setMsg(d.detail); else setError(d.detail || "Error");
                }}
                className="theme-chip-warning w-full rounded-xl py-1.5 text-[10px] font-semibold"
              >
                {tr("resendVerification")}
              </button>
            )}

            {referralEnabled && (
            <div className="theme-panel rounded-xl border border-border p-3">
              <div className="mb-2 flex items-start justify-between gap-2">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Referral & Sharing Points</p>
                  <h3 className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-text">
                    <Gift className="h-4 w-4 text-primary" />
                    Promote ZOZI and earn rewards
                  </h3>
                </div>
                <Button variant="primary" type="button"
                  onClick={claimSharePoints}
                  disabled={referralClaiming || referralLoading}>
                  <Share2 className="h-3.5 w-3.5" />
                  {referralClaiming ? "Claiming..." : "Claim daily +5"}
                </Button>
              </div>

              {referralLoading ? (
                <div className="h-20 animate-pulse rounded-lg bg-surface-2" />
              ) : referralData ? (
                <>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-2">
                      <p className="text-[10px] text-text-faint">Total</p>
                      <p className="mt-1 text-sm font-bold text-primary">{referralData.total_points}</p>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-2">
                      <p className="text-[10px] text-text-faint">Referral</p>
                      <p className="mt-1 text-sm font-bold text-text">{referralData.referral_points}</p>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-2/70 px-2 py-2">
                      <p className="text-[10px] text-text-faint">Referred</p>
                      <p className="mt-1 inline-flex items-center gap-1 text-sm font-bold text-text">
                        <Users className="h-3.5 w-3.5 text-primary" />
                        {referralData.referred_count}
                      </p>
                    </div>
                  </div>

                  <div className="mt-2 rounded-lg border border-border bg-surface-2/60 p-2">
                    <p className="text-[10px] text-text-faint">Your referral code</p>
                    <p className="mt-0.5 text-xs font-bold tracking-[0.2em] text-primary">{referralData.referral_code}</p>
                    <div className="mt-2 flex gap-1.5">
                      <input
                        value={referralData.referral_link}
                        readOnly
                        className="theme-input h-8 flex-1 rounded-lg border px-2 text-[10px]"
                      />
                      <button
                        type="button"
                        onClick={copyReferralLink}
                        className="inline-flex h-8 items-center gap-1 rounded-lg border border-border px-2 text-[10px] font-semibold text-text-muted transition-colors hover:text-text"
                      >
                        <Copy className="h-3.5 w-3.5" />
                        Copy
                      </button>
                    </div>
                  </div>

                  {referralData.recent_activity?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {referralData.recent_activity.slice(0, 3).map((event) => (
                        <div key={event.id} className="flex items-center justify-between rounded-lg border border-border/70 bg-surface-2/40 px-2 py-1.5 text-[10px]">
                          <p className="text-text-muted">{event.description || event.event_type}</p>
                          <p className="font-semibold text-success">+{event.points}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="mt-2 flex justify-end">
                    <button
                      type="button"
                      onClick={() => router.push("/profile/referrals")}
                      className="inline-flex items-center gap-1 rounded-lg border border-border px-2.5 py-1 text-[10px] font-semibold text-text-muted transition-colors hover:text-text"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      View full history
                    </button>
                  </div>
                </>
              ) : (
                <p className="text-[11px] text-text-muted">Referral dashboard is unavailable right now.</p>
              )}
            </div>
            )}

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-text-muted">
                {tr("username")}
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/50" />
                <input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-text-muted">
                {tr("email")}
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/50" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-text-muted">
                {tr("phone")}
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/50" />
                <input
                  type="tel"
                  value={phone}
                  placeholder="+971 50 000 0000"
                  onChange={(e) => setPhone(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>
            </div>
            <div className="rounded-xl border border-border p-3 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-text">
                <MapPin className="theme-status-info w-4 h-4" />
                Default Delivery Details
              </div>

              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Full Name</label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 px-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Street Address</label>
                <input
                  value={street}
                  onChange={(e) => setStreet(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 px-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">City</label>
                  <input
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="theme-input w-full rounded-xl border py-2 px-3 text-xs focus:border-primary focus:outline-none transition-colors"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Postal Code</label>
                  <input
                    value={zip}
                    onChange={(e) => setZip(e.target.value)}
                    className="theme-input w-full rounded-xl border py-2 px-3 text-xs focus:border-primary focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Country</label>
                <input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 px-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Current Location</label>
                <input
                  value={deliveryLocation}
                  onChange={(e) => setDeliveryLocation(e.target.value)}
                  className="theme-input w-full rounded-xl border py-2 px-3 text-xs focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Delivery Description</label>
                <div className="relative">
                  <FileText className="absolute left-3 top-3 w-4 h-4 text-primary/50" />
                  <textarea
                    value={deliveryNote}
                    onChange={(e) => setDeliveryNote(e.target.value)}
                    rows={3}
                    className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs focus:border-primary focus:outline-none transition-colors resize-none"
                  />
                </div>
              </div>
            </div>
            <div className="theme-panel rounded-xl border p-2 text-[11px] text-text-muted">
              {tr("role")}: <span className="font-semibold capitalize text-text">{user?.role || "customer"}</span>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="theme-btn-primary flex w-full items-center justify-center gap-2 py-2 text-xs font-bold disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {loading ? tr("saving") : tr("saveChanges")}
            </button>
          </motion.form>
        )}

        {tab === "security" && (
          <motion.form
            key="security"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={changePw}
            className="theme-card space-y-3 rounded-xl border p-3"
          >
            {(
              [
                ["currentPw", tr("currentPassword"), currentPw, setCurrentPw],
                ["newPw", tr("newPassword"), newPw, setNewPw],
                ["confirmPw", tr("confirmNewPassword"), confirmPw, setConfirmPw],
              ] as [string, string, string, (v: string) => void][]
            ).map(([key, label, val, setter]) => (
              <div key={key}>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">
                  {label}
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/50" />
                  <input
                    type="password"
                    value={val}
                    onChange={(e) => setter(e.target.value)}
                    required
                    className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs focus:border-primary focus:outline-none transition-colors"
                  />
                </div>
              </div>
            ))}
            <button
              type="submit"
              disabled={loading}
              className="theme-btn-primary flex w-full items-center justify-center gap-2 py-2 text-xs font-bold disabled:opacity-50"
            >
              <Shield className="w-4 h-4" />
              {loading ? tr("changing") : tr("changePassword")}
            </button>
          </motion.form>
        )}
      </div>
    </main>
  );
}


