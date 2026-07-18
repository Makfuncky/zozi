"use client";

/**
 * TranslatedText — inline component that renders dynamic text
 * translated to the current locale via the backend /translate endpoint.
 *
 * Wraps useTranslateText. Falls back to the original text while loading
 * or on network failure, so the UI is never blank.
 *
 * @example
 *   <TranslatedText text={product.name} as="h2" className="font-bold" />
 *   <TranslatedText text={supplier.username} />
 */

import { useTranslateText } from "@/lib/useTranslate";
import { ElementType } from "react";

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