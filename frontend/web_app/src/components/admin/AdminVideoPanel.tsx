"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Video, Phone, Users, Clock, Lock,
  Plus, Loader2, X, Copy, CheckCircle,
  AlertCircle, Shield, Calendar, Play,
  Trash2, Edit3, Download, FileText,
  Mic, Square,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { PanelContent, PanelLoadingState, PanelTabs, PanelCard, PanelGrid, PanelSection, PanelStatCard, PanelActionBar, PanelFilterBar, PanelDivider, PanelBreadcrumb } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { Button } from "@/components/ui/Button";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";

interface VideoRoom {
  id: number;
  name: string;
  room_uuid: string;
  room_id?: string;
  purpose: string;
  status: string;
  created_at: string;
  max_participants: number;
  invite_link?: string;
  started_at?: string;
  ended_at?: string;
  recording_enabled?: boolean;
  transcription_enabled?: boolean;
  country_code?: string;
}

interface TranscriptSegment {
  speaker_id: number;
  content: string;
  timestamp: string;
  language?: string;
}

interface TranscriptData {
  meeting_id: string;
  segments: TranscriptSegment[];
  action_items: { entity_type: string; entity_id: number; action: string; status: string }[];
  summary: string;
  word_count: number;
}

export default function AdminVideoPanel() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuth();
  const addToast = useToastStore((s) => s.addToast);

  const { selectedCountry, assignedCountries, isGlobalView } = useAdminCountry();
  const countryCode = isGlobalView
    ? (assignedCountries[0]?.code || selectedCountry?.code || "AE")
    : (selectedCountry?.code || "AE");

  const [loading, setLoading] = useState(true);
  const [rooms, setRooms] = useState<VideoRoom[]>([]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [newRoomName, setNewRoomName] = useState("");
  const [newRoomPurpose, setNewRoomPurpose] = useState("meeting");
  const [newRoomParticipants, setNewRoomParticipants] = useState("10");
  const [creatingRoom, setCreatingRoom] = useState(false);
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [recordingRoomId, setRecordingRoomId] = useState<string | null>(null);
  const [transcriptRoomId, setTranscriptRoomId] = useState<string | null>(null);
  const [transcriptData, setTranscriptData] = useState<TranscriptData | null>(null);
  const [transcriptLoading, setTranscriptLoading] = useState(false);

  const loadRooms = useCallback(async () => {
    try {
      const res = await apiFetch("/admin/video/rooms");
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setRooms(Array.isArray(data) ? data : []);
      }
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) return;
    loadRooms();
  }, [loadRooms, user?.role]);

  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return;
    setCreatingRoom(true);
    try {
      const body = { name: newRoomName.trim(), purpose: newRoomPurpose, max_participants: parseInt(newRoomParticipants) || 10, created_by: user?.id };
      const res = await apiFetch(`/admin/video/rooms/${countryCode}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (res.ok) {
        addToast("Video room created", "success");
        setShowCreateModal(false);
        setNewRoomName("");
        setNewRoomPurpose("meeting");
        setNewRoomParticipants("10");
        loadRooms();
      } else {
        const err = await parseJsonResponse(res);
        addToast(err?.detail ?? "Failed to create room", "error");
      }
    } catch { addToast("Network error", "error"); }
    finally { setCreatingRoom(false); }
  };

  const handleSchedule = async () => {
    if (!newRoomName.trim() || !scheduledDate || !scheduledTime) return;
    setCreatingRoom(true);
    try {
      const body = { name: newRoomName.trim(), purpose: newRoomPurpose, max_participants: parseInt(newRoomParticipants) || 10, created_by: user?.id, scheduled_for: `${scheduledDate}T${scheduledTime}:00Z` };
      const res = await apiFetch(`/admin/video/rooms/${countryCode}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (res.ok) {
        addToast("Video room scheduled", "success");
        setShowScheduleModal(false);
        setNewRoomName("");
        setScheduledDate("");
        setScheduledTime("");
        loadRooms();
      }
    } catch { addToast("Failed to schedule", "error"); }
    finally { setCreatingRoom(false); }
  };

  const handleCopyLink = async (link: string) => {
    try { await navigator.clipboard.writeText(window.location.origin + link); addToast("Link copied", "success"); } catch { addToast("Failed to copy", "error"); }
  };

  const handleStartRecording = async (room: VideoRoom) => {
    setRecordingRoomId(room.room_id ?? room.room_uuid);
    try {
      const res = await apiFetch(`/admin/video/rooms/${room.room_id ?? room.room_uuid}/recording/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ employee_id: user?.id }),
      });
      if (res.ok) {
        addToast("Recording started", "success");
        loadRooms();
      } else {
        addToast("Failed to start recording", "error");
      }
    } catch { addToast("Network error", "error"); }
    finally { setRecordingRoomId(null); }
  };

  const handleStopRecording = async (room: VideoRoom) => {
    setRecordingRoomId(room.room_id ?? room.room_uuid);
    try {
      const res = await apiFetch(`/admin/video/rooms/${room.room_id ?? room.room_uuid}/recording/end`, {
        method: "POST",
      });
      if (res.ok) {
        addToast("Recording stopped", "success");
        loadRooms();
      } else {
        addToast("Failed to stop recording", "error");
      }
    } catch { addToast("Network error", "error"); }
    finally { setRecordingRoomId(null); }
  };

  const handleViewTranscript = async (room: VideoRoom) => {
    setTranscriptLoading(true);
    setTranscriptRoomId(room.room_id ?? room.room_uuid);
    try {
      const res = await apiFetch(`/admin/video/rooms/${room.room_id ?? room.room_uuid}/transcript`);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setTranscriptData(data);
      } else {
        addToast("No transcript available", "error");
        setTranscriptData(null);
      }
    } catch { addToast("Network error", "error"); }
    finally { setTranscriptLoading(false); }
  };

  const handleCloseTranscript = () => {
    setTranscriptRoomId(null);
    setTranscriptData(null);
  };

  const activeRooms = rooms.filter((r) => r.status === "active");
  const scheduledRooms = rooms.filter((r) => r.status === "scheduled" || r.status === "waiting");

  return (
    <PanelContent width="full" className="space-y-4">
      <PanelBreadcrumb items={[
        { label: "Communication", href: "/admin/communication" },
        { label: "Video", href: "/admin/video" },
      ]} />

      {/* Metrics */}
      <PanelGrid cols={4}>
        <PanelStatCard label="Total Rooms" value={rooms.length} icon={Video} />
        <PanelStatCard label="Active" value={activeRooms.length} icon={Play} color="from-success/20 to-emerald-500/20" />
        <PanelStatCard label="Scheduled" value={scheduledRooms.length} icon={Calendar} color="from-warning/20 to-amber-500/20" />
        <PanelStatCard label="Max Participants" value={Math.max(...rooms.map((r) => r.max_participants), 0)} icon={Users} color="from-info/20 to-blue-500/20" />
      </PanelGrid>

      <PanelSection title="Video Rooms" description="Create and manage secure video meeting rooms"
        action={
          <PanelActionBar>
            <Button variant="ghost" size="sm" onClick={() => setShowScheduleModal(true)} leftIcon={<Calendar className="h-3.5 w-3.5" />}>Schedule</Button>
            <Button variant="primary" size="sm" onClick={() => setShowCreateModal(true)} leftIcon={<Plus className="h-3.5 w-3.5" />}>Create Room</Button>
          </PanelActionBar>
        }>
        {rooms.length === 0 && !loading ? (
          <PanelCard className="text-center py-12">
            <Video className="w-12 h-12 text-text-muted/30 mx-auto mb-3" />
            <p className="text-text-muted font-medium">No video rooms created yet</p>
            <p className="text-xs text-text-faint mt-1">Create a room to start a video conference</p>
          </PanelCard>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {rooms.map((room) => (
              <PanelCard key={room.id} className="p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Video className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-text">{room.name}</h3>
                      <p className="text-[10px] text-text-muted capitalize">{room.purpose} room</p>
                    </div>
                  </div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-semibold ${
                    room.status === "active" ? "bg-success/10 text-success" : room.status === "scheduled" ? "bg-warning/10 text-warning" : "bg-surface-3 text-text-muted"
                  }`}>{room.status ?? "active"}</span>
                </div>

                {room.started_at && (
                  <div className="flex items-center gap-2 text-[10px] text-text-faint">
                    <Clock className="h-3 w-3" />
                    Started: {new Date(room.started_at).toLocaleString()}
                    {room.ended_at && <span>· Ended: {new Date(room.ended_at).toLocaleString()}</span>}
                  </div>
                )}

                <div className="flex items-center gap-3 text-[10px] text-text-muted">
                  <span className="flex items-center gap-1"><Users className="h-3 w-3" />{room.max_participants} max</span>
                  <span className="flex items-center gap-1"><Lock className="h-3 w-3" />E2EE</span>
                  {room.recording_enabled && <span className="flex items-center gap-1"><Play className="h-3 w-3" />Recording</span>}
                  {room.transcription_enabled && <span className="flex items-center gap-1"><Mic className="h-3 w-3" />Transcription</span>}
                </div>

                {room.invite_link && (
                  <button onClick={() => handleCopyLink(room.invite_link!)}
                    className="flex items-center gap-1.5 w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-[10px] font-mono text-text-muted hover:text-text transition truncate">
                    <Copy className="h-3 w-3 shrink-0" />
                    <span className="truncate">{room.invite_link}</span>
                  </button>
                )}

                <div className="flex gap-2 pt-1">
                  {room.status === "active" ? (
                    <Button variant="primary" className="flex-1 rounded-lg px-3 py-2 text-[11px] font-semibold" onClick={() => { if (room.invite_link) router.push(room.invite_link!); }}>
                      <Phone className="h-3 w-3 inline mr-1" />Join Room
                    </Button>
                  ) : (
                    <Button variant="accent" className="flex-1 rounded-lg px-3 py-2 text-[11px] font-semibold" onClick={() => handleCopyLink(room.invite_link ?? `/meet/${room.room_uuid}`)}>
                      <Play className="h-3 w-3 inline mr-1" />Start
                    </Button>
                  )}
                  {room.status === "active" && !room.recording_enabled && (
                    <Button variant="ghost" size="sm" className="rounded-lg" onClick={() => handleStartRecording(room)} disabled={recordingRoomId === (room.room_id ?? room.room_uuid)}>
                      {recordingRoomId === (room.room_id ?? room.room_uuid) ? <Loader2 className="h-3 w-3 animate-spin" /> : <Mic className="h-3 w-3 text-danger" />}
                    </Button>
                  )}
                  {room.status === "active" && room.recording_enabled && (
                    <Button variant="ghost" size="sm" className="rounded-lg" onClick={() => handleStopRecording(room)} disabled={recordingRoomId === (room.room_id ?? room.room_uuid)}>
                      {recordingRoomId === (room.room_id ?? room.room_uuid) ? <Loader2 className="h-3 w-3 animate-spin" /> : <Square className="h-3 w-3 text-danger" />}
                    </Button>
                  )}
                  {room.status === "ended" && (
                    <Button variant="ghost" size="sm" className="rounded-lg" onClick={() => handleViewTranscript(room)} disabled={transcriptLoading && transcriptRoomId === (room.room_id ?? room.room_uuid)}>
                      {transcriptLoading && transcriptRoomId === (room.room_id ?? room.room_uuid) ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileText className="h-3 w-3" />}
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" className="rounded-lg" onClick={() => handleCopyLink(room.invite_link ?? `/meet/${room.room_uuid}`)}>
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </PanelCard>
            ))}
          </div>
        )}
      </PanelSection>

      {/* Create room modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setShowCreateModal(false)}>
            <div className="absolute inset-0 bg-black/40" />
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }}
              className="relative bg-surface-1 rounded-xl border border-border p-5 w-full max-w-md shadow-xl"
              onClick={(e: React.MouseEvent) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-text flex items-center gap-2"><Video className="h-4 w-4 text-primary" />Create Video Room</h3>
                <button onClick={() => setShowCreateModal(false)} className="text-text-muted hover:text-text"><X className="h-4 w-4" /></button>
              </div>
              <div className="space-y-3">
                <label className="block space-y-1 text-[10px] text-text-muted">
                  Room Name
                  <input value={newRoomName} onChange={(e) => setNewRoomName(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" placeholder="e.g. Q3 Board Review" />
                </label>
                <label className="block space-y-1 text-[10px] text-text-muted">
                  Meeting Type
                  <select value={newRoomPurpose} onChange={(e) => setNewRoomPurpose(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text">
                    <option value="meeting">Standard Meeting</option>
                    <option value="boardroom">Boardroom</option>
                    <option value="workshop">Workshop</option>
                    <option value="training">Training</option>
                  </select>
                </label>
                <label className="block space-y-1 text-[10px] text-text-muted">
                  Max Participants
                  <input type="number" min={2} max={500} value={newRoomParticipants}
                    onChange={(e) => setNewRoomParticipants(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" />
                </label>
              </div>
              <div className="flex items-center justify-end gap-2 mt-5">
                <button onClick={() => setShowCreateModal(false)} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text transition">Cancel</button>
                <Button variant="primary" onClick={handleCreateRoom} disabled={creatingRoom || !newRoomName.trim}>
                  {creatingRoom ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Video className="h-3.5 w-3.5" />}
                  Create Room
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}

        {showScheduleModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setShowScheduleModal(false)}>
            <div className="absolute inset-0 bg-black/40" />
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }}
              className="relative bg-surface-1 rounded-xl border border-border p-5 w-full max-w-md shadow-xl"
              onClick={(e: React.MouseEvent) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-text flex items-center gap-2"><Calendar className="h-4 w-4 text-primary" />Schedule Video Room</h3>
                <button onClick={() => setShowScheduleModal(false)} className="text-text-muted hover:text-text"><X className="h-4 w-4" /></button>
              </div>
              <div className="space-y-3">
                <label className="block space-y-1 text-[10px] text-text-muted">
                  Room Name
                  <input value={newRoomName} onChange={(e) => setNewRoomName(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" />
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="block space-y-1 text-[10px] text-text-muted">
                    Date
                    <input type="date" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)}
                      className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" />
                  </label>
                  <label className="block space-y-1 text-[10px] text-text-muted">
                    Time
                    <input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)}
                      className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" />
                  </label>
                </div>
              </div>
              <div className="flex items-center justify-end gap-2 mt-5">
                <button onClick={() => setShowScheduleModal(false)} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text transition">Cancel</button>
                <Button variant="primary" onClick={handleSchedule} disabled={creatingRoom || !newRoomName.trim || !scheduledDate || !scheduledTime}>Schedule</Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Transcript modal */}
      <AnimatePresence>
        {transcriptRoomId && transcriptData && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center" onClick={handleCloseTranscript}>
            <div className="absolute inset-0 bg-black/40" />
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }}
              className="relative bg-surface-1 rounded-xl border border-border p-5 w-full max-w-2xl max-h-[80vh] shadow-xl overflow-y-auto"
              onClick={(e: React.MouseEvent) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-text flex items-center gap-2"><FileText className="h-4 w-4 text-primary" />Transcript</h3>
                <button onClick={handleCloseTranscript} className="text-text-muted hover:text-text"><X className="h-4 w-4" /></button>
              </div>
              <p className="text-[10px] text-text-muted mb-3">Meeting: {transcriptData.meeting_id} · {transcriptData.word_count} words</p>

              {transcriptData.summary && (
                <div className="mb-4 p-3 rounded-lg bg-surface-2 border border-border">
                  <p className="text-[10px] font-semibold text-text-muted mb-1">Summary</p>
                  <p className="text-xs text-text">{transcriptData.summary}</p>
                </div>
              )}

              <div className="space-y-3 mb-4">
                <p className="text-[10px] font-semibold text-text-muted">Segments</p>
                {transcriptData.segments.length === 0 ? (
                  <p className="text-xs text-text-faint">No transcript segments recorded</p>
                ) : (
                  transcriptData.segments.map((seg, i) => (
                    <div key={i} className="p-3 rounded-lg bg-surface-2 border border-border">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-semibold text-primary">Speaker {seg.speaker_id}</span>
                        <span className="text-[10px] text-text-faint">{new Date(seg.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-xs text-text">{seg.content}</p>
                      {seg.language && <p className="text-[10px] text-text-faint mt-1">Language: {seg.language}</p>}
                    </div>
                  ))
                )}
              </div>

              {transcriptData.action_items.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold text-text-muted mb-2">Action Items</p>
                  <div className="space-y-2">
                    {transcriptData.action_items.map((item, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-warning/5 border border-warning/20">
                        <span className="text-[10px] font-medium text-text">{item.action}</span>
                        <span className="text-[10px] text-text-faint">· {item.entity_type} #{item.entity_id}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                          item.status === "done" ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                        }`}>{item.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PanelContent>
  );
}