"use client";

import { type ElementType } from "react";
import { useTranslateText } from "@/lib/useTranslate";

interface TranslatedTextProps {
	text: string | null | undefined;
	as?: ElementType;
	className?: string;
	fallback?: string;
}

export default function TranslatedText({
	text,
	as: Tag = "span",
	className,
	fallback = "",
}: TranslatedTextProps) {
	const value = useTranslateText(text ?? fallback);
	return <Tag className={className}>{value || fallback}</Tag>;
}


