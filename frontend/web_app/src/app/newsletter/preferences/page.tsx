"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";

const MotionDiv: any = motion.div;

import { Mail, CheckCircle, XCircle } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

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

export default function NewsletterPreferences() {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const loadPreferences = useCallback(async () => {
    try {
      const userEmail = user?.email;
      if (!userEmail) {
        setMessage("Please log in to manage your email preferences.");
        setLoading(false);
        return;
      }

      const response = await apiFetch(`/email/newsletter/preferences?email=${encodeURIComponent(userEmail)}`);
      if (response.ok) {
        const data = await response.json();
        setPreferences(data);
      } else {
        setMessage("Unable to load your preferences. Please try again.");
      }
    } catch (error) {
      console.error("Failed to load preferences:", error);
      setMessage("An error occurred while loading your preferences.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  const updatePreferences = async (newPreferences: Partial<UserPreferences['preferences']>) => {
    if (!preferences) return;

    setSaving(true);
    try {
      const response = await apiFetch("/email/newsletter/preferences", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email: preferences.email,
          preferences: { ...preferences.preferences, ...newPreferences }
        })
      });

      if (response.ok) {
        setPreferences(prev => prev ? {
          ...prev,
          preferences: { ...prev.preferences, ...newPreferences }
        } : null);
        setMessage("Preferences updated successfully!");
        setTimeout(() => setMessage(""), 3000);
      } else {
        setMessage("Failed to update preferences. Please try again.");
      }
    } catch (error) {
      console.error("Failed to update preferences:", error);
      setMessage("An error occurred while updating your preferences.");
    } finally {
      setSaving(false);
    }
  };

  const unsubscribeAll = async () => {
    if (!confirm("Are you sure you want to unsubscribe from all emails? You can always resubscribe later.")) {
      return;
    }

    try {
      const response = await apiFetch("/email/newsletter/unsubscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email: preferences?.email })
      });

      if (response.ok) {
        setMessage("You have been unsubscribed from all emails.");
        setPreferences(prev => prev ? { ...prev, is_active: false } : null);
      } else {
        setMessage("Failed to unsubscribe. Please try again.");
      }
    } catch (error) {
      console.error("Failed to unsubscribe:", error);
      setMessage("An error occurred while unsubscribing.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-base flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="min-h-screen bg-surface-base flex items-center justify-center px-4">
        <div className="max-w-md w-full theme-card shadow-lg p-8 text-center">
          <Mail className="w-16 h-16 text-primary/40 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-text mb-4">Email Preferences</h1>
          <p className="text-text-muted mb-6">{message || "Please log in to manage your email preferences."}</p>
          <button
            onClick={() => window.location.href = "/auth/login"}
            className="theme-btn-primary px-6 py-2 rounded-lg"
          >
            Log In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-base">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text">Email Preferences</h1>
          <p className="text-text-muted mt-2">Manage your email subscriptions and preferences</p>
        </div>

        {/* Status Message */}
        {message && (
          <MotionDiv
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-6 p-4 rounded-lg ${
              message.includes("success") || message.includes("updated") || message.includes("unsubscribed")
                ? "theme-alert-success"
                : "theme-alert-danger"
            }`}
          >
            {message}
          </MotionDiv>
        )}

        {/* Current Status */}
        <div className="theme-card rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-text">Subscription Status</h2>
              <p className="mt-1 text-sm text-text-muted">
                Subscribed on {new Date(preferences.subscribed_at).toLocaleDateString()}
              </p>
            </div>
            <div className="flex items-center">
              {preferences.is_active ? (
                <CheckCircle className="theme-status-success mr-2 h-5 w-5" />
              ) : (
                <XCircle className="theme-status-danger mr-2 h-5 w-5" />
              )}
              <span className={`text-sm font-medium ${
                preferences.is_active ? "theme-status-success" : "theme-status-danger"
              }`}>
                {preferences.is_active ? "Active" : "Unsubscribed"}
              </span>
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="theme-card rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-medium text-text mb-4">Email Preferences</h2>

          <div className="space-y-4">
            {[
              {
                key: "newsletter",
                label: "Newsletter",
                description: "Weekly updates about new products, fashion trends, and exclusive offers"
              },
              {
                key: "promotional_emails",
                label: "Promotional Emails",
                description: "Special promotions, flash sales, and limited-time offers"
              },
              {
                key: "product_updates",
                label: "Product Updates",
                description: "Notifications about new arrivals and product restocks"
              },
              {
                key: "order_updates",
                label: "Order Updates",
                description: "Updates about your orders, shipping, and delivery status"
              },
              {
                key: "marketing_emails",
                label: "Marketing Communications",
                description: "Personalized recommendations and marketing content"
              }
            ].map(({ key, label, description }) => (
              <div key={key} className="flex items-start justify-between p-4 border border-border rounded-lg bg-surface-1">
                <div className="flex-1">
                  <h3 className="font-medium text-text">{label}</h3>
                  <p className="text-sm text-text-muted mt-1">{description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={preferences.preferences[key as keyof typeof preferences.preferences]}
                    onChange={(e) => updatePreferences({ [key]: e.target.checked })}
                    disabled={saving || !preferences.is_active}
                    className="sr-only peer"
                  />
                  <div className="peer h-6 w-11 rounded-full bg-border peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-border-light peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-['']"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="theme-card rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-text mb-4">Account Actions</h2>

          <div className="space-y-3">
            <button
              onClick={unsubscribeAll}
              disabled={!preferences.is_active}
              className="theme-action-danger w-full rounded-lg border border-border px-4 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Unsubscribe from All Emails
            </button>

            <p className="text-xs text-text-muted">
              You can always resubscribe by signing up for our newsletter again.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


