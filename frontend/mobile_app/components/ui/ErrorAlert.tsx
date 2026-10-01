import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { dark, light } from "@shared/theme.native";
import { useThemeStore } from "@/lib/themeStore";

interface ErrorAlertProps {
	message: string;
	type?: "error" | "success" | "info";
}

const TEXT_COLORS: Record<"error" | "success" | "info", { dark: string; light: string }> = {
	error: { dark: "#fca5a5", light: "#b91c1c" },
	success: { dark: "#bbf7d0", light: "#15803d" },
	info: { dark: "#7dd3fc", light: "#0369a1" },
};

const getStyles = (type: "error" | "success" | "info", mode: "dark" | "light") => {
	const colors = mode === "light" ? light : dark;
	const base = {
		marginBottom: 16,
		padding: 16,
		borderRadius: 12,
		borderWidth: 1,
		flexDirection: "row" as const,
		alignItems: "center" as const,
		gap: 10,
	};

	switch (type) {
		case "error":
			return { ...base, backgroundColor: `${colors.danger}1A`, borderColor: `${colors.danger}4D` };
		case "success":
			return { ...base, backgroundColor: `${colors.success}1A`, borderColor: `${colors.success}4D` };
		case "info":
			return { ...base, backgroundColor: `${colors.info}1A`, borderColor: `${colors.info}4D` };
	}
};

export default function ErrorAlert({ message, type = "error" }: ErrorAlertProps) {
	if (!message) return null;

	const { mode } = useThemeStore();
	const styles = getStyles(type, mode);
	const textColor = TEXT_COLORS[type][mode];

	return (
		<View style={styles}>
			<Text style={[textStyle, { color: textColor }]}>{message}</Text>
		</View>
	);
}

const textStyle = StyleSheet.create({
	text: { fontSize: 14, flexShrink: 1, lineHeight: 20 },
}).text;
