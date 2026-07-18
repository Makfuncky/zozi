"use client";

import { Button } from "@/components/ui/Button";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Video, Mic, MicOff, VideoOff, Phone,
  ScreenShare, MessageCircle, Users,
  Shield, Copy, CheckCircle, Loader2,
} from "@/lib/icons";
import { useToastStore } from "@/lib/toastStore";

export default function MeetingRoomPage() {
  const params = useParams();
  const router = useRouter();
  const addToast = useToastStore((s) => s.addToast);
  const roomUuid = params?.room as string;

  const [joined, setJoined] = useState(false);
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [displayName, setDisplayName] = useState("");
  const [joining, setJoining] = useState(false);

  const handleJoin = useCallback(async () => {
    setJoining(true);
    // Simulate WebRTC negotiation delay
    await new Promise((r) => setTimeout(r, 1000));
    setJoined(true);
    setJoining(false);
  }, []);

  const handleLeave = useCallback(() => {
    setJoined(false);
    router.push("/admin/communication?tab=video");
  }, [router]);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      addToast("Meeting link copied", "success");
    } catch {
      addToast("Failed to copy", "error");
    }
  };

  if (!joined) {
    return (
      <div className="min-h-screen bg-surface-1 flex items-center justify-center p-4">
        <div className="max-w-sm w-full rounded-xl border border-border bg-surface-1 p-6 shadow-lg space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Video className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-text">Join Meeting</h2>
              <p className="text-[10px] text-text-muted font-mono">Room: {roomUuid}</p>
            </div>
          </div>

          <div className="h-40 rounded-xl bg-surface-2 border border-border flex items-center justify-center">
            <div className="text-center text-text-muted">
              <Video className="h-8 w-8 mx-auto mb-2 opacity-40" />
              <p className="text-xs">Camera preview</p>
              <p className="text-[10px] text-text-faint mt-1">E2E Encrypted</p>
            </div>
          </div>

          <label className="block space-y-1 text-[10px] text-text-muted">
            Your Display Name
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Enter your name"
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none"
            />
          </label>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setMicOn(!micOn)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                micOn ? "bg-surface-2 text-text border border-border" : "bg-danger/10 text-danger border border-danger/30"
              }`}
            >
              {micOn ? <Mic className="h-3.5 w-3.5" /> : <MicOff className="h-3.5 w-3.5" />}
              {micOn ? "Mute" : "Unmute"}
            </button>
            <button
              onClick={() => setCamOn(!camOn)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                camOn ? "bg-surface-2 text-text border border-border" : "bg-danger/10 text-danger border border-danger/30"
              }`}
            >
              {camOn ? <Video className="h-3.5 w-3.5" /> : <VideoOff className="h-3.5 w-3.5" />}
              {camOn ? "Camera On" : "Camera Off"}
            </button>
          </div>

          <Button variant="primary" onClick={handleJoin}
            disabled={joining}>
            {joining ? <Loader2 className="h-4 w-4 animate-spin" /> : <Phone className="h-4 w-4" />}
            {joining ? "Joining..." : "Join Meeting"}
          </Button>

          <div className="flex items-center gap-2 text-[10px] text-text-faint justify-center">
            <Shield className="h-3 w-3" />
            End-to-end encrypted · Secure room
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Main video grid */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="grid grid-cols-2 gap-3 w-full max-w-5xl">
          {/* Local video (simulated) */}
          <div className="aspect-video rounded-xl bg-surface-2 border border-border/30 flex items-center justify-center relative">
            {camOn ? (
              <div className="text-center text-text-muted">
                <Video className="h-10 w-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm">{displayName || "You"}</p>
                <p className="text-[10px] text-text-faint mt-1">Camera feed (simulated)</p>
              </div>
            ) : (
              <div className="text-center text-text-muted">
                <VideoOff className="h-10 w-10 mx-auto mb-2" />
                <p className="text-sm">Camera Off</p>
              </div>
            )}
            <span className="absolute bottom-2 left-2 text-[10px] text-text-faint bg-black/50 px-2 py-0.5 rounded">
              {displayName || "You"}
            </span>
          </div>

          {/* Remote participant placeholder */}
          <div className="aspect-video rounded-xl bg-surface-2 border border-border/30 flex items-center justify-center">
            <div className="text-center text-text-muted">
              <Users className="h-10 w-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Waiting for others...</p>
              <p className="text-[10px] text-text-faint mt-1">Share the meeting link to invite</p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls bar */}
      <div className="flex items-center justify-center gap-3 p-4">
        <button
          onClick={() => setMicOn(!micOn)}
          className={`rounded-xl p-3 transition ${
            micOn ? "bg-surface-2 text-text hover:bg-surface-3" : "bg-danger text-white"
          }`}
          title={micOn ? "Mute" : "Unmute"}
        >
          {micOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
        </button>
        <button
          onClick={() => setCamOn(!camOn)}
          className={`rounded-xl p-3 transition ${
            camOn ? "bg-surface-2 text-text hover:bg-surface-3" : "bg-danger text-white"
          }`}
          title={camOn ? "Camera Off" : "Camera On"}
        >
          {camOn ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
        </button>
        <button className="rounded-xl bg-surface-2 p-3 text-text hover:bg-surface-3 transition" title="Share Screen">
          <ScreenShare className="h-5 w-5" />
        </button>
        <button className="rounded-xl bg-surface-2 p-3 text-text hover:bg-surface-3 transition" title="Chat">
          <MessageCircle className="h-5 w-5" />
        </button>
        <button onClick={handleCopyLink} className="rounded-xl bg-surface-2 p-3 text-text hover:bg-surface-3 transition" title="Copy Invite Link">
          <Copy className="h-5 w-5" />
        </button>
        <Button variant="danger" className="rounded-xl p-3 transition" onClick={handleLeave}
          title="Leave Meeting"
        >
          <Phone className="h-5 w-5 rotate-135" />
        </Button>
      </div>

      <div className="text-center text-[10px] text-text-faint pb-2 flex items-center justify-center gap-2">
        <Shield className="h-3 w-3" />
        E2EE · Room: {roomUuid}
      </div>
    </div>
  );
}
