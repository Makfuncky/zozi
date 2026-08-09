import React, { type ReactNode } from "react";
import {
	View,
	ScrollView,
	RefreshControl,
	StyleSheet,
	TouchableOpacity,
	type ViewStyle,
	type ScrollViewProps,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Stack } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

interface ScreenProps {
	children: React.ReactNode;
	/** Wrap content in a scrollable area (default true). */
	scroll?: boolean;
	/** Style applied to the root container (SafeAreaView). */
	style?: ViewStyle;
	/** Style applied to the inner content (ScrollView content / View). */
	contentContainerStyle?: ViewStyle;
	/** Pull-to-refresh state (only used when scroll is true). */
	refreshing?: boolean;
	onRefresh?: () => void;
	/** Avoid keyboard covering inputs (default "handled" when scroll). */
	keyboardShouldPersistTaps?: "always" | "never" | "handled";
	/** Safe-area edges to apply (defaults to all). */
	edges?: ("top" | "bottom" | "left" | "right")[];
	/** Render header content above the scroll area (e.g. a custom header). */
	header?: React.ReactNode;
	contentInset?: ScrollViewProps["contentInset"];
	testID?: string;
	/** Title for the native stack header. Enables the header automatically. */
	title?: string;
	/** Right-side header accessory (e.g. an icon button). */
	headerRight?: ReactNode;
	/** Custom left header accessory. Defaults to a back button when a router can pop. */
	headerLeft?: ReactNode;
	/** Set to false to hide the stack header entirely. */
	headerShown?: boolean;
	/** Floating action button rendered above the content (bottom-right). */
	fab?: ReactNode;
	/** Show a scroll-to-top button after scrolling down (only with scroll). */
	showScrollToTop?: boolean;
}

const createStyles = (theme: AppTheme) =>
	StyleSheet.create({
		container: {
			flex: 1,
			backgroundColor: theme.colors.surface0,
		},
		content: {
			flex: 1,
		},
		scrollToTop: {
			position: "absolute",
			right: 16,
			bottom: 20,
			width: 42,
			height: 42,
			borderRadius: 21,
			backgroundColor: theme.colors.surface1,
			borderWidth: 1,
			borderColor: theme.colors.border,
			alignItems: "center",
			justifyContent: "center",
			shadowColor: theme.colors.text,
			shadowOpacity: 0.15,
			shadowRadius: 8,
			shadowOffset: { width: 0, height: 3 },
			elevation: 5,
		},
	});

export function Screen({
	children,
	scroll = true,
	style,
	contentContainerStyle,
	refreshing,
	onRefresh,
	keyboardShouldPersistTaps = "handled",
	edges,
	header,
	contentInset,
	testID,
	title,
	headerRight,
	headerLeft,
	headerShown = true,
	fab,
	showScrollToTop = false,
}: ScreenProps) {
	const { theme } = useThemeStore();
	const router = useRouter();
	const styles = createStyles(theme);
	const scrollRef = React.useRef<ScrollView>(null);
	const [showTop, setShowTop] = React.useState(false);

	const showHeader = headerShown && !!title;

	const content = scroll ? (
		<ScrollView
			ref={scrollRef}
			style={styles.content}
			contentContainerStyle={[{ paddingBottom: theme.spacing.lg }, contentContainerStyle]}
			contentInset={contentInset ?? { bottom: 0 }}
			keyboardShouldPersistTaps={keyboardShouldPersistTaps}
			onScroll={
				showScrollToTop
					? (e) => setShowTop(e.nativeEvent.contentOffset.y > 400)
					: undefined
			}
			scrollEventThrottle={showScrollToTop ? 200 : undefined}
			refreshControl={
				onRefresh ? (
					<RefreshControl
						refreshing={!!refreshing}
						onRefresh={onRefresh}
						tintColor={theme.colors.brand}
						colors={[theme.colors.brand]}
					/>
				) : undefined
			}
		>
			{children}
		</ScrollView>
	) : (
		<View style={[styles.content, contentContainerStyle]}>{children}</View>
	);

	return (
		<>
			{showHeader ? (
				<Stack.Screen
					options={{
						title,
						headerRight: headerRight ? () => <>{headerRight}</> : undefined,
						headerLeft: headerLeft
							? () => <>{headerLeft}</>
							: () => (
									<TouchableOpacity
										onPress={() => router.back()}
										style={{ marginLeft: theme.spacing.md, flexDirection: "row", alignItems: "center", gap: 4 }}
										accessibilityRole="button"
										accessibilityLabel="Go back"
									>
										<Ionicons name="chevron-back" size={22} color={theme.colors.text} />
									</TouchableOpacity>
							  ),
					}}
				/>
			) : null}
			<SafeAreaView
				testID={testID}
				style={[styles.container, style]}
				edges={(edges ?? ["top", "bottom", "left", "right"]) as any}
			>
				{header}
				{content}
				{showScrollToTop && showTop && scroll ? (
					<TouchableOpacity
						style={styles.scrollToTop}
						onPress={() => scrollRef.current?.scrollTo({ y: 0, animated: true })}
						accessibilityRole="button"
						accessibilityLabel="Scroll to top"
					>
						<Ionicons name="arrow-up" size={22} color={theme.colors.text} />
					</TouchableOpacity>
				) : null}
				{fab ? <View style={{ position: "absolute", right: 16, bottom: 20 }}>{fab}</View> : null}
			</SafeAreaView>
		</>
	);
}

export default Screen;
