"use client";

import { useEffect, useState, useCallback, type ChangeEvent } from "react";
import { motion } from "framer-motion";
import {
  User,
  Mail,
  Phone,
  MapPin,
  Save,
  AlertCircle,
  CheckCircle,
  Contact2,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { PanelLoadingState } from "@/components/PanelPage";
import { useToastStore } from "@/stores/toastStore";
import { ErrorBoundary, ErrorState } from "@/components/employee/ErrorBoundary";

interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
}

interface ProfileData {
  full_name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  emergency_contacts: EmergencyContact[];
}

export default function EmployeeProfilePage() {
  const { user } = useAuth();
  const { addToast } = useToastStore();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [profile, setProfile] = useState<ProfileData>({
    full_name: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    country: "",
    emergency_contacts: [{ name: "", relationship: "", phone: "" }],
  });

  const fetchProfile = useCallback(async () => {
    setFetching(true);
    setError("");
    try {
      const res = await apiFetch("/api/v1/employee/hr/profile");
      if (res.ok) {
        const data = await res.json();
        setProfile({
          full_name: data.full_name || "",
          email: data.email || "",
          phone: data.phone || "",
          address: data.address || "",
          city: data.city || "",
          country: data.country || "",
          emergency_contacts: data.emergency_contacts?.length
            ? data.emergency_contacts
            : [{ name: "", relationship: "", phone: "" }],
        });
      } else {
        setError("Failed to load profile");
      }
    } catch {
      setError("Failed to load profile");
    } finally {
      setFetching(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleChange = (field: keyof ProfileData) => (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setProfile((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleContactChange = (index: number, field: keyof EmergencyContact) => (
    e: ChangeEvent<HTMLInputElement>,
  ) => {
    setProfile((prev) => ({
      ...prev,
      emergency_contacts: prev.emergency_contacts.map((c, i) =>
        i === index ? { ...c, [field]: e.target.value } : c,
      ),
    }));
  };

  const addContact = () => {
    setProfile((prev) => ({
      ...prev,
      emergency_contacts: [...prev.emergency_contacts, { name: "", relationship: "", phone: "" }],
    }));
  };

  const removeContact = (index: number) => {
    setProfile((prev) => ({
      ...prev,
      emergency_contacts: prev.emergency_contacts.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/employee/hr/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const msg = data.detail || "Failed to update profile";
        setError(msg);
        addToast(msg, "error");
        return;
      }
      setSuccess("Profile updated successfully");
      addToast("Profile updated successfully", "success");
    } catch {
      setError("Network error occurred");
      addToast("Network error occurred", "error");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <PanelLoadingState count={3} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />;
  }

  if (error && !profile.full_name) {
    return <ErrorState message={error} onRetry={fetchProfile} />;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-text">My Profile</h1>
        <p className="text-sm text-text-muted mt-1">Manage your personal information and emergency contacts</p>
      </div>

      {error && (
        <Alert tone="danger" title="Error">
          {error}
        </Alert>
      )}
      {success && (
        <Alert tone="success" title="Success">
          {success}
        </Alert>
      )}

      <motion.form
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="space-y-6"
      >
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <h2 className="text-sm font-semibold text-text flex items-center gap-2">
            <User className="h-4 w-4 text-primary" />
            Personal Information
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Full Name</label>
              <Input
                value={profile.full_name}
                onChange={handleChange("full_name")}
                placeholder="Your full name"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Email</label>
              <Input
                type="email"
                value={profile.email}
                onChange={handleChange("email")}
                placeholder="email@example.com"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Phone</label>
              <Input
                value={profile.phone}
                onChange={handleChange("phone")}
                placeholder="+968 ..."
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">City</label>
              <Input
                value={profile.city}
                onChange={handleChange("city")}
                placeholder="Muscat"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Country</label>
              <Input
                value={profile.country}
                onChange={handleChange("country")}
                placeholder="Oman"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Address</label>
              <Input
                value={profile.address}
                onChange={handleChange("address")}
                placeholder="Street address"
              />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-text flex items-center gap-2">
              <Contact2 className="h-4 w-4 text-info" />
              Emergency Contacts
            </h2>
            <Button type="button" variant="secondary" size="sm" onClick={addContact}>
              Add Contact
            </Button>
          </div>
          {profile.emergency_contacts.map((contact, index) => (
            <div key={index} className="grid grid-cols-1 gap-3 sm:grid-cols-4 items-end p-3 rounded-lg bg-surface-2">
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-muted">Name</label>
                <Input
                  value={contact.name}
                  onChange={handleContactChange(index, "name")}
                  placeholder="Contact name"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-muted">Relationship</label>
                <Input
                  value={contact.relationship}
                  onChange={handleContactChange(index, "relationship")}
                  placeholder="Spouse, Parent..."
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-text-muted">Phone</label>
                <Input
                  value={contact.phone}
                  onChange={handleContactChange(index, "phone")}
                  placeholder="+968 ..."
                />
              </div>
              <Button
                type="button"
                variant="danger-outline"
                size="sm"
                onClick={() => removeContact(index)}
                disabled={profile.emergency_contacts.length <= 1}
              >
                Remove
              </Button>
            </div>
          ))}
        </div>

        <div className="flex justify-end">
          <Button type="submit" isLoading={loading} leftIcon={<Save className="h-4 w-4" />}>
            Save Changes
          </Button>
        </div>
      </motion.form>
    </div>
  );
}
