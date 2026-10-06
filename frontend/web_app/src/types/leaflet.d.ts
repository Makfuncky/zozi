declare module "leaflet" {
  const L: any;
  export default L;
  export type DivIcon = any;
  export type Marker = any;
}

declare module "react-leaflet" {
  import * as React from "react";
  export const MapContainer: React.FC<any>;
  export const TileLayer: React.FC<any>;
  export const Marker: React.FC<any>;
  export const Popup: React.FC<any>;
  export function useMap(): any;
  export function useMapEvents(handlers: Record<string, (...args: any[]) => void>): any;
}
