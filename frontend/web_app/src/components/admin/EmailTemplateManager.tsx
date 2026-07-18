"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useMemo, useState, type MouseEvent as ReactMouseEvent } from "react";
import DOMPurify from "dompurify";
import { motion } from "framer-motion";
import {
  Plus, Edit2, Trash2, Eye, Code, Save, X
} from "@/lib/icons";
import { useDensity } from "@/lib/densityContext";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  content: string;
  template_type: string;
  created_at: string;
  updated_at: string;
}

export default function EmailTemplateManager() {
  const { density } = useDensity();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTemplateId, setExpandedTemplateId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null);
  const [typeFilter, setTypeFilter] = useState("all");
  const addToast = useToastStore((state) => state.addToast);

  useEffect(() => {
    loadTemplates();
  }, []);

  async function loadTemplates() {
    try {
      const response = await apiFetch("/email/templates");
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error("Failed to load templates:", error);
    } finally {
      setLoading(false);
    }
  }

  const deleteTemplate = async (templateId: number) => {
    if (!confirm("Are you sure you want to delete this template?")) {
      return;
    }

    try {
      const response = await apiFetch(`/email/templates/${templateId}`, {
        method: "DELETE"
      });

      if (response.ok) {
        setTemplates((current) => current.filter((t) => t.id !== templateId));
        setExpandedTemplateId((current) => (current === templateId ? null : current));
        addToast("Template deleted", "success");
      } else {
        addToast("Failed to delete template", "error");
      }
    } catch (error) {
      console.error("Failed to delete template:", error);
      addToast("Failed to delete template", "error");
    }
  };

  const getTemplateTypeColor = (type: string) => {
    switch (type) {
      case "promotional":
        return "bg-info/15 text-info";
      case "newsletter":
        return "bg-success/15 text-success";
      case "welcome":
        return "bg-primary/15 text-primary";
      case "transactional":
        return "bg-warning/15 text-warning";
      default:
        return "bg-surface-2 text-text-muted";
    }
  };

  const filteredTemplates = useMemo(
    () => templates.filter((template) => typeFilter === "all" || template.template_type === typeFilter),
    [templates, typeFilter]
  );

  const templateColumns = useMemo<Array<EnterpriseColumn<EmailTemplate>>>(() => [
    {
      key: "name",
      label: "Template",
      sortable: true,
      sortValue: (template) => template.name.toLowerCase(),
      searchValue: (template) => `${template.name} ${template.subject}`,
      render: (template) => (
        <div>
          <div className="font-semibold text-text">{template.name}</div>
          <div className="mt-0.5 text-[11px] text-text-faint">{template.subject}</div>
        </div>
      ),
    },
    {
      key: "template_type",
      label: "Type",
      sortable: true,
      sortValue: (template) => template.template_type,
      searchValue: (template) => template.template_type,
      render: (template) => (
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTemplateTypeColor(template.template_type)}`}>
          {template.template_type}
        </span>
      ),
    },
    {
      key: "updated_at",
      label: "Updated",
      sortable: true,
      sortValue: (template) => new Date(template.updated_at).getTime(),
      searchValue: (template) => `${template.updated_at} ${template.created_at}`,
      render: (template) => <span className="text-xs text-text-faint">{new Date(template.updated_at).toLocaleDateString()}</span>,
    },
    {
      key: "created_at",
      label: "Created",
      sortable: true,
      sortValue: (template) => new Date(template.created_at).getTime(),
      searchValue: (template) => template.created_at,
      render: (template) => <span className="text-xs text-text-faint">{new Date(template.created_at).toLocaleDateString()}</span>,
    },
  ], []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-text">Email Templates</h2>
          <p className="text-xs text-text-muted">Create and manage reusable templates in the same shared table workflow as campaigns and finance.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none">
            <option value="all">All types</option>
            <option value="promotional">Promotional</option>
            <option value="newsletter">Newsletter</option>
            <option value="welcome">Welcome</option>
            <option value="transactional">Transactional</option>
          </select>
          <button
            onClick={() => setShowCreateForm(true)}
            className="theme-btn-primary px-4 py-2 rounded-lg flex items-center gap-2 text-xs font-semibold"
          >
            <Plus className="w-4 h-4" />
            New Template
          </button>
        </div>
      </div>

      <div className="theme-card rounded-xl border p-3">
        <EnterpriseDataTable
          columns={templateColumns}
          rows={filteredTemplates}
          rowKey={(template) => template.id}
          densityMode={density}
          emptyState="No templates found. Create your first email template."
          searchPlaceholder="Search by template name, subject, or type"
          expandedRowKey={expandedTemplateId ?? undefined}
          rowActions={(template) => {
            const isExpanded = expandedTemplateId === template.id;
            return (
              <div className="flex flex-wrap items-center justify-end gap-1.5">
                <Button variant="secondary" className="rounded-md border border-border bg-surface px-2 py-1 text-[11px] font-semibold text-text-muted transition-colors hover:text-primary" type="button"
                  onClick={() => setExpandedTemplateId(isExpanded ? null : template.id)}
                >
                  {isExpanded ? "Hide preview" : "Preview"}
                </Button>
                <button
                  type="button"
                  onClick={() => setEditingTemplate(template)}
                  className="rounded-md border border-border bg-surface px-2 py-1 text-[11px] font-semibold text-text hover:bg-surface-2"
                >
                  Edit
                </button>
                <Button variant="danger" className="rounded-md px-2 py-1 text-[11px] font-semibold text-danger" type="button"
                  onClick={() => void deleteTemplate(template.id)}
                >
                  Delete
                </Button>
              </div>
            );
          }}
          mobileCardRenderer={(template) => (
            <div className="space-y-2 text-xs">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-text">{template.name}</p>
                  <p className="mt-1 text-text-faint">{template.subject}</p>
                </div>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium ${getTemplateTypeColor(template.template_type)}`}>
                  {template.template_type}
                </span>
              </div>
              <p className="text-text-muted">Updated {new Date(template.updated_at).toLocaleDateString()}</p>
            </div>
          )}
          expandedRowRenderer={(template) => (
            <div className="p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h4 className="text-sm font-bold text-text">Template Preview</h4>
                  <p className="mt-1 text-xs text-text-muted">Reusable preview for {template.name}.</p>
                </div>
                <button type="button" onClick={() => setExpandedTemplateId(null)} className="rounded-lg border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">
                  Close
                </button>
              </div>
              <div className="grid gap-3 xl:grid-cols-[260px_minmax(0,1fr)]">
                <div className="space-y-3">
                  <div className="rounded-xl border border-border bg-surface-1 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Template Type</p>
                    <p className="mt-1.5 text-xs font-medium capitalize text-text">{template.template_type}</p>
                  </div>
                  <div className="rounded-xl border border-border bg-surface-1 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Subject</p>
                    <p className="mt-1.5 text-xs font-medium text-text">{template.subject}</p>
                  </div>
                  <div className="rounded-xl border border-border bg-info/10 p-3">
                    <h5 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-info">Variables</h5>
                    <div className="mt-2 space-y-1 text-[11px] text-info">
                      <div><code>{"{{customer_name}}"}</code></div>
                      <div><code>{"{{customer_email}}"}</code></div>
                      <div><code>{"{{unsubscribe_link}}"}</code></div>
                      <div><code>{"{{tracking_pixel}}"}</code></div>
                      <div><code>{"{{company_name}}"}</code></div>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
                  <div className="border-b border-border bg-surface-2 px-4 py-2 text-sm text-text-muted">
                    <strong>Subject:</strong> {template.subject}
                  </div>
                  <div className="max-h-96 overflow-y-auto p-4">
                    <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(template.content) }} />
                  </div>
                </div>
              </div>
            </div>
          )}
        />
      </div>

      {/* Create/Edit Template Form */}
      {(showCreateForm || editingTemplate) && (
        <TemplateForm
          template={editingTemplate}
          onClose={() => {
            setShowCreateForm(false);
            setEditingTemplate(null);
          }}
          onSuccess={() => {
            setShowCreateForm(false);
            setEditingTemplate(null);
            loadTemplates();
          }}
        />
      )}
    </div>
  );
}

interface TemplateFormProps {
  template?: EmailTemplate | null;
  onClose: () => void;
  onSuccess: () => void;
}

function TemplateForm({ template, onClose, onSuccess }: TemplateFormProps) {
  const [formData, setFormData] = useState({
    name: template?.name || "",
    subject: template?.subject || "",
    content: template?.content || "",
    template_type: template?.template_type || "promotional"
  });
  const [loading, setLoading] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const url = template ? `/email/templates/${template.id}` : "/email/templates";
      const method = template ? "PUT" : "POST";

      const response = await apiFetch(url, {
        method,
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        onSuccess();
      } else {
        alert("Failed to save template");
      }
    } catch (error) {
      console.error("Failed to save template:", error);
      alert("Failed to save template");
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
        className="glass-panel rounded-xl max-w-6xl w-full max-h-[95vh] overflow-hidden border"
        onClick={(e: ReactMouseEvent<HTMLDivElement>) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="text-lg font-medium text-text">
            {template ? "Edit Template" : "Create Template"}
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPreviewMode(!previewMode)}
              className="text-text-faint hover:text-text-muted p-1"
              title={previewMode ? "Edit Mode" : "Preview Mode"}
            >
              {previewMode ? <Code className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="text-text-faint hover:text-text-muted"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex h-[calc(95vh-80px)]">
          {/* Form Section */}
          <div className="w-1/2 p-6 border-r border-border overflow-y-auto">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  Template Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="e.g., Spring Sale Template"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  Subject Line
                </label>
                <input
                  type="text"
                  required
                  value={formData.subject}
                  onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="e.g., {{customer_name}}, Check out our amazing deals!"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  Template Type
                </label>
                <select
                  value={formData.template_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, template_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="promotional">Promotional</option>
                  <option value="newsletter">Newsletter</option>
                  <option value="welcome">Welcome</option>
                  <option value="transactional">Transactional</option>
                </select>
              </div>

              <div className="flex-1">
                <label className="block text-sm font-medium text-text mb-1">
                  HTML Content
                </label>
                <textarea
                  required
                  value={formData.content}
                  onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
                  className="w-full h-64 px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                  placeholder="<html>...</html>"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-border">
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
                {template ? "Update" : "Create"} Template
              </button>
            </div>
          </div>

          {/* Preview Section */}
          <div className="w-1/2 p-6 overflow-y-auto">
            <div className="mb-4">
              <h4 className="text-sm font-medium text-text mb-2">Live Preview</h4>
              <div className="border border-border rounded-lg overflow-hidden">
                <div className="bg-surface-2 px-4 py-2 border-b border-border">
                  <div className="text-sm text-text-muted">
                    <strong>Subject:</strong> {formData.subject}
                  </div>
                </div>
                <div className="p-4 max-h-96 overflow-y-auto">
                  {formData.content ? (
                    <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formData.content) }} />
                  ) : (
                    <div className="text-text-faint text-center py-8">
                      Enter HTML content to see preview
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-info/10 p-4 rounded-lg">
              <h5 className="text-sm font-medium text-info mb-2">Available Variables</h5>
              <div className="text-xs text-info space-y-1">
                <div><code>{"{{customer_name}}"}</code> - Customer's full name</div>
                <div><code>{"{{customer_email}}"}</code> - Customer's email</div>
                <div><code>{"{{unsubscribe_link}}"}</code> - Unsubscribe URL</div>
                <div><code>{"{{tracking_pixel}}"}</code> - Email tracking pixel</div>
                <div><code>{"{{company_name}}"}</code> - ZOZI</div>
              </div>
            </div>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}


