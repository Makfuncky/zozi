"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import {
  Mail, BarChart3, FileText, Users, Send, Inbox,
  Eye, MousePointer, ShieldAlert, Plus, X,
  RefreshCw, Search, Filter, MoreHorizontal,
  Clock, CheckCircle2, AlertCircle, Ban,
  ChevronDown, ChevronUp, ChevronRight, Paperclip,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { PanelContent, PanelLoadingState, PanelTabs, PanelCard, PanelGrid, PanelStatCard, PanelSection, PanelActionBar, PanelFilterBar, PanelDivider } from "@/components/PanelPage";
import EmailCampaignManager from "@/components/admin/EmailCampaignManager";
import EmailTemplateManager from "@/components/admin/EmailTemplateManager";
import EmailProviderConfigManager from "@/components/admin/EmailProviderConfigManager";
import EmailSuppressionManager from "@/components/admin/EmailSuppressionManager";
import { useToastStore } from "@/lib/toastStore";

type TabType = "overview" | "inbox" | "compose" | "campaigns" | "templates" | "provider" | "suppressions" | "dlp";

interface EmailThread {
  id: number;
  subject: string;
  sender: string;
  sender_email: string;
  recipients: string[];
  snippet: string;
  status: "sent" | "draft" | "scheduled" | "failed";
  read: boolean;
  created_at: string;
  has_attachments: boolean;
}

interface DlpViolation {
  id: number;
  violation_type: string;
  severity: string;
  sender_id: number | null;
  recipient_email: string | null;
  detected_content: string | null;
  action_taken: string;
  status: string;
  created_at: string | null;
}

const CAMPAIGN_STATUS_STYLES: Record<string, string> = {
  sent: "theme-chip-success",
  sending: "theme-chip-info",
  scheduled: "theme-chip-warning",
};

export default function AdminEmailPanel() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  const tabs = [
    { id: "overview" as TabType, name: "Overview", icon: BarChart3 },
    { id: "inbox" as TabType, name: "Inbox", icon: Inbox },
    { id: "compose" as TabType, name: "Compose", icon: Plus },
    { id: "campaigns" as TabType, name: "Campaigns", icon: Send },
    { id: "templates" as TabType, name: "Templates", icon: FileText },
    { id: "provider" as TabType, name: "Delivery Settings", icon: Mail },
    { id: "suppressions" as TabType, name: "Suppressions", icon: ShieldAlert },
    { id: "dlp" as TabType, name: "DLP Violations", icon: ShieldAlert },
  ];

  const [inboxEmails, setInboxEmails] = useState<EmailThread[]>([]);
  const [inboxLoading, setInboxLoading] = useState(false);
  const [showCompose, setShowCompose] = useState(false);
  const [composeTo, setComposeTo] = useState("");
  const [composeSubject, setComposeSubject] = useState("");
  const [composeBody, setComposeBody] = useState("");
  const [sending, setSending] = useState(false);
  const [dlpViolations, setDlpViolations] = useState<DlpViolation[]>([]);
  const [dlpLoading, setDlpLoading] = useState(false);

  const handleSend = async () => {
    if (!composeTo.trim() || !composeSubject.trim() || !composeBody.trim()) {
      addToast("Please fill in all fields", "error");
      return;
    }
    setSending(true);
    try {
      const recipientIds = composeTo.split(",").map((id) => parseInt(id.trim(), 10)).filter((id) => !Number.isNaN(id));
      if (recipientIds.length === 0) {
        addToast("Enter valid numeric employee IDs separated by commas", "error");
        return;
      }
      await apiFetch("/messaging/internal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: recipientIds, subject: composeSubject, body: composeBody }),
      });
      addToast("Email sent", "success");
      setComposeTo("");
      setComposeSubject("");
      setComposeBody("");
    } catch {
      addToast("Failed to send", "error");
    } finally {
      setSending(false);
    }
  };

  const loadInbox = useCallback(async () => {
    setInboxLoading(true);
    try {
      const res = await apiFetch("/email/inbox?folder=inbox&limit=50");
      if (res.ok) {
        const data = await parseJsonResponse(res);
        const items = data?.emails ?? data ?? [];
        setInboxEmails(items.map((e: any) => ({
          id: e.id,
          subject: e.subject ?? "(no subject)",
          sender: e.sender_name ?? `User #${e.sender_id}`,
          sender_email: "",
          recipients: [],
          snippet: e.body_preview ?? "",
          status: "sent",
          read: false,
          created_at: e.timestamp ?? e.created_at,
          has_attachments: false,
        })));
      }
    } catch { /* silent */ }
    setInboxLoading(false);
  }, []);

  const addToast = useToastStore((s) => s.addToast);

  const loadDlpViolations = useCallback(async () => {
    setDlpLoading(true);
    try {
      const res = await apiFetch("/email-gateway/dlp-violations?limit=50");
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setDlpViolations(data?.violations ?? []);
      }
    } catch { /* silent */ }
    setDlpLoading(false);
  }, []);

  return (
    <PanelContent className="space-y-4">
      <PanelTabs
        items={tabs.map((tab) => ({ key: tab.id, label: tab.name, icon: tab.icon }))}
        value={activeTab}
        onChange={setActiveTab}
      />
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.2 }}>
          {activeTab === "overview" && <EmailOverview onSelectTab={setActiveTab} onLoadInbox={loadInbox} />}
          {activeTab === "inbox" && <EmailInbox emails={inboxEmails} loading={inboxLoading} onLoad={loadInbox} />}
          {activeTab === "compose" && <EmailCompose
            to={composeTo} onToChange={setComposeTo}
            subject={composeSubject} onSubjectChange={setComposeSubject}
            body={composeBody} onBodyChange={setComposeBody}
            sending={sending} onSend={handleSend}
          />}
          {activeTab === "campaigns" && <EmailCampaignManager />}
          {activeTab === "templates" && <EmailTemplateManager />}
          {activeTab === "provider" && <EmailProviderConfigManager />}
          {activeTab === "suppressions" && <EmailSuppressionManager />}
          {activeTab === "dlp" && <DlpViolationsPanel violations={dlpViolations} loading={dlpLoading} onLoad={loadDlpViolations} />}
        </motion.div>
      </AnimatePresence>
    </PanelContent>
  );
}

function EmailOverview({ onSelectTab, onLoadInbox }: { onSelectTab: (tab: TabType) => void; onLoadInbox: () => void }) {
  return (
    <PanelSection className="space-y-4">
      <PanelGrid cols={4}>
        <PanelStatCard label="Inbox" value="24" icon={Inbox}
          description="Unread emails this week" onClick={() => onSelectTab("inbox")} />
        <PanelStatCard label="Sent Today" value="12" icon={Send}
          description="Emails sent today" />
        <PanelStatCard label="Drafts" value="3" icon={FileText}
          description="Unsaved drafts" onClick={() => onSelectTab("compose")} />
        <PanelStatCard label="Campaigns" value="5" icon={BarChart3}
          description="Active email campaigns" onClick={() => onSelectTab("campaigns")} />
      </PanelGrid>

      <PanelCard>
        <PanelCard.Header>Quick Actions</PanelCard.Header>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "Compose Email", tab: "compose" as TabType, icon: Plus, color: "text-primary" },
            { label: "View Inbox", tab: "inbox" as TabType, icon: Inbox, color: "text-info", action: onLoadInbox },
            { label: "New Campaign", tab: "campaigns" as TabType, icon: Send, color: "text-success" },
            { label: "Delivery Settings", tab: "provider" as TabType, icon: Mail, color: "text-warning" },
          ].map((item) => (
            <button key={item.label} onClick={() => { onSelectTab(item.tab); if ((item as any).action) (item as any).action(); }}
              className="flex items-center gap-3 p-3 rounded-xl bg-surface-1 hover:bg-surface-2
                transition-colors text-left group">
              <item.icon className={`w-4 h-4 ${item.color}`} />
              <span className="text-xs font-medium text-text flex-1">{item.label}</span>
              <ChevronRight className="w-3 h-3 text-text-muted group-hover:translate-x-0.5 transition-transform" />
            </button>
          ))}
        </div>
      </PanelCard>
    </PanelSection>
  );
}

function EmailInbox({ emails, loading, onLoad }: { emails: EmailThread[]; loading: boolean; onLoad: () => void }) {
  const [search, setSearch] = useState("");

  useEffect(() => { onLoad(); }, []);

  const filtered = search
    ? emails.filter((e) => e.subject.toLowerCase().includes(search.toLowerCase()) || e.sender.toLowerCase().includes(search.toLowerCase()))
    : emails;

  return (
    <PanelSection title="Inbox" icon={<Inbox className="w-4 h-4 text-primary" />}>
      <PanelFilterBar>
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-text-faint" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search emails..."
            className="w-full rounded-lg border border-border bg-surface pl-7 pr-2 py-1.5 text-xs text-text outline-none focus:border-primary/50" />
        </div>
        <PanelActionBar>
          <Button variant="ghost" size="sm" leftIcon={<RefreshCw className="h-3.5 w-3.5" />} onClick={onLoad}>Refresh</Button>
          <Button variant="primary" size="sm" leftIcon={<Plus className="h-3.5 w-3.5" />} onClick={() => {}}>New Email</Button>
        </PanelActionBar>
      </PanelFilterBar>

      {loading ? (
        <PanelCard className="text-center py-12">
          <RefreshCw className="w-8 h-8 text-text-muted/30 mx-auto mb-3 animate-spin" />
          <p className="text-text-muted font-medium">Loading inbox...</p>
        </PanelCard>
      ) : filtered.length === 0 ? (
        <PanelCard className="text-center py-12">
          <Mail className="w-10 h-10 text-text-muted/30 mx-auto mb-3" />
          <p className="text-text-muted font-medium">No emails found</p>
        </PanelCard>
      ) : (
        <div className="space-y-2">
          {filtered.map((email) => (
            <PanelCard key={email.id} className="p-3 cursor-pointer hover:bg-surface-2 transition-colors">
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold ${email.read ? "bg-primary/20 text-primary" : "bg-primary text-white"}`}>
                  {email.sender.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-semibold ${email.read ? "text-text-muted" : "text-text"}`}>{email.sender}</span>
                    <span className="text-[10px] text-text-faint">{new Date(email.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className={`text-xs ${email.read ? "text-text-muted" : "text-text font-medium"} truncate`}>{email.subject}</p>
                  <p className="text-[10px] text-text-faint truncate">{email.snippet}</p>
                </div>
                {email.has_attachments && <Paperclip className="h-3 w-3 text-text-faint shrink-0" />}
                {!email.read && <div className="w-2 h-2 bg-primary rounded-full shrink-0 mt-2" />}
              </div>
            </PanelCard>
          ))}
        </div>
      )}
    </PanelSection>
  );
}

interface DirectoryEntry {
  id: number;
  employee_code: string;
  full_name: string;
  email: string;
  department?: string;
  position?: string;
}

function EmailCompose({
  to, onToChange, subject, onSubjectChange, body, onBodyChange, sending, onSend
}: {
  to: string; onToChange: (v: string) => void;
  subject: string; onSubjectChange: (v: string) => void;
  body: string; onBodyChange: (v: string) => void;
  sending: boolean; onSend: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DirectoryEntry[]>([]);
  const [searching, setSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedRecipients, setSelectedRecipients] = useState<DirectoryEntry[]>([]);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await apiFetch(`/email-gateway/directory?search=${encodeURIComponent(searchQuery)}&limit=10`);
        if (res.ok) {
          const data = await parseJsonResponse(res);
          setSearchResults(Array.isArray(data) ? data : []);
          setShowResults(true);
        }
      } catch { /* silent */ }
      setSearching(false);
    }, 300);
  }, [searchQuery]);

  const addRecipient = (emp: DirectoryEntry) => {
    if (selectedRecipients.some((r) => r.id === emp.id)) return;
    const updated = [...selectedRecipients, emp];
    setSelectedRecipients(updated);
    onToChange(updated.map((r) => r.id).join(","));
    setSearchQuery("");
    setSearchResults([]);
    setShowResults(false);
  };

  const removeRecipient = (empId: number) => {
    const updated = selectedRecipients.filter((r) => r.id !== empId);
    setSelectedRecipients(updated);
    onToChange(updated.map((r) => r.id).join(","));
  };

  return (
    <PanelSection title="Compose Email" icon={<Send className="w-4 h-4 text-primary" />}>
      <div className="space-y-4 max-w-2xl">
        <div className="relative">
          <label className="block text-[10px] font-medium text-text-muted mb-1">To</label>
          <div className="flex flex-wrap gap-1 mb-1">
            {selectedRecipients.map((r) => (
              <span key={r.id} className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary text-[10px] px-2 py-0.5 font-medium">
                {r.full_name} <button onClick={() => removeRecipient(r.id)} className="hover:text-danger"><X className="h-2.5 w-2.5" /></button>
              </span>
            ))}
          </div>
          <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowResults(true)}
            placeholder={selectedRecipients.length === 0 ? "Search employees by name, email, or department..." : "Add more recipients..."}
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
          {searching && <RefreshCw className="absolute right-2 top-8 h-3 w-3 animate-spin text-text-faint" />}
          {showResults && searchResults.length > 0 && (
            <div className="absolute z-20 mt-1 w-full rounded-lg border border-border bg-surface shadow-xl max-h-48 overflow-y-auto">
              {searchResults.map((emp) => (
                <button key={emp.id} onClick={() => addRecipient(emp)}
                  className="w-full text-left px-3 py-2 hover:bg-surface-2 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-text font-medium">{emp.full_name}</span>
                    <span className="text-text-faint ml-2">{emp.department}</span>
                  </div>
                  <span className="text-text-faint text-[10px]">{emp.employee_code}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <div>
          <label className="block text-[10px] font-medium text-text-muted mb-1">Subject</label>
          <input type="text" value={subject} onChange={(e) => onSubjectChange(e.target.value)} placeholder="Email subject"
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
        </div>
        <div>
          <label className="block text-[10px] font-medium text-text-muted mb-1">Body</label>
          <textarea rows={8} value={body} onChange={(e) => onBodyChange(e.target.value)} placeholder="Compose your message..."
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text outline-none focus:border-primary/50 resize-none" />
        </div>
        <PanelActionBar>
          <Button variant="ghost" size="sm">Save Draft</Button>
          <Button variant="primary" size="sm" onClick={onSend} disabled={sending || selectedRecipients.length === 0}>
            {sending ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
            Send Email
          </Button>
        </PanelActionBar>
      </div>
    </PanelSection>
  );
}

function DlpViolationsPanel({ violations, loading, onLoad }: { violations: DlpViolation[]; loading: boolean; onLoad: () => void }) {
  useEffect(() => { onLoad(); }, []);

  return (
    <PanelSection title="DLP Violations" description="Data Loss Prevention alerts for outbound emails"
      icon={<ShieldAlert className="w-4 h-4 text-danger" />}
      action={
        <PanelActionBar>
          <Button variant="ghost" size="sm" leftIcon={<RefreshCw className="h-3.5 w-3.5" />} onClick={onLoad}>Refresh</Button>
        </PanelActionBar>
      }>
      {loading ? (
        <PanelCard className="text-center py-12">
          <RefreshCw className="w-8 h-8 text-text-muted/30 mx-auto mb-3 animate-spin" />
          <p className="text-text-muted font-medium">Loading DLP violations...</p>
        </PanelCard>
      ) : violations.length === 0 ? (
        <PanelCard className="text-center py-12">
          <ShieldAlert className="w-10 h-10 text-text-muted/30 mx-auto mb-3" />
          <p className="text-text-muted font-medium">No DLP violations</p>
          <p className="text-xs text-text-faint mt-1">All outbound emails have passed DLP scanning</p>
        </PanelCard>
      ) : (
        <div className="space-y-2">
          {violations.map((v) => (
            <PanelCard key={v.id} className="p-3">
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                  v.severity === "high" ? "bg-danger/20 text-danger" : v.severity === "medium" ? "bg-warning/20 text-warning" : "bg-info/20 text-info"
                }`}>
                  {v.severity.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text capitalize">{v.violation_type.replace("_", " ")}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      v.status === "pending" ? "bg-warning/10 text-warning" : "bg-success/10 text-success"
                    }`}>{v.status}</span>
                  </div>
                  <p className="text-xs text-text-muted mt-1">To: {v.recipient_email || "N/A"} {v.detected_content ? `· Subject: ${v.detected_content}` : ""}</p>
                  <p className="text-[10px] text-text-faint mt-0.5">
                    {v.created_at ? new Date(v.created_at).toLocaleString() : ""}
                    {v.sender_id ? ` · Sender ID: ${v.sender_id}` : ""}
                  </p>
                </div>
              </div>
            </PanelCard>
          ))}
        </div>
      )}
    </PanelSection>
  );
}
