import React, { useCallback, useMemo, useRef, useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  TextInput,
  ActivityIndicator,
  StyleSheet,
  type ViewStyle,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { apiFetch } from "@/lib/api";
import { toast } from "@/lib/toastStore";
import {
  LatLng,
  defaultCenterForCountry,
  formatLatLng,
  parseLatLng,
  pixelToLatLng,
  staticMapUrl,
} from "@/lib/geo";

interface LocationPickerProps {
  /** Existing value in "lat,lng" format. */
  value?: string;
  onChange: (value: string) => void;
  /** Called with a best-effort address when reverse geocoding succeeds. */
  onReverseGeocode?: (info: { street?: string; city?: string; country?: string }) => void;
  countryCode?: string;
  zoom?: number;
  testID?: string;
}

const MAP_HEIGHT = 200;
const REQUEST_WIDTH = 600;
const REQUEST_HEIGHT = 300;

function reverseGeocode(point: LatLng): Promise<{ street?: string; city?: string; country?: string } | null> {
  return apiFetch<Record<string, any>>("/location/api/geo/reverse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: point.lat, lng: point.lng }),
  })
    .then((data) => {
      if (!data) return null;
      const address = data.address ?? data;
      const street =
        address.road ?? address.street ?? address.pedestrian ?? address.neighbourhood ?? "";
      const city =
        address.city ?? address.town ?? address.village ?? address.county ?? address.state ?? "";
      const country = address.country ?? "";
      if (!street && !city && !country) return null;
      return { street, city, country };
    })
    .catch(() => null);
}

export function LocationPicker({
  value,
  onChange,
  onReverseGeocode,
  countryCode,
  zoom = 16,
  testID,
}: LocationPickerProps) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);

  const initialPoint = useMemo(() => parseLatLng(value), [value]);
  const defaultCenter = useMemo(() => defaultCenterForCountry(countryCode), [countryCode]);

  const [point, setPoint] = useState<LatLng | null>(initialPoint);
  const [center, setCenter] = useState<LatLng>(initialPoint ?? defaultCenter);
  const [size, setSize] = useState<{ w: number; h: number }>({ w: REQUEST_WIDTH, h: MAP_HEIGHT });
  const [imageError, setImageError] = useState(false);
  const [locating, setLocating] = useState(false);

  const [latText, setLatText] = useState(initialPoint ? String(initialPoint.lat) : "");
  const [lngText, setLngText] = useState(initialPoint ? String(initialPoint.lng) : "");

  const sizeRef = useRef(size);
  sizeRef.current = size;

  const mapUri = useMemo(() => staticMapUrl(center, zoom, REQUEST_WIDTH, REQUEST_HEIGHT), [center, zoom]);

  const applyPoint = useCallback(
    (next: LatLng) => {
      setPoint(next);
      setCenter(next);
      setLatText(String(next.lat));
      setLngText(String(next.lng));
      setImageError(false);
      onChange(formatLatLng(next));
      if (onReverseGeocode) {
        void reverseGeocode(next).then((info) => {
          if (info) onReverseGeocode(info);
        });
      }
    },
    [onChange, onReverseGeocode],
  );

  const handleTap = useCallback(
    (e: { nativeEvent: { locationX: number; locationY: number } }) => {
      const { locationX, locationY } = e.nativeEvent;
      const next = pixelToLatLng(center, zoom, locationX, locationY, sizeRef.current.w, sizeRef.current.h);
      applyPoint(next);
    },
    [applyPoint, center, zoom],
  );

  const handleManualSet = useCallback(() => {
    const lat = parseFloat(latText);
    const lng = parseFloat(lngText);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      toast.error("Enter valid latitude and longitude");
      return;
    }
    applyPoint({ lat, lng });
  }, [applyPoint, latText, lngText]);

  const handleUseMyLocation = useCallback(() => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      toast.error("Location services are not available on this device");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        applyPoint({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      },
      () => {
        setLocating(false);
        toast.error("Could not get your location");
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }, [applyPoint]);

  const handleClear = useCallback(() => {
    setPoint(null);
    setCenter(defaultCenter);
    setLatText("");
    setLngText("");
    setImageError(false);
    onChange("");
  }, [defaultCenter, onChange]);

  return (
    <View testID={testID} style={styles.wrap}>
      <View style={[styles.headerRow, { marginBottom: theme.spacing.sm }]}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Ionicons name="map-outline" size={16} color={theme.colors.brand} />
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.sm }]}>
            Drop-off location
          </Text>
        </View>
        {point ? (
          <TouchableOpacity onPress={handleClear} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Text style={{ color: theme.colors.textMuted, fontSize: 12, fontWeight: "600" }}>Clear</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <View style={styles.mapFrame}>
        {imageError ? (
          <View style={[styles.mapPlaceholder, { height: MAP_HEIGHT }]}>
            <Ionicons name="image-outline" size={28} color={theme.colors.textMuted} />
            <Text style={[s.textMuted, { textAlign: "center", marginTop: 6 }]}>
              Map preview unavailable. Tap the map area or enter coordinates below.
            </Text>
          </View>
        ) : (
          <TouchableOpacity
            activeOpacity={1}
            onPress={handleTap}
            style={{ width: "100%", height: MAP_HEIGHT }}
          >
            <Image
              source={{ uri: mapUri }}
              style={{ width: "100%", height: MAP_HEIGHT }}
              resizeMode="cover"
              onLayout={(e) => setSize({ w: e.nativeEvent.layout.width, h: e.nativeEvent.layout.height })}
              onError={() => setImageError(true)}
            />
            <View style={styles.pinOverlay} pointerEvents="none">
              <Ionicons name="location" size={36} color={theme.colors.danger} />
            </View>
            <View style={styles.tapHint} pointerEvents="none">
              <Text style={styles.tapHintText}>Tap to move pin</Text>
            </View>
          </TouchableOpacity>
        )}
      </View>

      <View style={[styles.manualRow, { marginTop: theme.spacing.sm }]}>
        <View style={[styles.coordInput, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
          <Text style={[s.textMuted, { fontSize: 11 }]}>Lat</Text>
          <TextInput
            style={[styles.coordText, { color: theme.colors.text }]}
            value={latText}
            onChangeText={setLatText}
            placeholder="23.588"
            keyboardType="decimal-pad"
            placeholderTextColor={theme.colors.textMuted}
          />
        </View>
        <View style={[styles.coordInput, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
          <Text style={[s.textMuted, { fontSize: 11 }]}>Lng</Text>
          <TextInput
            style={[styles.coordText, { color: theme.colors.text }]}
            value={lngText}
            onChangeText={setLngText}
            placeholder="58.3829"
            keyboardType="decimal-pad"
            placeholderTextColor={theme.colors.textMuted}
          />
        </View>
        <TouchableOpacity
          onPress={handleManualSet}
          style={[styles.setBtn, { backgroundColor: theme.colors.brand }]}
        >
          <Text style={styles.setBtnText}>Set</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        onPress={handleUseMyLocation}
        disabled={locating}
        style={[styles.locateBtn, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand + "12" }]}
      >
        {locating ? (
          <ActivityIndicator size="small" color={theme.colors.brand} />
        ) : (
          <Ionicons name="locate-outline" size={15} color={theme.colors.brand} />
        )}
        <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: 12 }}>
          {locating ? "Locating…" : "Use my location"}
        </Text>
      </TouchableOpacity>

      {point ? (
        <Text style={[s.textMuted, { marginTop: theme.spacing.xs, fontSize: 11 }]}>
          Pinned at {formatLatLng(point)}
        </Text>
      ) : null}
    </View>
  );
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  wrap: {},
  headerRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  mapFrame: {
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface0,
  },
  mapPlaceholder: {
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    backgroundColor: theme.colors.surface0,
  },
  pinOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "center",
  },
  tapHint: {
    position: "absolute",
    bottom: 8,
    alignSelf: "center",
    backgroundColor: "rgba(0,0,0,0.55)",
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 10,
  },
  tapHintText: { color: "#fff", fontSize: 11, fontWeight: "600" },
  manualRow: { flexDirection: "row", gap: 8, alignItems: "center" },
  coordInput: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
    gap: 2,
  },
  coordText: { fontSize: 14, fontWeight: "600" },
  setBtn: {
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  setBtnText: { color: "#fff", fontWeight: "800", fontSize: 13 },
  locateBtn: {
    marginTop: theme.spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderRadius: 10,
    borderWidth: 1,
    paddingVertical: 10,
  },
});

export default LocationPicker;
