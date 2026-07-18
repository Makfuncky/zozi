/**
 * Admin Email Management — React Native
 * Full email campaign management matching web_app admin email section.
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Modal,
  StyleSheet,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { BackgroundJob, trackBackgroundJob } from "@/lib/backgroundJobs";
import { buildAdminEmailCampaignPayload } from "@/lib/adminManagementUtils";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";
import { toast } from "@/lib/toastStore";
import { canAccessAdminEmailManagement } from "@shared/adminPermissions";
import { Ionicons } from "@expo/vector-icons";

interface EmailCampaign {
  id: number;
  subject: string;
  status: "draft" | "sent" | "scheduled";
  recipient_count?: number;
  sent_at?: string;
  created_at: string;
}

interface CampaignAnalytics {
  total_recipients: number;
  sent_count: number;
  opened_count: number;
  open_rate: number;
  clicked_count: number;
  click_rate: number;
  bounced_count: number;
  bounce_rate: number;
  unsubscribed_count: number;
  unsubscribe_rate: number;
}

interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  text_content?: string | null;
}

type Tab = "campaigns" | "newsletter" | "compose" | "templates" | "settings";

export default function AdminEmailDashboard() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminEmailManagement(user?.role);

  const [tab, setTab] = useState<Tab>("campaigns");
  const [campaigns, setCampaigns] = useState<EmailCampaign[]>([]);
  const [loading, setLoading] = useState(true);

  // Compose form
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [recipientType, setRecipientType] = useState<"all" | "newsletter" | "customers">("newsletter");
  const [sending, setSending] = useState(false);

  // Newsletter stats
  const [subscriberCount, setSubscriberCount] = useState<number>(0);

  // Analytics modal
  const [analyticsVisible, setAnalyticsVisible] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<EmailCampaign | null>(null);
  const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null);
  const [sendingId, setSendingId] = useState<number | null>(null);

  // Templates for compose tab
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);

  // Templates management state
  const [newTplName, setNewTplName] = useState("");
  const [newTplSubject, setNewTplSubject] = useState("");
  const [newTplBody, setNewTplBody] = useState("");
  const [tplSaving, setTplSaving] = useState(false);
  const [deletingTplId, setDeletingTplId] = useState<number | null>(null);

  // Settings state
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [providerForm, setProviderForm] = useState({
    provider: "environment" as string,
    email_from_default: "",
    resend_api_key: "",
  });

  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<EmailCampaign[]>("/email/campaigns").catch(() => []);
      setCampaigns(Array.isArray(data) ? data : []);
    } catch {}
    setLoading(false);
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const data = await apiFetch<EmailTemplate[]>("/email/templates").catch(() => []);
      setTemplates(Array.isArray(data) ? data : []);
    } catch {}
  }, []);

  const loadNewsletterStats = useCallback(async () => {
    try {
      const data = await apiFetch<{ count: number }>("/email/newsletter/subscribers/count").catch(() => ({ count: 0 }));
      setSubscriberCount((data as any)?.count ?? 0);
    } catch {}
  }, []);

  const loadProviderConfig = useCallback(async () => {
    setSettingsLoading(true);
    try {
      const data = await apiFetch<any>("/email/config/runtime").catch(() => null);
      if (data) {
        setProviderForm({
          provider: data.provider ?? "environment",
          email_from_default: data.email_from_default ?? "",
          resend_api_key: "",
        });
      }
    } catch {}
    setSettingsLoading(false);
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!canAccess) {
      setLoading(false);
      return;
    }
    loadCampaigns();
    loadNewsletterStats();
    loadTemplates();
  }, [canAccess]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (tab === "settings" && canAccess) loadProviderConfig();
  }, [tab]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!canAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: "Email Management" }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  const openAnalytics = async (campaign: EmailCampaign) => {
    setSelectedCampaign(campaign);
    setAnalytics(null);
    setAnalyticsVisible(true);
    setAnalyticsLoading(true);
    try {
      const data = await apiFetch<CampaignAnalytics>(`/email/campaigns/${campaign.id}/analytics`);
      setAnalytics(data);
    } catch {
      setAnalytics(null);
    }
    setAnalyticsLoading(false);
  };

  const sendExistingCampaign = async (id: number) => {
    Alert.alert(
      "Send Campaign",
      "Send this campaign now to all recipients?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Send",
          style: "destructive",
          onPress: async () => {
            setSendingId(id);
            try {
              const job = await apiFetch<BackgroundJob<{ recipient_count?: number }>>(`/email/campaigns/${id}/send`, { method: "POST" });
              void trackBackgroundJob(job, {
                label: "Email campaign send",
                description: `Campaign #${id}`,
                route: "/admin/email",
                queuedToast: `Queued campaign #${id} for delivery`,
                successToast: (finalJob) => {
                  const recipients = typeof finalJob.result?.recipient_count === "number" ? finalJob.result.recipient_count : 0;
                  return recipients > 0
                    ? `Campaign #${id} sent to ${recipients.toLocaleString()} recipients`
                    : `Campaign #${id} sent successfully`;
                },
                errorToast: false,
              }).then(() => loadCampaigns()).catch((error) => {
                const message = error instanceof Error ? error.message : "Failed to send campaign.";
                toast.error(message);
              });
              toast.info(`Campaign #${id} is running in the background.`);
              loadCampaigns();
            } catch {
              Alert.alert("Error", "Failed to send campaign.");
            }
            setSendingId(null);
          },
        },
      ]
    );
  };

  const sendEmail = async () => {
    if (!subject.trim() || !body.trim()) {
      Alert.alert("Error", "Subject and body are required.");
      return;
    }
    setSending(true);
    try {
      const created = await apiFetch<EmailCampaign>("/email/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildAdminEmailCampaignPayload(subject, body, recipientType)),
      });
      const job = await apiFetch<BackgroundJob<{ recipient_count?: number }>>(`/email/campaigns/${created.id}/send`, {
        method: "POST",
      });
      void trackBackgroundJob(job, {
        label: "Email campaign send",
        description: subject.trim(),
        route: "/admin/email",
        queuedToast: `Queued ${subject.trim()} for delivery`,
        successToast: (finalJob) => {
          const recipients = typeof finalJob.result?.recipient_count === "number" ? finalJob.result.recipient_count : 0;
          return recipients > 0
            ? `${subject.trim()} sent to ${recipients.toLocaleString()} recipients`
            : `${subject.trim()} sent successfully`;
        },
        errorToast: false,
      }).then(() => loadCampaigns()).catch((error) => {
        const message = error instanceof Error ? error.message : "Failed to send email.";
        toast.error(message);
      });
      toast.info(`Queued ${subject.trim()} in the background.`);
      setSubject("");
      setBody("");
      setTab("campaigns");
      loadCampaigns();
    } catch {
      Alert.alert("Error", "Failed to send email. Please try again.");
    }
    setSending(false);
  };

  const TABS: { key: Tab; label: string }[] = [
    { key: "campaigns", label: "Campaigns" },
    { key: "newsletter", label: "Newsletter" },
    { key: "compose", label: "✉ Compose" },
    { key: "templates", label: "Templates" },
    { key: "settings", label: "⚙ Settings" },
  ];

  const statusColor: Record<string, string> = {
    sent: "#22c55e",
    scheduled: "#f59e0b",
    draft: "#9ca3af",
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Email Management" }} />

      {/* Tab bar */}
      <View style={{ flexDirection: "row", borderBottomWidth: 1, borderColor: theme.colors.border }}>
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.key}
            onPress={() => setTab(t.key)}
            style={[
              styles.tab,
              tab === t.key
                ? { borderBottomWidth: 2, borderColor: theme.colors.brand }
                : {},
            ]}
          >
            <Text
              style={{
                color: tab === t.key ? theme.colors.brand : theme.colors.textMuted,
                fontWeight: tab === t.key ? "700" : "500",
                fontSize: 13,
              }}
            >
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
        {/* ─── CAMPAIGNS ─── */}
        {tab === "campaigns" && (
          <>
            <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 12 }]}>
              Email Campaigns
            </Text>
            {loading ? (
              <ActivityIndicator color={theme.colors.brand} />
            ) : campaigns.length === 0 ? (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 16 }]}>
                  No campaigns yet. Use Compose to send your first email.
                </Text>
              </View>
            ) : (
              campaigns.map((c) => (
                <TouchableOpacity
                  key={c.id}
                  onPress={() => openAnalytics(c)}
                  activeOpacity={0.75}
                  style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
                >
                  <Text style={[s.text, { fontWeight: "700", fontSize: 14 }]} numberOfLines={2}>
                    {c.subject}
                  </Text>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginTop: 6 }}>
                    <View
                      style={{
                        backgroundColor: statusColor[c.status] + "22",
                        borderRadius: 6,
                        paddingHorizontal: 8,
                        paddingVertical: 2,
                      }}
                    >
                      <Text style={{ color: statusColor[c.status], fontSize: 11, fontWeight: "700" }}>
                        {c.status.toUpperCase()}
                      </Text>
                    </View>
                    {c.recipient_count !== undefined && (
                      <Text style={[s.textMuted, { fontSize: 11 }]}>{c.recipient_count} recipients</Text>
                    )}
                  </View>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                    <Text style={[s.textMuted, { fontSize: 11 }]}>
                      {c.sent_at
                        ? `Sent ${c.sent_at.slice(0, 10)}`
                        : `Created ${c.created_at.slice(0, 10)}`}
                    </Text>
                    <View style={{ flexDirection: "row", gap: 6 }}>
                      {c.status !== "sent" && (
                        <TouchableOpacity
                          onPress={(e) => { e.stopPropagation?.(); sendExistingCampaign(c.id); }}
                          style={{
                            backgroundColor: theme.colors.brand,
                            borderRadius: 8,
                            paddingHorizontal: 10,
                            paddingVertical: 4,
                          }}
                        >
                          {sendingId === c.id ? (
                            <ActivityIndicator size="small" color="#fff" />
                          ) : (
                            <Text style={{ color: "#fff", fontSize: 11, fontWeight: "700" }}>Send ▶</Text>
                          )}
                        </TouchableOpacity>
                      )}
                      <TouchableOpacity
                        onPress={() => openAnalytics(c)}
                        style={{
                          backgroundColor: theme.colors.surface2,
                          borderRadius: 8,
                          paddingHorizontal: 10,
                          paddingVertical: 4,
                          borderWidth: 1,
                          borderColor: theme.colors.border,
                        }}
                      >
                        <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="bar-chart-outline" size={11} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.textMuted, fontSize: 11, fontWeight: "600" }}>Stats</Text></View>
                      </TouchableOpacity>
                    </View>
                  </View>
                </TouchableOpacity>
              ))
            )}
          </>
        )}

        {/* ─── NEWSLETTER ─── */}
        {tab === "newsletter" && (
          <>
            <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 12 }]}>
              Newsletter Subscribers
            </Text>
            <View
              style={[
                styles.card,
                { backgroundColor: theme.colors.brand + "18", borderColor: theme.colors.brand + "40" },
              ]}
            >
              <Text style={{ color: theme.colors.brand, fontSize: 40, fontWeight: "800", textAlign: "center" }}>
                {subscriberCount.toLocaleString()}
              </Text>
              <Text style={[s.textMuted, { textAlign: "center", marginTop: 4 }]}>
                Active newsletter subscribers
              </Text>
            </View>
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "700", marginBottom: 8 }]}>Quick Actions</Text>
              <TouchableOpacity
                onPress={() => setTab("compose")}
                style={[styles.btn, { backgroundColor: theme.colors.brand }]}
              >
                <Text style={{ color: "#fff", fontWeight: "700", textAlign: "center" }}>
                  ✉ Send Newsletter
                </Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        {/* ─── COMPOSE ─── */}
        {tab === "compose" && (
          <>
            <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 12 }]}>
              Compose Email
            </Text>

            {/* Template picker */}
            {templates.length > 0 && (
              <>
                <Text style={[s.textMuted, { fontSize: 12, marginBottom: 6 }]}>Template (optional):</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
                  <View style={{ flexDirection: "row", gap: 8 }}>
                    <TouchableOpacity
                      onPress={() => { setSelectedTemplateId(null); }}
                      style={[
                        styles.chip,
                        selectedTemplateId === null
                          ? { backgroundColor: theme.colors.brand }
                          : { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, borderWidth: 1 },
                      ]}
                    >
                      <Text style={{ color: selectedTemplateId === null ? "#fff" : theme.colors.textMuted, fontSize: 12, fontWeight: "600" }}>
                        None
                      </Text>
                    </TouchableOpacity>
                    {templates.map((t) => (
                      <TouchableOpacity
                        key={t.id}
                        onPress={() => {
                          setSelectedTemplateId(t.id);
                          setSubject(t.subject);
                          if (t.text_content) setBody(t.text_content);
                        }}
                        style={[
                          styles.chip,
                          selectedTemplateId === t.id
                            ? { backgroundColor: theme.colors.brand }
                            : { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, borderWidth: 1 },
                        ]}
                      >
                        <Text style={{ color: selectedTemplateId === t.id ? "#fff" : theme.colors.textMuted, fontSize: 12, fontWeight: "600" }}>
                          {t.name}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </ScrollView>
              </>
            )}

            {/* Recipient type */}
            <Text style={[s.textMuted, { fontSize: 12, marginBottom: 6 }]}>Send to:</Text>
            <View style={{ flexDirection: "row", gap: 8, marginBottom: 12 }}>
              {(["newsletter", "customers", "all"] as const).map((r) => (
                <TouchableOpacity
                  key={r}
                  onPress={() => setRecipientType(r)}
                  style={[
                    styles.chip,
                    recipientType === r
                      ? { backgroundColor: theme.colors.brand }
                      : { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, borderWidth: 1 },
                  ]}
                >
                  <Text
                    style={{
                      color: recipientType === r ? "#fff" : theme.colors.textMuted,
                      fontSize: 12,
                      fontWeight: "600",
                      textTransform: "capitalize",
                    }}
                  >
                    {r === "all" ? "Everyone" : r}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Subject:</Text>
            <TextInput
              value={subject}
              onChangeText={setSubject}
              placeholder="Email subject line…"
              placeholderTextColor={theme.colors.textMuted}
              style={[s.input, { marginBottom: 12 }]}
            />

            <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Message:</Text>
            <TextInput
              value={body}
              onChangeText={setBody}
              placeholder="Email body (plain text or HTML)…"
              placeholderTextColor={theme.colors.textMuted}
              multiline
              numberOfLines={8}
              textAlignVertical="top"
              style={[s.input, { height: 160, marginBottom: 16 }]}
            />

            <TouchableOpacity
              onPress={sendEmail}
              disabled={sending || !subject.trim() || !body.trim()}
              style={[
                styles.btn,
                { backgroundColor: sending ? theme.colors.surface2 : theme.colors.brand },
              ]}
            >
              {sending ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={{ color: "#fff", fontWeight: "700", textAlign: "center", fontSize: 15 }}>
                  Send Email Campaign
                </Text>
              )}
            </TouchableOpacity>
          </>
        )}

        {/* ─── TEMPLATES ─── */}
        {tab === "templates" && (
          <>
            <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 12 }]}>
              Email Templates
            </Text>

            {/* Existing templates */}
            {templates.length === 0 ? (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 8 }]}>No templates yet.</Text>
              </View>
            ) : (
              templates.map((t) => (
                <View
                  key={t.id}
                  style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, flexDirection: "row", alignItems: "center" }]}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]}>{t.name}</Text>
                    <Text style={[s.textMuted, { fontSize: 11, marginTop: 2 }]} numberOfLines={1}>
                      {t.subject}
                    </Text>
                  </View>
                  <TouchableOpacity
                    onPress={() =>
                      Alert.alert("Delete Template", `Delete "${t.name}"?`, [
                        { text: "Cancel", style: "cancel" },
                        {
                          text: "Delete",
                          style: "destructive",
                          onPress: async () => {
                            setDeletingTplId(t.id);
                            try {
                              await apiFetch(`/email/templates/${t.id}`, { method: "DELETE" });
                              setTemplates((prev) => prev.filter((x) => x.id !== t.id));
                              toast.success("Template deleted");
                            } catch {
                              toast.error("Failed to delete template");
                            }
                            setDeletingTplId(null);
                          },
                        },
                      ])
                    }
                    disabled={deletingTplId === t.id}
                    style={{
                      backgroundColor: "#ef444418",
                      borderRadius: 8,
                      paddingHorizontal: 10,
                      paddingVertical: 5,
                      borderWidth: 1,
                      borderColor: "#ef444440",
                    }}
                  >
                    {deletingTplId === t.id ? (
                      <ActivityIndicator size="small" color="#ef4444" />
                    ) : (
                      <Text style={{ color: "#ef4444", fontSize: 11, fontWeight: "700" }}>Delete</Text>
                    )}
                  </TouchableOpacity>
                </View>
              ))
            )}

            {/* Create new template */}
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginTop: 12 }]}>
              <Text style={[s.text, { fontWeight: "700", marginBottom: 10 }]}>New Template</Text>
              <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Name:</Text>
              <TextInput
                value={newTplName}
                onChangeText={setNewTplName}
                placeholder="Template name…"
                placeholderTextColor={theme.colors.textMuted}
                style={[s.input, { marginBottom: 10 }]}
              />
              <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Subject:</Text>
              <TextInput
                value={newTplSubject}
                onChangeText={setNewTplSubject}
                placeholder="Email subject…"
                placeholderTextColor={theme.colors.textMuted}
                style={[s.input, { marginBottom: 10 }]}
              />
              <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Body:</Text>
              <TextInput
                value={newTplBody}
                onChangeText={setNewTplBody}
                placeholder="HTML or plain text body…"
                placeholderTextColor={theme.colors.textMuted}
                multiline
                numberOfLines={5}
                textAlignVertical="top"
                style={[s.input, { height: 100, marginBottom: 12 }]}
              />
              <TouchableOpacity
                onPress={async () => {
                  if (!newTplName.trim() || !newTplSubject.trim()) {
                    Alert.alert("Error", "Name and subject are required.");
                    return;
                  }
                  setTplSaving(true);
                  try {
                    const created = await apiFetch<EmailTemplate>("/email/templates", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ name: newTplName.trim(), subject: newTplSubject.trim(), html_content: newTplBody.trim() || undefined }),
                    });
                    setTemplates((prev) => [...prev, created]);
                    setNewTplName("");
                    setNewTplSubject("");
                    setNewTplBody("");
                    toast.success("Template created");
                  } catch {
                    toast.error("Failed to create template");
                  }
                  setTplSaving(false);
                }}
                disabled={tplSaving || !newTplName.trim() || !newTplSubject.trim()}
                style={[styles.btn, { backgroundColor: tplSaving ? theme.colors.surface2 : theme.colors.brand }]}
              >
                {tplSaving ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={{ color: "#fff", fontWeight: "700", textAlign: "center" }}>
                    Save Template
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </>
        )}

        {/* ─── SETTINGS ─── */}
        {tab === "settings" && (
          <>
            <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 12 }]}>
              Delivery Settings
            </Text>

            {settingsLoading ? (
              <ActivityIndicator color={theme.colors.brand} style={{ marginVertical: 32 }} />
            ) : (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <Text style={[s.text, { fontWeight: "700", marginBottom: 10 }]}>Provider</Text>
                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
                  {(["environment", "resend", "smtp", "disabled"] as const).map((p) => (
                    <TouchableOpacity
                      key={p}
                      onPress={() => setProviderForm((f) => ({ ...f, provider: p }))}
                      style={[
                        styles.chip,
                        providerForm.provider === p
                          ? { backgroundColor: theme.colors.brand }
                          : { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, borderWidth: 1 },
                      ]}
                    >
                      <Text
                        style={{
                          color: providerForm.provider === p ? "#fff" : theme.colors.textMuted,
                          fontSize: 12,
                          fontWeight: "600",
                          textTransform: "capitalize",
                        }}
                      >
                        {p}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                {providerForm.provider === "resend" && (
                  <>
                    <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Resend API Key:</Text>
                    <TextInput
                      value={providerForm.resend_api_key}
                      onChangeText={(v) => setProviderForm((f) => ({ ...f, resend_api_key: v }))}
                      placeholder="re_xxxxxxxxxxxxxxxx"
                      placeholderTextColor={theme.colors.textMuted}
                      secureTextEntry
                      style={[s.input, { marginBottom: 12 }]}
                    />
                  </>
                )}

                <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>Default From Address:</Text>
                <TextInput
                  value={providerForm.email_from_default}
                  onChangeText={(v) => setProviderForm((f) => ({ ...f, email_from_default: v }))}
                  placeholder="donotreply@zozi.com"
                  placeholderTextColor={theme.colors.textMuted}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  style={[s.input, { marginBottom: 16 }]}
                />

                <TouchableOpacity
                  onPress={async () => {
                    setSettingsSaving(true);
                    try {
                      const payload: Record<string, unknown> = { provider: providerForm.provider };
                      if (providerForm.email_from_default.trim()) payload.email_from_default = providerForm.email_from_default.trim();
                      if (providerForm.resend_api_key.trim()) payload.resend_api_key = providerForm.resend_api_key.trim();
                      await apiFetch("/email/config/runtime", {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                      });
                      toast.success("Email settings saved");
                      setProviderForm((f) => ({ ...f, resend_api_key: "" }));
                    } catch {
                      toast.error("Failed to save settings");
                    }
                    setSettingsSaving(false);
                  }}
                  disabled={settingsSaving}
                  style={[styles.btn, { backgroundColor: settingsSaving ? theme.colors.surface2 : theme.colors.brand }]}
                >
                  {settingsSaving ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={{ color: "#fff", fontWeight: "700", textAlign: "center" }}>
                      Save Settings
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            )}
          </>
        )}
      </ScrollView>

      {/* ─── Analytics Modal ─── */}
      <Modal
        visible={analyticsVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setAnalyticsVisible(false)}
      >
        <View style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.5)", justifyContent: "flex-end" }}>
          <View
            style={{
              backgroundColor: theme.colors.surface0,
              borderTopLeftRadius: 24,
              borderTopRightRadius: 24,
              padding: 24,
              paddingBottom: 40,
            }}
          >
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <Text style={[s.text, { fontWeight: "800", fontSize: 15, flex: 1, marginRight: 8 }]} numberOfLines={2}>
                {selectedCampaign?.subject}
              </Text>
              <TouchableOpacity onPress={() => setAnalyticsVisible(false)}>
                <Ionicons name="close-outline" size={20} color={theme.colors.textMuted} />
              </TouchableOpacity>
            </View>

            {analyticsLoading ? (
              <ActivityIndicator color={theme.colors.brand} style={{ marginVertical: 24 }} />
            ) : analytics ? (
              <View style={{ gap: 10 }}>
                <View style={{ flexDirection: "row", gap: 10 }}>
                  <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                    <Text style={[s.textMuted, { fontSize: 11, marginBottom: 2 }]}>Sent</Text>
                    <Text style={[s.text, { fontSize: 22, fontWeight: "800" }]}>{analytics.sent_count}</Text>
                    <Text style={[s.textMuted, { fontSize: 10 }]}>of {analytics.total_recipients}</Text>
                  </View>
                  <View style={[styles.statCard, { backgroundColor: "#22c55e18", borderColor: "#22c55e40" }]}>
                    <Text style={{ color: "#22c55e", fontSize: 11, marginBottom: 2, fontWeight: "600" }}>Opened</Text>
                    <Text style={{ color: "#22c55e", fontSize: 22, fontWeight: "800" }}>{analytics.opened_count}</Text>
                    <Text style={{ color: "#22c55e", fontSize: 10 }}>{(analytics.open_rate * 100).toFixed(1)}% rate</Text>
                  </View>
                </View>
                <View style={{ flexDirection: "row", gap: 10 }}>
                  <View style={[styles.statCard, { backgroundColor: "#3b82f618", borderColor: "#3b82f640" }]}>
                    <Text style={{ color: "#3b82f6", fontSize: 11, marginBottom: 2, fontWeight: "600" }}>Clicked</Text>
                    <Text style={{ color: "#3b82f6", fontSize: 22, fontWeight: "800" }}>{analytics.clicked_count}</Text>
                    <Text style={{ color: "#3b82f6", fontSize: 10 }}>{(analytics.click_rate * 100).toFixed(1)}% rate</Text>
                  </View>
                  <View style={[styles.statCard, { backgroundColor: "#f59e0b18", borderColor: "#f59e0b40" }]}>
                    <Text style={{ color: "#f59e0b", fontSize: 11, marginBottom: 2, fontWeight: "600" }}>Bounced</Text>
                    <Text style={{ color: "#f59e0b", fontSize: 22, fontWeight: "800" }}>{analytics.bounced_count}</Text>
                    <Text style={{ color: "#f59e0b", fontSize: 10 }}>{(analytics.bounce_rate * 100).toFixed(1)}% rate</Text>
                  </View>
                </View>
                <View style={[styles.statCard, { backgroundColor: "#ef444418", borderColor: "#ef444440" }]}>
                  <Text style={{ color: "#ef4444", fontSize: 11, marginBottom: 2, fontWeight: "600" }}>Unsubscribed</Text>
                  <Text style={{ color: "#ef4444", fontSize: 22, fontWeight: "800" }}>{analytics.unsubscribed_count}</Text>
                  <Text style={{ color: "#ef4444", fontSize: 10 }}>{(analytics.unsubscribe_rate * 100).toFixed(1)}% rate</Text>
                </View>
              </View>
            ) : (
              <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 16 }]}>
                No analytics available for this campaign yet.
              </Text>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  tab: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 12,
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
  },
  btn: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  statCard: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
  },
  chip: {
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
});
