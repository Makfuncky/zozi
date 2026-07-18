import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Defs, Ellipse, G, LinearGradient, Path, RadialGradient, Stop } from "react-native-svg";
import { brand } from "../theme";
import type { LogoSize, LogoTheme } from "./types";

export interface LogoNativeProps {
  size?: LogoSize;
  onPress?: () => void;
  theme?: LogoTheme;
  showWordmark?: boolean;
}

const SIZES = {
  sm: { icon: 58, text: 22, gap: 2 },
  md: { icon: 82, text: 30, gap: 4 },
  lg: { icon: 110, text: 40, gap: 6 },
} as const;

const TOKENS = {
  light: {
    zTop: "#E2FF70",
    zMid1: "#C8EC22",
    zMid2: "#86BE12",
    zMid3: "#409808",
    zBot: "#1A5204",
    pinHole: "#ffffff",
    pinHoleStroke: "rgba(0,0,0,0.08)",
    flareColor: "#F8C400",
    flareStart: "#E8A000",
    wordmark: brand.primaryDark,
  },
  dark: {
    zTop: "#EEFF99",
    zMid1: "#CCEE38",
    zMid2: "#97D01A",
    zMid3: "#55B010",
    zBot: "#2A7006",
    pinHole: "#ffffff",
    pinHoleStroke: "rgba(255,255,255,0.15)",
    flareColor: "#FFD740",
    flareStart: "#FFCC22",
    wordmark: "#4E6790",
  },
} as const;

export default function Logo({ size = "md", onPress, theme = "light", showWordmark = true }: LogoNativeProps) {
  const { icon, text, gap } = SIZES[size];
  const tokens = TOKENS[theme];
  const iconHeight = (icon * 170) / 200;

  const content = (
    <View style={styles.container}>
      <View style={[styles.iconWrap, { marginRight: showWordmark ? gap : 0 }]}>
        <Svg viewBox="0 0 200 170" width={icon} height={iconHeight} fill="none">
          <Defs>
            <LinearGradient id="greenGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <Stop offset="0%" stopColor={tokens.zTop} />
              <Stop offset="20%" stopColor={tokens.zMid1} />
              <Stop offset="50%" stopColor={tokens.zMid2} />
              <Stop offset="80%" stopColor={tokens.zMid3} />
              <Stop offset="100%" stopColor={tokens.zBot} />
            </LinearGradient>
            <LinearGradient id="pinGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <Stop offset="0%" stopColor="#FFF550" />
              <Stop offset="35%" stopColor="#F0C800" />
              <Stop offset="75%" stopColor="#D08C00" />
              <Stop offset="100%" stopColor="#A86000" />
            </LinearGradient>
            <RadialGradient id="flareGradient" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor={tokens.flareColor} stopOpacity="0.7" />
              <Stop offset="100%" stopColor={tokens.flareColor} stopOpacity="0" />
            </RadialGradient>
            <LinearGradient id="pinReflection" x1="0%" y1="0%" x2="0%" y2="100%">
              <Stop offset="0%" stopColor={tokens.flareStart} stopOpacity="0.4" />
              <Stop offset="100%" stopColor={tokens.flareStart} stopOpacity="0" />
            </LinearGradient>
          </Defs>

          <G>
            <Path
              d="M 20,40 C 70,15 135,10 188,20 C 191,21 190,23 182,24 C 125,35 65,55 25,70 Z"
              fill="url(#greenGradient)"
            />
            <Path
              d="M 182,24 C 110,65 52,115 40,140 C 22,148 20,120 40,102 C 40,100 116,35 188,22 Z"
              fill="url(#greenGradient)"
            />
            <Path
              d="M 38,126 C 68,127 115,123 134,121 L 134,124 C 98,135 68,140 38,140 C 24,140 24,126 38,126 Z"
              fill="url(#greenGradient)"
            />
          </G>

          <Ellipse cx="155" cy="150" rx="24" ry="2.5" fill="url(#flareGradient)" />
          <Path d="M 147,150 Q 155,166 163,150 Z" fill="url(#pinReflection)" />
          <Ellipse cx="155" cy="150" rx="16" ry="4" fill="rgba(0,0,0,0.06)" />
          <Path
            d="M 155,148 C 139,122 123,106 123,86 C 123,68 137,54 155,54 C 173,54 187,68 187,86 C 187,106 171,122 155,148 Z"
            fill="url(#pinGradient)"
          />
          <Path
            d="M 155,145 C 141,120 126,105 126,86 C 126,70 139,57 155,57 C 171,57 184,70 184,86 C 184,105 169,120 155,145 Z"
            fill="none"
            stroke="white"
            strokeWidth="1.5"
            opacity="0.35"
          />
          <Circle cx="155" cy="86" r="14" fill={tokens.pinHole} />
          <Circle cx="155" cy="86" r="14" fill="none" stroke={tokens.pinHoleStroke} strokeWidth="1.5" />
        </Svg>
      </View>

      {showWordmark ? (
        <Text style={[styles.text, { fontSize: text, color: tokens.wordmark }]}>ZOZI</Text>
      ) : null}
    </View>
  );

  if (!onPress) {
    return content;
  }

  return (
    <Pressable onPress={onPress} style={({ pressed }) => (pressed ? styles.pressed : null)}>
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
  },
  iconWrap: {
    shadowColor: "#10233e",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.16,
    shadowRadius: 8,
    elevation: 5,
  },
  text: {
    fontWeight: "900",
    letterSpacing: -1.5,
  },
  pressed: {
    opacity: 0.82,
    transform: [{ scale: 0.97 }],
  },
});