"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Phone, Clock, Send, CheckCircle } from "@/lib/icons";

const MotionDiv: any = motion.div;

import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

interface ContactForm {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export default function ContactPage() {
  const [formData, setFormData] = useState<ContactForm>({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const { isLoggedIn, user } = useAuth();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.subject || !formData.message) {
      setError("All fields are required");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const res = await apiFetch("/contact", {
        method: "POST",
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        setError(payload?.detail || payload?.message || "Failed to send message");
        return;
      }
      setSuccess(true);
      setFormData({ name: "", email: "", subject: "", message: "" });
    } catch (err: unknown) {
      const apiErr = err as { detail?: string; message?: string };
      setError(apiErr?.detail ?? apiErr?.message ?? "Failed to send message");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-surface-base py-12 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-text">Contact Us</h1>
          <p className="text-text-muted mt-2">We're here to help. Reach out to our team.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <MotionDiv
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="theme-card border rounded-xl p-5"
          >
            <Mail className="w-6 h-6 text-primary mb-3" />
            <h3 className="font-semibold text-text mb-1">Email</h3>
            <p className="text-sm text-text-faint">support@zozi.com</p>
          </MotionDiv>

          <MotionDiv
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="theme-card border rounded-xl p-5"
          >
            <Phone className="w-6 h-6 text-primary mb-3" />
            <h3 className="font-semibold text-text mb-1">Phone</h3>
            <p className="text-sm text-text-faint">+1 (555) 123-4567</p>
          </MotionDiv>

          <MotionDiv
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="theme-card border rounded-xl p-5"
          >
            <Clock className="w-6 h-6 text-primary mb-3" />
            <h3 className="font-semibold text-text mb-1">Hours</h3>
            <p className="text-sm text-text-faint">24/7 Support</p>
          </MotionDiv>
        </div>

        <MotionDiv
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="theme-card border rounded-2xl p-6"
        >
          <h2 className="text-xl font-bold text-text mb-5">Send a Message</h2>

          {success && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="theme-alert-success mb-5 flex items-center gap-3 rounded-xl p-4"
            >
              <CheckCircle className="theme-status-success h-5 w-5" />
              <p className="theme-status-success text-sm font-medium">Message sent successfully!</p>
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="block text-xs font-semibold text-text-muted mb-1">
                  Name
                </label>
                <input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  disabled={submitting}
                  className="w-full px-4 py-2.5 rounded-xl theme-input border text-text text-sm"
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-xs font-semibold text-text-muted mb-1">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={submitting}
                  className="w-full px-4 py-2.5 rounded-xl theme-input border text-text text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="subject" className="block text-xs font-semibold text-text-muted mb-1">
                Subject
              </label>
              <input
                id="subject"
                name="subject"
                value={formData.subject}
                onChange={handleChange}
                required
                disabled={submitting}
                className="w-full px-4 py-2.5 rounded-xl theme-input border text-text text-sm"
              />
            </div>

            <div>
              <label htmlFor="message" className="block text-xs font-semibold text-text-muted mb-1">
                Message
              </label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                rows={5}
                required
                disabled={submitting}
                className="w-full px-4 py-2.5 rounded-xl theme-input border text-text text-sm resize-none"
              />
            </div>

            {error && <p className="text-sm text-status-danger">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <span className="btn-spinner" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Send Message
                </>
              )}
            </button>
          </form>
        </MotionDiv>
      </div>
    </main>
  );
}


