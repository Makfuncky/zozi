import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  LayoutChangeEvent,
  PanResponder,
  StyleProp,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ViewStyle,
} from "react-native";
import Svg, { Path, Rect } from "react-native-svg";

type Point = { x: number; y: number };

interface SignaturePadProps {
  height?: number;
  strokeColor?: string;
  backgroundColor?: string;
  borderColor?: string;
  style?: StyleProp<ViewStyle>;
  onChange: (value: string | null) => void;
}

function buildPath(points: Point[]): string {
  if (!points.length) return "";
  if (points.length === 1) {
    const point = points[0];
    return `M ${point.x} ${point.y} L ${point.x + 0.1} ${point.y + 0.1}`;
  }
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

export default function SignaturePad({
  height = 180,
  strokeColor = "#111827",
  backgroundColor = "#ffffff",
  borderColor = "#d1d5db",
  style,
  onChange,
}: SignaturePadProps) {
  const [width, setWidth] = useState(0);
  const [paths, setPaths] = useState<Point[][]>([]);
  const [currentPath, setCurrentPath] = useState<Point[]>([]);
  const currentPathRef = useRef<Point[]>([]);

  const allPaths = useMemo(() => {
    return currentPath.length ? [...paths, currentPath] : paths;
  }, [currentPath, paths]);

  useEffect(() => {
    if (!width || !allPaths.length) {
      onChange(null);
      return;
    }

    const svgPaths = allPaths
      .filter((path) => path.length)
      .map(
        (path) => `<path d="${buildPath(path)}" fill="none" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />`,
      )
      .join("");

    if (!svgPaths) {
      onChange(null);
      return;
    }

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="${backgroundColor}"/>${svgPaths}</svg>`;
    onChange(`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`);
  }, [allPaths, backgroundColor, height, onChange, strokeColor, width]);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: (event) => {
          const point = {
            x: event.nativeEvent.locationX,
            y: event.nativeEvent.locationY,
          };
          currentPathRef.current = [point];
          setCurrentPath([point]);
        },
        onPanResponderMove: (event) => {
          const point = {
            x: event.nativeEvent.locationX,
            y: event.nativeEvent.locationY,
          };
          currentPathRef.current = [...currentPathRef.current, point];
          setCurrentPath([...currentPathRef.current]);
        },
        onPanResponderRelease: () => {
          if (currentPathRef.current.length) {
            setPaths((prev) => [...prev, currentPathRef.current]);
          }
          currentPathRef.current = [];
          setCurrentPath([]);
        },
        onPanResponderTerminate: () => {
          if (currentPathRef.current.length) {
            setPaths((prev) => [...prev, currentPathRef.current]);
          }
          currentPathRef.current = [];
          setCurrentPath([]);
        },
      }),
    [],
  );

  function onLayout(event: LayoutChangeEvent) {
    setWidth(event.nativeEvent.layout.width);
  }

  function clearSignature() {
    currentPathRef.current = [];
    setPaths([]);
    setCurrentPath([]);
    onChange(null);
  }

  return (
    <View style={style}>
      <View style={styles.headerRow}>
        <Text style={styles.helperText}>Sign inside the box.</Text>
        <TouchableOpacity onPress={clearSignature}>
          <Text style={styles.clearText}>Clear</Text>
        </TouchableOpacity>
      </View>
      <View
        style={[styles.canvas, { height, borderColor, backgroundColor }]}
        onLayout={onLayout}
        {...panResponder.panHandlers}
      >
        <Svg width="100%" height="100%">
          <Rect x={0} y={0} width="100%" height="100%" fill={backgroundColor} />
          {allPaths.map((path, index) => (
            <Path
              key={`${index}-${path.length}`}
              d={buildPath(path)}
              fill="none"
              stroke={strokeColor}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}
        </Svg>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  helperText: {
    color: "#6b7280",
    fontSize: 12,
    fontWeight: "600",
  },
  clearText: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "700",
  },
  canvas: {
    borderWidth: 1,
    borderRadius: 16,
    overflow: "hidden",
  },
});