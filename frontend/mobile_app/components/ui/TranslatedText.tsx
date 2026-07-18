import React from "react";
import { Text, type TextProps } from "react-native";
import { useTranslateText } from "@/lib/useTranslate";

interface TranslatedTextProps extends TextProps {
	text: string | null | undefined;
	fallback?: string;
}

export default function TranslatedText({
	text,
	fallback = "",
	...props
}: TranslatedTextProps) {
	const value = useTranslateText(text ?? fallback);
	return <Text {...props}>{value}</Text>;
}
