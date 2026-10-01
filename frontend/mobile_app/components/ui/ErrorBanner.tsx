import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";
import { Button } from "./Button";

interface ErrorBannerProps {
	message: string;
	onRetry?: () => void;
	retryLabel?: string;
}

const createStyles = (theme: AppTheme) =>
	({
		container: {
			flexDirection: "row" as const,
			alignItems: "center" as const,
			gap: 10,
			marginHorizontal: theme.spacing.lg,
			marginVertical: theme.spacing.md,
			padding: theme.spacing.md,
			borderRadius: theme.radius.lg,
			backgroundColor: `${theme.colors.danger}16`,
			borderWidth: 1,
			borderColor: `${theme.colors.danger}40`,
		},
		icon: {
			marginTop: 2,
		},
		text: {
			flex: 1,
			color: theme.colors.danger,
			fontSize: theme.fontSize.sm,
			lineHeight: 18,
		},
		retry: {
			paddingVertical: 6,
			paddingHorizontal: 12,
			borderRadius: theme.radius.md,
			backgroundColor: theme.colors.surface1,
			borderWidth: 1,
			borderColor: theme.colors.border,
		},
		retryText: {
			color: theme.colors.text,
			fontSize: theme.fontSize.sm,
			fontWeight: "600" as const,
		},
	});

export function ErrorBanner({ message, onRetry, retryLabel = "Retry" }: ErrorBannerProps) {
	const { theme } = useThemeStore();
	const styles = createStyles(theme);
	return (
		<View style={styles.container} accessibilityRole="alert">
			<Ionicons name="alert-circle" size={20} color={theme.colors.danger} style={styles.icon} />
			<Text style={styles.text}>{message}</Text>
			{onRetry ? (
				<TouchableOpacity style={styles.retry} onPress={onRetry} accessibilityRole="button" accessibilityLabel={retryLabel}>
					<Text style={styles.retryText}>{retryLabel}</Text>
				</TouchableOpacity>
			) : null}
		</View>
	);
}

export default ErrorBanner;
