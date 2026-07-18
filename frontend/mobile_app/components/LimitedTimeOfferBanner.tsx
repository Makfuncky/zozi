import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { useRouter } from "expo-router";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  /* fallback */
}

export default function LimitedTimeOfferBanner() {
  useThemeStore(); // subscribe to theme changes
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(true);
  const [timeLeft, setTimeLeft] = useState(24 * 60 * 60); // 24h

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setIsVisible(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  if (!isVisible) return null;

  const hours = Math.floor(timeLeft / 3600);
  const minutes = Math.floor((timeLeft % 3600) / 60);
  const seconds = timeLeft % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");

  const content = (
    <View style={styles.inner}>
      <View style={styles.leftSection}>
        <Ionicons name="flash" size={16} color="#fff" />
        <Text style={styles.label}>Limited Offer!</Text>
      </View>
      <View style={styles.timerSection}>
        <View style={styles.timerBox}>
          <Text style={styles.timerDigit}>{pad(hours)}</Text>
        </View>
        <Text style={styles.timerColon}>:</Text>
        <View style={styles.timerBox}>
          <Text style={styles.timerDigit}>{pad(minutes)}</Text>
        </View>
        <Text style={styles.timerColon}>:</Text>
        <View style={styles.timerBox}>
          <Text style={styles.timerDigit}>{pad(seconds)}</Text>
        </View>
      </View>
      <TouchableOpacity
        style={styles.shopBtn}
        onPress={() => router.push("/flash-sales" as any)}
        activeOpacity={0.8}
      >
        <Text style={styles.shopBtnText}>Go</Text>
      </TouchableOpacity>
      <TouchableOpacity
        onPress={() => setIsVisible(false)}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
      >
        <Ionicons name="close" size={14} color="rgba(255,255,255,0.7)" />
      </TouchableOpacity>
    </View>
  );

  if (LinearGradient) {
    return (
      <LinearGradient
        colors={["#7CFC00", "#32CD32"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={styles.container}
      >
        {content}
      </LinearGradient>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: "#32CD32" }]}>
      {content}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    overflow: "hidden",
  },
  inner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 8,
    gap: 8,
  },
  leftSection: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  label: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "800",
  },
  timerSection: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
  },
  timerBox: {
    backgroundColor: "rgba(0,0,0,0.25)",
    borderRadius: 4,
    paddingHorizontal: 5,
    paddingVertical: 2,
  },
  timerDigit: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "800",
    fontVariant: ["tabular-nums"],
  },
  timerColon: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "800",
  },
  shopBtn: {
    backgroundColor: "rgba(0,0,0,0.2)",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  shopBtnText: {
    color: "#fff",
    fontSize: 11,
    fontWeight: "800",
  },
});
