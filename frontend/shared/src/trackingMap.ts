import type { OrderTracking, OrderTrackingEvent } from "./types";

export interface TrackingMapPoint {
  shipmentId: number;
  label: string;
  latitude: number;
  longitude: number;
  location?: string | null;
  currentHub?: string | null;
  trackingNumber?: string | null;
  recordedAt?: string | null;
}

function hasCoordinates(event: OrderTrackingEvent): boolean {
  return typeof event.latitude === "number" && typeof event.longitude === "number";
}

function latestCoordinateEvent(events: OrderTrackingEvent[] | undefined): OrderTrackingEvent | null {
  if (!Array.isArray(events)) return null;
  const coordinateEvents = events.filter(hasCoordinates);
  if (!coordinateEvents.length) return null;

  return [...coordinateEvents].sort((left, right) => {
    const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
    const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
    return rightTime - leftTime;
  })[0] ?? null;
}

export function extractTrackingMapPoints(tracking: OrderTracking | null): TrackingMapPoint[] {
  if (!tracking) return [];

  return tracking.shipments.reduce<TrackingMapPoint[]>((points, shipment) => {
      const event = latestCoordinateEvent(shipment.events ?? undefined);
      if (!event || typeof event.latitude !== "number" || typeof event.longitude !== "number") {
        return points;
      }

      points.push({
        shipmentId: shipment.id,
        label: shipment.supplier_name ? `Shipment #${shipment.id} · ${shipment.supplier_name}` : `Shipment #${shipment.id}`,
        latitude: event.latitude,
        longitude: event.longitude,
        location: event.location,
        currentHub: shipment.current_hub,
        trackingNumber: shipment.tracking_number,
        recordedAt: event.created_at,
      });

      return points;
    }, []);
}

export function buildTrackingMapHref(latitude: number, longitude: number): string {
  return `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=12/${latitude}/${longitude}`;
}