/**
 * useTranslate — translates dynamic text (product names, descriptions,
 * supplier names, etc.) via the backend /translate endpoint.
 *
 * • When locale === "en" → returns the original text immediately, no API call.
 * • When locale === "ar" → calls POST /translate, caches results in module-level
 *   cache, and returns the translated text reactively.
 * • Falls back to the original text gracefully if the request fails.
 */

"use client";

import { useState, useEffect } from "react";
import { useLocaleStore } from "./localeStore";
import { apiFetch } from "./api";

// ── Module-level LRU cache (survives component re-renders) ─────────────────
const CACHE = new Map<string, string>();
const CACHE_LIMIT = 2000;
const BATCH_DEBOUNCE_MS = 16;

function cacheKey(text: string, target: string) {
  return `${target}::${text}`;
}

function cacheGet(text: string, target: string): string | undefined {
  return CACHE.get(cacheKey(text, target));
}

function cacheSet(text: string, target: string, translated: string) {
  if (CACHE.size >= CACHE_LIMIT) {
    // Evict oldest entry (Map preserves insertion order)
    const firstKey = CACHE.keys().next().value;
    if (firstKey !== undefined) CACHE.delete(firstKey);
  }
  CACHE.set(cacheKey(text, target), translated);
}

// ── Batch queue — coalesces multiple translate calls into one request ───────
type PendingBucket = {
  texts: Set<string>;
  resolvers: Map<string, Array<(v: string) => void>>;
  timer: ReturnType<typeof setTimeout> | null;
};

const pendingBuckets = new Map<string, PendingBucket>();

function getPendingBucket(target: string): PendingBucket {
  const existing = pendingBuckets.get(target);
  if (existing) return existing;

  const next: PendingBucket = {
    texts: new Set<string>(),
    resolvers: new Map<string, Array<(v: string) => void>>(),
    timer: null,
  };
  pendingBuckets.set(target, next);
  return next;
}

function resolvePending(target: string, original: string, translated: string) {
  const bucket = pendingBuckets.get(target);
  const resolvers = bucket?.resolvers.get(original);
  if (!resolvers?.length) return;
  resolvers.forEach((fn) => fn(translated));
  bucket?.resolvers.delete(original);
}

async function requestTranslations(texts: string[], target: string) {
  const uniqueTexts = [...new Set(texts.filter(Boolean))];
  const missingTexts = uniqueTexts.filter((text) => cacheGet(text, target) === undefined);

  if (missingTexts.length === 0) {
    return uniqueTexts.reduce<Map<string, string>>((map, text) => {
      map.set(text, cacheGet(text, target) ?? text);
      return map;
    }, new Map<string, string>());
  }

  try {
    const res = await apiFetch("/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts: missingTexts, target, source: "en" }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: { translations: string[] } = await res.json();

    missingTexts.forEach((original, index) => {
      const translated = data.translations[index] ?? original;
      cacheSet(original, target, translated);
      resolvePending(target, original, translated);
    });
  } catch {
    missingTexts.forEach((original) => {
      cacheSet(original, target, original);
      resolvePending(target, original, original);
    });
  }

  return uniqueTexts.reduce<Map<string, string>>((map, text) => {
    map.set(text, cacheGet(text, target) ?? text);
    return map;
  }, new Map<string, string>());
}

async function flushBatch(target: string) {
  const bucket = getPendingBucket(target);
  bucket.timer = null;
  const texts = [...bucket.texts];
  bucket.texts.clear();

  if (texts.length === 0) return;

  await requestTranslations(texts, target);
}

function enqueueBatch(text: string, target: string): Promise<string> {
  const cached = cacheGet(text, target);
  if (cached !== undefined) return Promise.resolve(cached);

  return new Promise((resolve) => {
    const bucket = getPendingBucket(target);
    const existing = bucket.resolvers.get(text) ?? [];
    bucket.resolvers.set(text, [...existing, resolve]);
    bucket.texts.add(text);

    if (!bucket.timer) {
      bucket.timer = setTimeout(() => {
        void flushBatch(target);
      }, BATCH_DEBOUNCE_MS);
    }
  });
}

async function translateMany(texts: string[], target: string): Promise<string[]> {
  const safeTexts = texts.map((text) => text || "");
  const lookup = await requestTranslations(safeTexts, target);
  return safeTexts.map((text) => (text ? lookup.get(text) ?? text : ""));
}

// ── Main hook ──────────────────────────────────────────────────────────────

/**
 * Translates a single string to the current locale.
 * Returns the original while waiting (no flicker of wrong-language text).
 *
 * @example
 *   const name = useTranslateText(product.name);
 *   return <h2>{name}</h2>;
 */
export function useTranslateText(text: string | null | undefined): string {
  const locale = useLocaleStore((s) => s.locale) || "en";
  const [translated, setTranslated] = useState<string>(text ?? "");

  useEffect(() => {
    if (!text) {
      setTranslated("");
      return;
    }

    if (locale === "en") {
      setTranslated(text);
      return;
    }

    // Check cache first (sync)
    const cached = cacheGet(text, locale);
    if (cached !== undefined) {
      setTranslated(cached);
      return;
    }

    // Kick off batched request
    let cancelled = false;
    enqueueBatch(text, locale).then((result) => {
      if (!cancelled) setTranslated(result);
    });

    return () => {
      cancelled = true;
    };
  }, [text, locale]);

  return translated || text || "";
}

/**
 * Translates an array of strings to the current locale in one request.
 * Returns an array of the same length (originals while loading).
 */
export function useTranslateTexts(texts: (string | undefined | null)[]): string[] {
  const locale = useLocaleStore((s) => s.locale) || "en";
  const [translated, setTranslated] = useState<string[]>(
    texts.map((t) => t ?? "")
  );

  // Stable key so effect only re-runs on real content changes
  const key = texts.join("||");

  useEffect(() => {
    const safeTexts = texts.map((t) => t ?? "");

    if (locale === "en") {
      setTranslated(safeTexts);
      return;
    }

    let cancelled = false;
    translateMany(safeTexts, locale).then((results) => {
      if (!cancelled) setTranslated(results);
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, locale]);

  return translated;
}
