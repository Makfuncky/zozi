"use client";

import { useEffect, useState, type MouseEvent as ReactMouseEvent } from "react";
import DOMPurify from "dompurify";
import { motion } from "framer-motion";
import { X, Save } from "@/lib/icons";
import { apiFetch } from "@/lib/api";

interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  content: string;
  template_type: string;
}

interface CreateCampaignFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateCampaignForm({ onClose, onSuccess }: CreateCampaignFormProps) {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    subject: "",
    html_content: "",
    text_content: "",
    subject_b: "",
    ab_test_enabled: false,
    template_id: "",
    target_audience: "all",
    send_at: "",
  });

  async function loadTemplates() {
    try {
      const response = await apiFetch("/email/templates");
      if (response.ok) {
        const data = await response.json();
        const normalizedTemplates: EmailTemplate[] = Array.isArray(data)
          ? data.map((template: any) => ({
              id: Number(template?.id ?? 0),
              name: String(template?.name ?? ""),
              subject: String(template?.subject ?? ""),
              content: String(template?.content ?? template?.html_content ?? ""),
              template_type: String(template?.template_type ?? "marketing"),
            }))
          : [];
        setTemplates(normalizedTemplates);
      }
    } catch (error) {
      console.error("Failed to load templates:", error);
    }
  }

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleTemplateChange = (templateId: string) => {
    const template = templates.find(t => t.id.toString() === templateId);
    if (template) {
      const templateContent = template.content || "";
      setFormData(prev => ({
        ...prev,
        template_id: templateId,
        subject: template.subject,
        html_content: templateContent,
        text_content: templateContent.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim(),
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const templateId = formData.template_id ? parseInt(formData.template_id, 10) : null;
      const payload = {
        name: formData.name.trim(),
        subject: formData.subject.trim(),
        html_content: formData.html_content,
        text_content: formData.text_content || null,
        template_id: templateId,
        target_audience: formData.target_audience,
        send_at: formData.send_at || null,
        subject_b: formData.ab_test_enabled && formData.subject_b.trim() ? formData.subject_b.trim() : null,
        ab_test_enabled: formData.ab_test_enabled,
      };

      const response = await apiFetch("/email/campaigns", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        onSuccess();
        onClose();
      } else {
        alert("Failed to create campaign");
      }
    } catch (error) {
      console.error("Failed to create campaign:", error);
      alert("Failed to create campaign");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 theme-overlay flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9 }}
        animate={{ scale: 1 }}
        className="bg-surface-1 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-border"
        onClick={(e: ReactMouseEvent<HTMLDivElement>) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="text-lg font-medium text-text">Create Email Campaign</h3>
          <button
            onClick={onClose}
            className="text-text-faint hover:text-text-muted"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Campaign Name */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Campaign Name
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary theme-input"
              placeholder="e.g., Spring Sale 2024"
            />
          </div>

          {/* Email Template */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Email Template
            </label>
            <select
              required
              value={formData.template_id}
              onChange={(e) => handleTemplateChange(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary theme-input"
            >
              <option value="">Select a template...</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name} - {template.template_type}
                </option>
              ))}
            </select>
          </div>

          {/* Subject Line */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Subject Line (Variant A)
            </label>
            <input
              type="text"
              required
              value={formData.subject}
              onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary theme-input"
              placeholder="Enter email subject..."
            />
          </div>

          {/* A/B Test Toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="ab_test_enabled"
              checked={formData.ab_test_enabled}
              onChange={(e) => setFormData(prev => ({ ...prev, ab_test_enabled: e.target.checked }))}
              className="w-4 h-4 accent-primary"
            />
            <label htmlFor="ab_test_enabled" className="text-sm font-medium text-text cursor-pointer">
              Enable A/B subject line test (50/50 split)
            </label>
          </div>

          {/* Variant B Subject */}
          {formData.ab_test_enabled && (
            <div>
              <label className="block text-sm font-medium text-text mb-2">
                Subject Line (Variant B)
              </label>
              <input
                type="text"
                required={formData.ab_test_enabled}
                value={formData.subject_b}
                onChange={(e) => setFormData(prev => ({ ...prev, subject_b: e.target.value }))}
                className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary theme-input"
                placeholder="Alternate subject for 50% of recipients..."
              />
              <p className="text-xs text-text-faint mt-1">
                Half your recipients will receive Variant A, half will receive Variant B.
                Compare open rates in the campaign analytics to pick a winner.
              </p>
            </div>
          )}

          {/* Target Audience */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Target Audience
            </label>
            <select
              value={formData.target_audience}
              onChange={(e) => setFormData(prev => ({ ...prev, target_audience: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary theme-input"
            >
              <option value="all">All Customers, Suppliers, Logistics + Newsletter</option>
              <option value="subscribers">Newsletter Subscribers Only</option>
              <option value="customers">Customers</option>
              <option value="suppliers">Suppliers</option>
              <option value="logistics">Logistics Partners</option>
              <option value="all_registered">All Registered Users</option>
            </select>
          </div>

          {/* Schedule Send */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Schedule Send (Optional)
            </label>
            <input
              type="datetime-local"
              value={formData.send_at}
              onChange={(e) => setFormData(prev => ({ ...prev, send_at: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary theme-input"
            />
            <p className="text-xs text-text-faint mt-1">
              Leave empty to send immediately after creation
            </p>
          </div>

          {/* Email Content Preview */}
          {formData.html_content && (
            <div>
              <label className="block text-sm font-medium text-text mb-2">
                Email Content Preview
              </label>
              <div className="border border-border rounded-md p-4 max-h-64 overflow-y-auto">
                <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formData.html_content) }} />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-text-muted hover:text-text"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="theme-btn-primary px-4 py-2 rounded-md disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Save className="w-4 h-4" />
              )}
              Create Campaign
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}


