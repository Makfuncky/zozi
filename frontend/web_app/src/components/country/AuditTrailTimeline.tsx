"use client";

import { useState, useEffect } from "react";
import { Clock, User, Shield, FileText, RefreshCw } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";

interface AuditEvent {
  id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  user_id: number;
  user_name: string;
  user_role: string;
  details: Record<string, any>;
  created_at: string;
  reason?: string;
}

interface AuditTrailTimelineProps {
  countryCode: string;
}

export default function AuditTrailTimeline({ countryCode }: AuditTrailTimelineProps) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadEvents = async () => {
      setLoading(true);
      const response = await apiFetch(`/admin/countries/${countryCode}/audit-trail`);
      if (response.ok) {
        const data = await parseJsonResponse(response);
        setEvents(Array.isArray(data) ? data : []);
      }
      setLoading(false);
    };
    loadEvents();
  }, [countryCode]);

  if (loading) {
    return (
      <div className="text-center py-8">
        <RefreshCw className="h-6 w-6 animate-spin text-text-muted mx-auto mb-2" />
        <p className="text-sm text-text-muted">Loading audit trail...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Immutable Audit Trail</h3>
        </div>
        <span className="text-xs text-text-muted">{events.length} events</span>
      </div>

      <div className="border border-border rounded-lg bg-surface-1 p-4">
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-sm text-text-muted italic">No audit events recorded</p>
          ) : (
            events.map((event, index) => (
              <div key={event.id} className="flex items-start gap-3 pb-3 border-b border-border last:border-0">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-3 w-3 text-primary" />
                </div>
                <div className="flex-1 text-xs">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-text">{event.user_name}</span>
                    <span className="text-text-muted">({event.user_role.replace("_", " ")})</span>
                  </div>
                  <p className="text-text-muted mb-1">{event.action.replace(/_/g, " ")}</p>
                  {event.reason && (
                    <p className="text-warning bg-warning/10 px-2 py-1 rounded text-[10px] mt-1">
                      Reason: {event.reason}
                    </p>
                  )}
                  <p className="text-text-faint mt-1">
                    {new Date(event.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}


