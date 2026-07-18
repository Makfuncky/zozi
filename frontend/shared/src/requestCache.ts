export const DEFAULT_SHORT_GET_TTL_MS = 2500;

type CacheEntry<T> = {
  expiresAt: number;
  value: T;
};

const UNCACHEABLE_GET_PATTERNS = [
  /^\/auth(?:\/|$)/,
  /^\/admin(?:\/|$)/,
  /^\/email(?:\/|$)/,
  /^\/jobs(?:\/|$)/,
  /^\/notifications(?:\/|$)/,
  /\/tracking(?:\?|$)/,
  /\/download(?:\?|$)/,
];

function normalizeCachePath(pathOrUrl: string): string {
  if (!pathOrUrl) return "/";
  if (/^https?:\/\//i.test(pathOrUrl)) {
    try {
      const parsed = new URL(pathOrUrl);
      return `${parsed.pathname}${parsed.search}`;
    } catch {
      return pathOrUrl;
    }
  }
  return pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`;
}

export function shouldUseShortGetCache(
  pathOrUrl: string,
  method: string,
  disableCache = false,
): boolean {
  if (disableCache || method.toUpperCase() !== "GET") {
    return false;
  }

  const normalizedPath = normalizeCachePath(pathOrUrl);
  return !UNCACHEABLE_GET_PATTERNS.some((pattern) => pattern.test(normalizedPath));
}

export function buildShortGetCacheKey({
  url,
  authToken,
  extraKey,
}: {
  url: string;
  authToken?: string | null;
  extraKey?: string;
}): string {
  return [url, authToken ?? "anon", extraKey ?? ""].join("::");
}

export function createTimedRequestCache<T>() {
  const resolved = new Map<string, CacheEntry<T>>();
  const inflight = new Map<string, Promise<T>>();

  function get(key: string): T | null {
    const entry = resolved.get(key);
    if (!entry) return null;
    if (entry.expiresAt <= Date.now()) {
      resolved.delete(key);
      return null;
    }
    return entry.value;
  }

  async function getOrSet(
    key: string,
    loader: () => Promise<T>,
    ttlMs: number,
    shouldStore: (value: T) => boolean = () => true,
  ): Promise<T> {
    const cached = get(key);
    if (cached !== null) {
      return cached;
    }

    const current = inflight.get(key);
    if (current) {
      return current;
    }

    const pending = loader()
      .then((value) => {
        if (ttlMs > 0 && shouldStore(value)) {
          resolved.set(key, { value, expiresAt: Date.now() + ttlMs });
        }
        return value;
      })
      .finally(() => {
        inflight.delete(key);
      });

    inflight.set(key, pending);
    return pending;
  }

  function invalidateAll(): void {
    resolved.clear();
    inflight.clear();
  }

  return {
    getOrSet,
    invalidateAll,
  };
}

type ResponseSnapshot = {
  body: ArrayBuffer;
  headers: Array<[string, string]>;
  status: number;
  statusText: string;
};

async function snapshotResponse(response: Response): Promise<ResponseSnapshot> {
  const clone = response.clone();
  const headers: Array<[string, string]> = [];
  clone.headers.forEach((value, key) => {
    headers.push([key, value]);
  });

  return {
    body: await clone.arrayBuffer(),
    headers,
    status: clone.status,
    statusText: clone.statusText,
  };
}

function materializeResponse(snapshot: ResponseSnapshot): Response {
  return new Response(snapshot.body.slice(0), {
    status: snapshot.status,
    statusText: snapshot.statusText,
    headers: snapshot.headers,
  });
}

export function createResponseRequestCache() {
  const cache = createTimedRequestCache<ResponseSnapshot>();

  return {
    async getOrSet(
      key: string,
      loader: () => Promise<Response>,
      ttlMs: number,
      shouldCache: (response: Response) => boolean = () => true,
    ): Promise<Response> {
      const snapshot = await cache.getOrSet(
        key,
        async () => snapshotResponse(await loader()),
        ttlMs,
        (snapshot) => shouldCache(materializeResponse(snapshot)),
      );
      return materializeResponse(snapshot);
    },
    invalidateAll(): void {
      cache.invalidateAll();
    },
  };
}