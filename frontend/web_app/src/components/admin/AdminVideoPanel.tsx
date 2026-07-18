"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Video, Phone, Users, Clock, Lock,
  Plus, Loader2, X, Copy, CheckCircle,
  AlertCircle, Shield, Calendar,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";

interface VideoRoom {
  id: number;
  name: string;
  room_uuid: string;
  purpose: string;
  status: string;
  created_at: string;
  max_participants: number;
  invite_link?: string;
}

export default function AdminVideoPanel() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((s) => s.addToast);

  const { selectedCountry, assignedCountries, isGlobalView } = useAdminCountry();
  const countryCode = isGlobalView ? (assignedCountries[0]?.code || selectedCountry?.code || "AE") : (selectedCountry?.code || "AE");
  const [loading, setLoading] = useState(true);
  const [rooms, setRooms] = useState<VideoRoom[]>([]);

  // Create room modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRoomName, setNewRoomName] = useState("");
  const [newRoomPurpose, setNewRoomPurpose] = useState("meeting");
  const [newRoomParticipants, setNewRoomParticipants] = useState("10");
  const [creatingRoom, setCreatingRoom] = useState(false);

  const loadRooms = useCallback(async () => {
    try {
      const res = await apiFetch("/admin/video/rooms");
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setRooms(Array.isArray(data) ? data : []);
      }
    } catch {
      // silent
    }
  }, [isGlobalView, countryCode]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
      router.replace("/admin/login");
      return;
    }
    (async () => {
      await loadRooms();
      setLoading(false);
    })();
  }, [authLoading, isLoggedIn, loadRooms, router, user?.role]);

  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return;
    setCreatingRoom(true);
    try {
      const body = {
        name: newRoomName.trim(),
        purpose: newRoomPurpose,
        max_participants: parseInt(newRoomParticipants) || 10,
        created_by: user?.id,
      };
      const res = await apiFetch(`/admin/video/rooms/${countryCode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await parseJsonResponse(res);
        addToast("Video room created", "success");
        setShowCreateModal(false);
        setNewRoomName("");
        setNewRoomPurpose("meeting");
        setNewRoomParticipants("10");
        loadRooms();
        if (data?.invite_link) {
          addToast(`Room link: ${data.invite_link}`, "info", 5000);
        }
      } else {
        const err = await parseJsonResponse(res);
        addToast(err?.detail ?? "Failed to create room", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setCreatingRoom(false);
    }
  };

  const handleCopyLink = async (link: string) => {
    try {
      await navigator.clipboard.writeText(window.location.origin + link);
      addToast("Meeting link copied to clipboard", "success");
    } catch {
      addToast("Failed to copy link", "error");
    }
  };

  if (authLoading || loading) {
    return <PanelLoadingState count={3} />;
  }

  if (!isLoggedIn || !isAdminStaffRole(user?.role)) return null;

  return (
    <PanelContent width="full" className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-text flex items-center gap-2">
            <Video className="h-4 w-4 text-primary" />
            Secure Video Boardrooms
          </h2>
          <p className="text-xs text-text-muted mt-1">End-to-end encrypted meeting rooms for teams and management</p>
        </div>
        <span className="text-[10px] text-text-faint">{isGlobalView ? "Global View" : `Country: ${selectedCountry?.code || countryCode}`}</span>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition" onClick={() => setShowCreateModal(true)}
        >
          <Plus className="h-3.5 w-3.5" />
          Create Room
        </Button>
      </div>

      {/* Rooms grid */}
      {rooms.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <Video className="h-12 w-12 mb-3 opacity-30" />
          <p className="text-sm">No video rooms created yet</p>
          <p className="text-xs text-text-faint mt-1">Click &quot;Create Room&quot; to start a new meeting</p>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {rooms.map((room) => (
            <div key={room.id} className="rounded-xl border border-border bg-surface-1 p-4 space-y-3 hover:shadow-sm transition">
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
                  room.status === "active" ? "bg-success/10 text-success" : "bg-surface-3 text-text-muted"
                }`}>
                  {room.status ?? "active"}
                </span>
              </div>

              <div className="flex items-center gap-3 text-[10px] text-text-muted">
                <span className="flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  {room.max_participants} max
                </span>
                <span className="flex items-center gap-1">
                  <Lock className="h-3 w-3" />
                  E2EE
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(room.created_at).toLocaleDateString()}
                </span>
              </div>

              {(room as any).invite_link && (
                <button
                  onClick={() => handleCopyLink((room as any).invite_link)}
                  className="flex items-center gap-1.5 w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-[10px] font-mono text-text-muted hover:text-text transition truncate"
                >
                  <Copy className="h-3 w-3 shrink-0" />
                  <span className="truncate">{(room as any).invite_link}</span>
                </button>
              )}

              <div className="flex gap-2 pt-1">
                <Button variant="primary" className="flex-1 rounded-lg px-3 py-2 text-[11px] font-semibold transition" onClick={() => {
                    if ((room as any).invite_link) {
                      router.push((room as any).invite_link);
                    }
                  }}
                >
                  <Phone className="h-3 w-3 inline mr-1" />
                  Join Room
                </Button>
                <button
                  onClick={() => handleCopyLink((room as any).invite_link ?? `/meet/${room.room_uuid}`)}
                  className="rounded-lg border border-border px-3 py-2 text-[11px] font-medium text-text-muted hover:text-text transition"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create room modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay">
          <div className="rounded-xl border border-border bg-surface-1 p-5 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-text flex items-center gap-2">
                <Video className="h-4 w-4 text-primary" />
                New Video Room
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-text-muted hover:text-text">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <label className="block space-y-1 text-[10px] text-text-muted">
                Room Name
                <input
                  value={newRoomName}
                  onChange={(e) => setNewRoomName(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                  placeholder="e.g. Q3 Board Review"
                />
              </label>
              <label className="block space-y-1 text-[10px] text-text-muted">
                Meeting Type
                <select
                  value={newRoomPurpose}
                  onChange={(e) => setNewRoomPurpose(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                >
                  <option value="meeting">Standard Meeting</option>
                  <option value="boardroom">Boardroom</option>
                  <option value="workshop">Workshop</option>
                  <option value="training">Training</option>
                </select>
              </label>
              <label className="block space-y-1 text-[10px] text-text-muted">
                Max Participants
                <input
                  type="number"
                  min="2"
                  max="500"
                  value={newRoomParticipants}
                  onChange={(e) => setNewRoomParticipants(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                />
              </label>
            </div>

            <div className="flex items-center justify-end gap-2 mt-5">
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text transition"
              >
                Cancel
              </button>
              <Button variant="primary" onClick={handleCreateRoom}
                disabled={creatingRoom || !newRoomName.trim()}>
                {creatingRoom ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Video className="h-3.5 w-3.5" />}
                Create Room
              </Button>
            </div>
          </div>
        </div>
      )}
    </PanelContent>
  );
}
