/**
 * MobileBackgroundEffect
 * ─────────────────────────────────────────────────────────────
 * Mobile equivalent of web's BackgroundEffect.tsx.
 * Reads the current "effect" from effectStore (set by MobileSeasonalBanner
 * when the active banner changes) and renders lightweight animated decorations
 * behind all screen content.
 *
 * Supported effects:
 *   balloons  — coloured orbs rising from bottom to top on a loop
 *   poppers   — confetti pieces falling from top to bottom
 *   ramadan   — soft twinkling stars scattered across the screen
 *   eid       — brighter sparks + two glow blobs
 *   aurora    — three slow large colour blobs (static, no animation needed)
 *   (any other / empty) → renders nothing
 *
 * Mounted in app/_layout.tsx as the first child of GestureHandlerRootView,
 * absolutely positioned behind everything, pointerEvents="none".
 */
import React, { useEffect, useRef } from "react";
import { Animated, Dimensions, View } from "react-native";
import { useEffectStore } from "@/lib/effectStore";

const { width: SW, height: SH } = Dimensions.get("window");

/* ─── static data (computed once) ──────────────────────────────────────── */

const BALLOON_COLORS = [
  "rgba(50,205,50,0.68)",   // brand green
  "rgba(124,252,0,0.58)",   // lime
  "rgba(255,215,0,0.62)",   // gold
  "rgba(34,197,94,0.55)",   // emerald
  "rgba(250,204,21,0.60)",  // warm yellow
  "rgba(50,205,50,0.52)",
  "rgba(255,234,0,0.60)",
  "rgba(34,197,94,0.60)",
];

const BALLOONS = Array.from({ length: 10 }, (_, i) => ({
  id: i,
  x: (i * SW) / 10 + ((i % 3) - 1) * 14,
  size: 20 + (i % 5) * 9,
  color: BALLOON_COLORS[i % BALLOON_COLORS.length],
  duration: 11000 + i * 2200,
  initDelay: (i * 800) % 8000,
}));

const CONFETTI_COLORS = [
  "#22c55e", "#facc15", "#7cfc00", "#fbbf24",
  "#16a34a", "#ffd700", "#bef264", "#84cc16",
];

const CONFETTI = Array.from({ length: 22 }, (_, i) => ({
  id: i,
  x: (i * SW) / 22 + ((i % 4) - 1) * 6,
  size: 6 + (i % 4) * 4,
  color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
  duration: 2800 + i * 250,
  initDelay: (i * 140) % 4500,
  isCircle: i % 4 === 0,
}));

const STARS = Array.from({ length: 30 }, (_, i) => ({
  id: i,
  x: 16 + ((i * 37) % (SW - 32)),
  y: 24 + ((i * 53) % (SH * 0.72)),
  size: 2 + (i % 4),
  duration: 1800 + (i % 5) * 600,
  initDelay: (i * 200) % 4000,
}));

const EID_STARS = Array.from({ length: 20 }, (_, i) => ({
  id: i,
  x: 16 + ((i * 57) % (SW - 32)),
  y: 16 + ((i * 71) % (SH * 0.8)),
  size: 3 + (i % 4) * 1.5,
  duration: 1400 + (i % 5) * 500,
  initDelay: (i * 180) % 3500,
}));

/* ─── individual animated elements ─────────────────────────────────────── */

function BalloonEl({ x, size, color, duration, initDelay }: (typeof BALLOONS)[0]) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(anim, { toValue: 1, duration, useNativeDriver: true })
    );
    const timer = setTimeout(() => loop.start(), initDelay);
    return () => { clearTimeout(timer); loop.stop(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const translateY = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [SH + 60, -size * 2],
  });

  return (
    <Animated.View
      style={{
        position: "absolute",
        left: x,
        width: size,
        height: size * 1.2,
        borderRadius: size / 2,
        backgroundColor: color,
        transform: [{ translateY }],
      }}
    />
  );
}

function ConfettiEl({ x, size, color, duration, initDelay, isCircle }: (typeof CONFETTI)[0]) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(anim, { toValue: 1, duration, useNativeDriver: true })
    );
    const timer = setTimeout(() => loop.start(), initDelay);
    return () => { clearTimeout(timer); loop.stop(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const translateY = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [-size * 2, SH + size * 2],
  });

  return (
    <Animated.View
      style={{
        position: "absolute",
        left: x,
        width: isCircle ? size : size * 0.7,
        height: size,
        borderRadius: isCircle ? size / 2 : 2,
        backgroundColor: color,
        opacity: 0.82,
        transform: [{ translateY }],
      }}
    />
  );
}

function StarEl({ x, y, size, duration, initDelay }: (typeof STARS)[0]) {
  const anim = useRef(new Animated.Value(0.15)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: duration / 2, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0.15, duration: duration / 2, useNativeDriver: true }),
      ])
    );
    const timer = setTimeout(() => loop.start(), initDelay);
    return () => { clearTimeout(timer); loop.stop(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Animated.View
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: "#ffffff",
        opacity: anim,
      }}
    />
  );
}

function EidStarEl({ x, y, size, duration, initDelay }: (typeof EID_STARS)[0]) {
  const anim = useRef(new Animated.Value(0.1)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 0.9, duration: duration / 2, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0.1, duration: duration / 2, useNativeDriver: true }),
      ])
    );
    const timer = setTimeout(() => loop.start(), initDelay);
    return () => { clearTimeout(timer); loop.stop(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const scale = anim.interpolate({ inputRange: [0.1, 0.9], outputRange: [0.6, 1.2] });

  return (
    <Animated.View
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: "#fcd34d",
        opacity: anim,
        transform: [{ scale }],
      }}
    />
  );
}

/* ─── main component ────────────────────────────────────────────────────── */

export default function MobileBackgroundEffect() {
  const effect = useEffectStore((s) => s.effect);

  // No active seasonal effect — render a soft ambient brand glow so frosted
  // glass surfaces have depth to refract. Cheap, static, low GPU cost.
  if (!effect || effect === "none" || effect === "") {
    return (
      <View
        pointerEvents="none"
        style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }}
      >
        <View style={{
          position: "absolute", top: -90, left: -70,
          width: 300, height: 300, borderRadius: 150,
          backgroundColor: "rgba(50,205,50,0.10)",
        }} />
        <View style={{
          position: "absolute", top: SH * 0.32, right: -80,
          width: 260, height: 260, borderRadius: 130,
          backgroundColor: "rgba(255,215,0,0.07)",
        }} />
        <View style={{
          position: "absolute", bottom: -50, left: SW * 0.22,
          width: 240, height: 240, borderRadius: 120,
          backgroundColor: "rgba(34,197,94,0.06)",
        }} />
      </View>
    );
  }

  if (effect === "aurora") {
    // Static blobs — no animation needed, low GPU cost
    return (
      <View
        pointerEvents="none"
        style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }}
      >
        <View style={{
          position: "absolute", top: -80, left: -80,
          width: 320, height: 320, borderRadius: 160,
          backgroundColor: "rgba(50,205,50,0.12)",
        }} />
        <View style={{
          position: "absolute", top: SH * 0.28, right: -90,
          width: 280, height: 280, borderRadius: 140,
          backgroundColor: "rgba(255,215,0,0.08)",
        }} />
        <View style={{
          position: "absolute", bottom: -60, left: SW * 0.25,
          width: 260, height: 260, borderRadius: 130,
          backgroundColor: "rgba(255,234,0,0.06)",
        }} />
      </View>
    );
  }

  return (
    <View
      pointerEvents="none"
      style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }}
    >
      {effect === "balloons" &&
        BALLOONS.map((b) => <BalloonEl key={b.id} {...b} />)}

      {effect === "poppers" &&
        CONFETTI.map((c) => <ConfettiEl key={c.id} {...c} />)}

      {effect === "ramadan" &&
        STARS.map((s) => <StarEl key={s.id} {...s} />)}

      {effect === "eid" && (
        <>
          {EID_STARS.map((s) => <EidStarEl key={s.id} {...s} />)}
          <View style={{
            position: "absolute", top: SH * 0.05, left: -40,
            width: 160, height: 160, borderRadius: 80,
            backgroundColor: "rgba(250,204,21,0.08)",
          }} />
          <View style={{
            position: "absolute", bottom: SH * 0.1, right: -40,
            width: 140, height: 140, borderRadius: 70,
            backgroundColor: "rgba(167,139,250,0.08)",
          }} />
        </>
      )}
    </View>
  );
}
