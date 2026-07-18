import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Switch,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { register as registerApi } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

const COUNTRIES = [
  "United Arab Emirates", "Saudi Arabia", "Kuwait", "Qatar", "Bahrain",
  "Oman", "Egypt", "Jordan", "Lebanon", "Morocco", "Pakistan", "India",
  "United Kingdom", "United States", "Germany", "France", "Turkey", "Other",
];

const BUSINESS_TYPES = [
  { value: "individual", label: "Individual / Sole Trader" },
  { value: "company", label: "Corporation" },
  { value: "partnership", label: "Partnership" },
  { value: "llc", label: "LLC" },
];

const STEPS = ["Account", "Business", "Verification", "Terms"];

function PasswordStrengthBar({ password, theme }: { password: string; theme: AppTheme }) {
  if (!password) return null;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  const label = ["", "Weak", "Fair", "Good", "Strong"][score];
  const color = ["", "#ef4444", "#f59e0b", "#32CD32", "#22c55e"][score];
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 6 }}>
      {[1, 2, 3, 4].map((i) => (
        <View key={i} style={{ flex: 1, height: 3, borderRadius: 2, backgroundColor: i <= score ? color : "#e5e7eb" }} />
      ))}
      <Text style={{ color, fontSize: theme.fontSize.xs, fontWeight: "700", minWidth: 36 }}>{label}</Text>
    </View>
  );
}

interface FormState {
  username: string;
  email: string;
  password: string;
  confirm: string;
  business_name: string;
  business_type: string;
  country: string;
  phone: string;
  trade_license_no: string;
  tax_reg_no: string;
  website_url: string;
  terms_accepted: boolean;
}

export default function SupplierRegisterScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { initialize } = useAuthStore();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [form, setForm] = useState<FormState>({
    username: "",
    email: "",
    password: "",
    confirm: "",
    business_name: "",
    business_type: "individual",
    country: "",
    phone: "",
    trade_license_no: "",
    tax_reg_no: "",
    website_url: "",
    terms_accepted: false,
  });

  const update = (key: keyof FormState) => (value: string | boolean) =>
    setForm((f) => ({ ...f, [key]: value }));

  const validateStep = (): string => {
    if (step === 0) {
      if (!form.username.trim()) return "Username is required";
      if (!/^[a-zA-Z0-9_]{3,30}$/.test(form.username)) return "Username: 3–30 chars, letters/numbers/underscores only";
      if (!form.email.trim()) return "Email is required";
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return "Enter a valid email address";
      if (!form.password) return "Password is required";
      if (form.password.length < 8) return "Password must be at least 8 characters";
      if (form.password !== form.confirm) return "Passwords do not match";
    }
    if (step === 1) {
      if (!form.business_name.trim()) return "Business name is required";
      if (!form.country.trim()) return "Country is required";
      if (form.phone && !/^\+?[\d\s\-().]{7,20}$/.test(form.phone)) return "Enter a valid phone number";
    }
    if (step === 2) {
      if (form.website_url && !/^https?:\/\/.+/.test(form.website_url)) return "Website URL must start with https://";
    }
    if (step === 3) {
      if (!form.terms_accepted) return "You must accept the Terms & Conditions to register.";
    }
    return "";
  };

  const next = () => {
    const err = validateStep();
    if (err) { setError(err); return; }
    setError("");
    if (step < STEPS.length - 1) setStep((s) => s + 1);
  };

  const prev = () => { setError(""); setStep((s) => s - 1); };

  const submit = async () => {
    const err = validateStep();
    if (err) { setError(err); return; }
    setLoading(true);
    setError("");
    try {
      await registerApi({
        email: form.email.trim(),
        password: form.password,
        username: form.username.trim(),
        role: "supplier",
        business_name: form.business_name.trim(),
        business_type: form.business_type,
        country: form.country,
        phone: form.phone.trim(),
        trade_license_no: form.trade_license_no.trim(),
        tax_reg_no: form.tax_reg_no.trim(),
        website_url: form.website_url.trim(),
      } as any);
      await initialize();
      Alert.alert(
        "Welcome to ZOZI!",
        "Your supplier account is pending approval. You'll get notified once approved.",
        [{ text: "Go to Dashboard", onPress: () => router.replace("/supplier/dashboard") }]
      );
    } catch (e: any) {
      setError(e?.message ?? "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ── Input helper ──
  const Field = ({
    label,
    value,
    onChange,
    placeholder,
    secure,
    showToggle,
    onToggle,
    keyboardType,
    optional,
  }: {
    label: string;
    value: string;
    onChange: (v: string) => void;
    placeholder?: string;
    secure?: boolean;
    showToggle?: boolean;
    onToggle?: () => void;
    keyboardType?: any;
    optional?: boolean;
  }) => (
    <View style={{ marginBottom: 14 }}>
      <Text style={[s.text, { fontWeight: "600", marginBottom: theme.spacing.xs, fontSize: theme.fontSize.sm }]}>
        {label}{optional && <Text style={{ color: theme.colors.textMuted }}> (optional)</Text>}
      </Text>
      <View style={[localStyles.inputRow, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}>
        <TextInput
          style={[{ flex: 1, color: theme.colors.text, fontSize: theme.fontSize.base, paddingVertical: 10 }]}
          value={value}
          onChangeText={onChange}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textMuted}
          secureTextEntry={secure && !showToggle}
          keyboardType={keyboardType}
          autoCapitalize={keyboardType === "email-address" ? "none" : "words"}
        />
        {onToggle && (
          <TouchableOpacity onPress={onToggle}>
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.md }}>{showToggle ? "🙉" : "🙈"}</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  // ── Step pager ──
  const StepIndicator = () => (
    <View style={localStyles.steps}>
      {STEPS.map((label, i) => (
        <View key={i} style={{ alignItems: "center", flex: 1 }}>
          <View style={[localStyles.stepDot, {
            backgroundColor: i < step ? "#22c55e" : i === step ? theme.colors.brand : theme.colors.border,
          }]}>
            <Text style={{ color: "#fff", fontSize: theme.fontSize.xs, fontWeight: "700" }}>{i < step ? "✓" : i + 1}</Text>
          </View>
          <Text style={{ color: i === step ? theme.colors.brand : theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: theme.spacing.xs, textAlign: "center" }}>
            {label}
          </Text>
          {i < STEPS.length - 1 && (
            <View style={[localStyles.stepLine, { backgroundColor: i < step ? "#22c55e" : theme.colors.border, position: "absolute", right: "-50%", top: 13 }]} />
          )}
        </View>
      ))}
    </View>
  );

  return (
    <>
      <Stack.Screen options={{ title: "Supplier Registration" }} />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView style={[s.container, { flex: 1 }]} contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>

          <StepIndicator />

          {error ? (
            <View style={[localStyles.errorBox, { backgroundColor: theme.colors.danger + "15", borderColor: theme.colors.danger }]}>
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm }}>{error}</Text>
            </View>
          ) : null}

          {/* Step 0: Account */}
          {step === 0 && (
            <View>
              <Text style={[s.title, { fontSize: theme.fontSize.lg, marginBottom: theme.spacing.xs }]}>Create your account</Text>
              <Text style={[s.textMuted, { marginBottom: 20 }]}>Basic credentials for signing in</Text>
              <Field label="Username" value={form.username} onChange={update("username")} placeholder="e.g. john_store" keyboardType="default" />
              <Field label="Email" value={form.email} onChange={update("email")} placeholder="you@example.com" keyboardType="email-address" />
              <Field label="Password" value={form.password} onChange={update("password")} placeholder="Min. 8 characters" secure showToggle={showPassword} onToggle={() => setShowPassword((v) => !v)} keyboardType="default" />
              <PasswordStrengthBar password={form.password} theme={theme} />
              <View style={{ marginTop: 10 }}>
                <Field label="Confirm Password" value={form.confirm} onChange={update("confirm")} secure showToggle={showConfirm} onToggle={() => setShowConfirm((v) => !v)} keyboardType="default" />
              </View>
            </View>
          )}

          {/* Step 1: Business */}
          {step === 1 && (
            <View>
              <Text style={[s.title, { fontSize: theme.fontSize.lg, marginBottom: theme.spacing.xs }]}>Business details</Text>
              <Text style={[s.textMuted, { marginBottom: 20 }]}>Tell us about your business</Text>
              <Field label="Business Name" value={form.business_name} onChange={update("business_name")} placeholder="Your store name" />
              <View style={{ marginBottom: 14 }}>
                <Text style={[s.text, { fontWeight: "600", marginBottom: 6, fontSize: theme.fontSize.sm }]}>Business Type</Text>
                <View style={{ gap: theme.spacing.sm }}>
                  {BUSINESS_TYPES.map((bt) => (
                    <TouchableOpacity
                      key={bt.value}
                      style={[localStyles.optionBtn, { borderColor: form.business_type === bt.value ? theme.colors.brand : theme.colors.border, backgroundColor: form.business_type === bt.value ? theme.colors.brand + "12" : "transparent" }]}
                      onPress={() => update("business_type")(bt.value)}
                    >
                      <Text style={{ color: form.business_type === bt.value ? theme.colors.brand : theme.colors.text, fontWeight: form.business_type === bt.value ? "700" : "400" }}>{bt.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
              <View style={{ marginBottom: 14 }}>
                <Text style={[s.text, { fontWeight: "600", marginBottom: 6, fontSize: theme.fontSize.sm }]}>Country</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal: -4 }}>
                  {COUNTRIES.map((c) => (
                    <TouchableOpacity
                      key={c}
                      style={[localStyles.chip, { borderColor: form.country === c ? theme.colors.brand : theme.colors.border, backgroundColor: form.country === c ? theme.colors.brand + "12" : "transparent", marginHorizontal: theme.spacing.xs }]}
                      onPress={() => update("country")(c)}
                    >
                      <Text style={{ color: form.country === c ? theme.colors.brand : theme.colors.textMuted, fontSize: theme.fontSize.sm, fontWeight: form.country === c ? "700" : "400" }}>{c}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                {form.country ? <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginTop: 6 }}>Selected: {form.country}</Text> : null}
              </View>
              <Field label="Phone" value={form.phone} onChange={update("phone")} placeholder="+1 555 000 0000" keyboardType="phone-pad" optional />
            </View>
          )}

          {/* Step 2: Verification */}
          {step === 2 && (
            <View>
              <Text style={[s.title, { fontSize: theme.fontSize.lg, marginBottom: theme.spacing.xs }]}>Verification</Text>
              <Text style={[s.textMuted, { marginBottom: 20 }]}>Optional but helps speed up approval</Text>
              <Field label="Trade License Number" value={form.trade_license_no} onChange={update("trade_license_no")} placeholder="e.g. TL-123456" optional />
              <Field label="Tax Registration Number" value={form.tax_reg_no} onChange={update("tax_reg_no")} placeholder="e.g. VAT-7890" optional />
              <Field label="Website URL" value={form.website_url} onChange={update("website_url")} placeholder="https://yourstore.com" keyboardType="url" optional />
            </View>
          )}

          {/* Step 3: Terms */}
          {step === 3 && (
            <View>
              <Text style={[s.title, { fontSize: theme.fontSize.lg, marginBottom: theme.spacing.xs }]}>Terms & Conditions</Text>
              <Text style={[s.textMuted, { marginBottom: 20 }]}>Please review our supplier agreement</Text>
              <View style={[localStyles.termsBox, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                {[
                  "Suppliers must list only authentic, genuine products.",
                  "A platform commission of 5–15% applies on each sale.",
                  "Products must comply with all applicable laws and regulations.",
                  "ZOZI reserves the right to suspend accounts that violate policies.",
                  "Payouts are processed within 7 business days after order completion.",
                  "You agree to handle customer complaints professionally.",
                ].map((t, i) => (
                  <View key={i} style={{ flexDirection: "row", gap: theme.spacing.sm, marginBottom: 10 }}>
                    <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{i + 1}.</Text>
                    <Text style={{ color: theme.colors.textMuted, flex: 1, fontSize: theme.fontSize.sm }}>{t}</Text>
                  </View>
                ))}
              </View>
              <TouchableOpacity
                style={[localStyles.termsRow, { borderColor: theme.colors.border }]}
                onPress={() => update("terms_accepted")(!form.terms_accepted)}
              >
                <Switch
                  value={form.terms_accepted}
                  onValueChange={(v) => update("terms_accepted")(v)}
                  trackColor={{ true: theme.colors.brand }}
                />
                <Text style={[s.text, { flex: 1, fontSize: theme.fontSize.sm, marginLeft: 10 }]}>
                  I have read and agree to the Supplier Terms & Conditions
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Navigation buttons */}
          <View style={localStyles.navRow}>
            {step > 0 && (
              <TouchableOpacity style={[localStyles.navBtn, { borderColor: theme.colors.border }]} onPress={prev}>
                <Text style={{ color: theme.colors.text, fontWeight: "600" }}>← Back</Text>
              </TouchableOpacity>
            )}
            {step < STEPS.length - 1 ? (
              <TouchableOpacity style={[localStyles.navBtn, { backgroundColor: theme.colors.brand, flex: 1 }]} onPress={next}>
                <Text style={{ color: "#fff", fontWeight: "700" }}>Next →</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={[localStyles.navBtn, { backgroundColor: theme.colors.brand, flex: 1 }, loading && { opacity: 0.6 }]}
                onPress={submit}
                disabled={loading}
              >
                {loading
                  ? <ActivityIndicator color="#fff" size="small" />
                  : <Text style={{ color: "#fff", fontWeight: "700" }}>Submit Application</Text>}
              </TouchableOpacity>
            )}
          </View>

          <TouchableOpacity style={{ alignItems: "center", marginTop: theme.spacing.md }} onPress={() => router.push("/supplier/login" as never)}>
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
              Already a supplier?{" "}
              <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>Sign in →</Text>
            </Text>
          </TouchableOpacity>

        </ScrollView>
      </KeyboardAvoidingView>
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  steps: {
    flexDirection: "row",
    marginBottom: 28,
    position: "relative",
  },
  stepDot: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
  },
  stepLine: {
    height: 2,
    width: "100%",
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
  },
  optionBtn: {
    borderWidth: 1.5,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
  },
  chip: {
    borderWidth: 1,
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  termsBox: {
    borderWidth: 1,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  termsRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: theme.spacing.sm,
  },
  errorBox: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: theme.spacing.md,
  },
  navRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: theme.spacing.lg,
  },
  navBtn: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: theme.radius.lg,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "transparent",
  },
});
