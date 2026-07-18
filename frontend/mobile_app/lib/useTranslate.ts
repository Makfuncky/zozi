import { useEffect, useState } from "react";
import { useLocaleStore } from "@/lib/localeStore";
import { apiFetch } from "@/lib/api";

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
    const firstKey = CACHE.keys().next().value;
    if (firstKey !== undefined) CACHE.delete(firstKey);
  }

  CACHE.set(cacheKey(text, target), translated);
}

type PendingBucket = {
  texts: Set<string>;
  resolvers: Map<string, Array<(value: string) => void>>;
  timer: ReturnType<typeof setTimeout> | null;
};

const pendingBuckets = new Map<string, PendingBucket>();

function getPendingBucket(target: string): PendingBucket {
  const existing = pendingBuckets.get(target);
  if (existing) return existing;

  const next: PendingBucket = {
    texts: new Set<string>(),
    resolvers: new Map<string, Array<(value: string) => void>>(),
    timer: null,
  };
  pendingBuckets.set(target, next);
  return next;
}

function resolvePending(target: string, original: string, translated: string) {
  const bucket = pendingBuckets.get(target);
  const resolvers = bucket?.resolvers.get(original);
  if (!resolvers?.length) return;

  resolvers.forEach((resolve) => resolve(translated));
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
    const data = await apiFetch<{ translations: string[] }>("/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts: missingTexts, target, source: "en" }),
      skipAuth: true,
    });

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

export function useTranslateText(text: string | null | undefined): string {
  const locale = useLocaleStore((state) => state.locale);
  const [translated, setTranslated] = useState(text ?? "");

  useEffect(() => {
    if (!text) {
      setTranslated("");
      return;
    }

    if (locale === "en") {
      setTranslated(text);
      return;
    }

    const cached = cacheGet(text, locale);
    if (cached !== undefined) {
      setTranslated(cached);
      return;
    }

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

export function useTranslateTexts(texts: (string | null | undefined)[]): string[] {
  const locale = useLocaleStore((state) => state.locale);
  const [translated, setTranslated] = useState<string[]>(texts.map((text) => text ?? ""));
  const key = texts.join("||");

  useEffect(() => {
    const safeTexts = texts.map((text) => text ?? "");

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
  }, [key, locale]);

  return translated;
}