"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Store, Mail, Lock, User, Building2, Phone, FileText, Globe, MapPin } from "@/lib/icons";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import TranslatedText from "@/components/TranslatedText";

export default function SupplierRegisterPage() {
  const router = useRouter();
  const addToast = useToastStore((s) => s.addToast);
  const tr = useLocaleStore((s) => s.t);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    business_name: "",
    business_type: "",
    tax_reg_no: "",
    phone: "",
    country: "",
    city: "",
    website: "",
    about_us: "",
  });

  const update = (patch: Partial<typeof form>) => setForm((prev) => ({ ...prev, ...patch }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) { addToast("Passwords do not match", "error"); return; }
    setSubmitting(true);
    try {
      const res = await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: form.username,
          email: form.email,
          password: form.password,
          role: "supplier",
          full_name: form.business_name || form.username,
          phone: form.phone || null,
          business_name: form.business_name,
          business_type: form.business_type || null,
          tax_reg_no: form.tax_reg_no || null,
          country: form.country || null,
          city: form.city || null,
          website: form.website || null,
          bio: form.about_us || null,
        }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || "Registration failed"); }
      addToast("Supplier account created! Please sign in.", "success");
      router.push("/supplier/login");
    } catch (err: any) {
      addToast(err.message || "Registration failed", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen py-10 px-4" dir="ltr">
      <div className="mx-auto max-w-2xl">
        <button onClick={() => router.back()} className="flex items-center gap-2 text-xs text-text-muted hover:text-text mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-2xl border p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary"><Store className="w-5 h-5" /></div>
            <div>
              <h1 className="text-lg font-bold text-text">Become a Supplier</h1>
              <p className="text-xs text-text-faint">Create your supplier account and start selling on ZOZI.</p>
            </div>
          </div>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Username *</label>
                <div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input value={form.username} onChange={(e) => update({ username: e.target.value })} required className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
              </div>
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Email *</label>
                <div className="relative"><Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input type="email" value={form.email} onChange={(e) => update({ email: e.target.value })} required className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
              </div>
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Password *</label>
                <div className="relative"><Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input type="password" value={form.password} onChange={(e) => update({ password: e.target.value })} required className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
              </div>
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">Confirm Password *</label>
                <div className="relative"><Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input type="password" value={form.confirmPassword} onChange={(e) => update({ confirmPassword: e.target.value })} required className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
              </div>
            </div>

            <div className="theme-panel rounded-xl border border-border p-3 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-text"><Building2 className="w-4 h-4 text-primary" /> Business Information</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Business Name *</label>
                  <input value={form.business_name} onChange={(e) => update({ business_name: e.target.value })} required className="theme-input w-full rounded-xl border py-2 px-3 text-xs" />
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Business Type</label>
                  <input value={form.business_type} onChange={(e) => update({ business_type: e.target.value })} className="theme-input w-full rounded-xl border py-2 px-3 text-xs" placeholder="e.g. LLC, Sole Proprietor" />
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Tax / TRN</label>
                  <div className="relative"><FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input value={form.tax_reg_no} onChange={(e) => update({ tax_reg_no: e.target.value })} className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Phone</label>
                  <div className="relative"><Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input value={form.phone} onChange={(e) => update({ phone: e.target.value })} className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Country</label>
                  <div className="relative"><Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input value={form.country} onChange={(e) => update({ country: e.target.value })} className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">City</label>
                  <div className="relative"><MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary/50" /><input value={form.city} onChange={(e) => update({ city: e.target.value })} className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" /></div>
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">Website</label>
                  <input value={form.website} onChange={(e) => update({ website: e.target.value })} className="theme-input w-full rounded-xl border py-2 px-3 text-xs" placeholder="https://..." />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-[11px] font-semibold text-text-muted">About Your Business</label>
                  <textarea value={form.about_us} onChange={(e) => update({ about_us: e.target.value })} rows={3} className="theme-input w-full rounded-xl border py-2 px-3 text-xs resize-none" />
                </div>
              </div>
            </div>

            <button type="submit" disabled={submitting} className="theme-btn-primary w-full rounded-xl py-3 text-sm font-bold disabled:opacity-60">
              {submitting ? "Creating Account..." : "Create Supplier Account"}
            </button>
            <p className="text-center text-[11px] text-text-faint">By registering, you agree to ZOZI&apos;s supplier terms and conditions.</p>
          </form>
        </motion.div>
      </div>
    </main>
  );
}
