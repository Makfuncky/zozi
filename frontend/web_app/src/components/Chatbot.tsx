"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { getChatbotReplyKey } from "@shared/chatbot";
import type { ChatbotResponsePayload, ChatbotResultMode, ChatbotSearchResult } from "@shared/chatbot";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { TranslationKey } from "@/lib/i18n";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateText, useTranslateTexts } from "@/lib/useTranslate";
import { PLACEHOLDER_IMAGE_PATH, resolveImage } from "@/lib/utils";

type SearchResult = ChatbotSearchResult;

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  time: string;
  products?: SearchResult[];
  suggestedPrompts?: string[];
  resultMode?: ChatbotResultMode;
  translateText?: boolean;
  translatePrompts?: boolean;
}

function productTags(product: SearchResult): string[] {
  const tags = [product.brand, product.category, product.color].filter(
    (value): value is string => Boolean(value && value.trim())
  );
  if (product.sizes?.length) {
    tags.push(`Sizes: ${product.sizes.slice(0, 3).join(", ")}`);
  }
  return tags.slice(0, 4);
}

function ChatMessageBubble({
  message,
  formatPrice,
  typing,
  onPromptPress,
  onProductPress,
}: {
  message: Message;
  formatPrice: (amount: number) => string;
  typing: boolean;
  onPromptPress: (prompt: string) => void;
  onProductPress: (productId: number) => void;
}) {
  const translatedBotText = useTranslateText(message.translateText ? message.text : null);
  const translatedPrompts = useTranslateTexts(message.translatePrompts ? message.suggestedPrompts ?? [] : []);
  const closeMatchesLabel = useTranslateText(message.resultMode === "close" ? "Close matches" : null);
  const displayText = message.translateText ? translatedBotText : message.text;

  return (
    <div className={`flex ${message.isBot ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[85%] rounded-[20px] border px-3 py-2.5 text-xs ${
          message.isBot
            ? "border-primary/40 bg-gradient-to-br from-primary/28 via-primary/18 to-primary/8 text-text backdrop-blur-md shadow-glow-primary"
            : "border-accent/50 bg-gradient-to-br from-accent/32 via-accent/20 to-accent/10 text-text backdrop-blur-md shadow-glow-accent"
        }`}
      >
        <p className="leading-5">{displayText}</p>

        <div className={`mt-2 h-1.5 rounded-full ${message.isBot ? "bg-primary/24" : "bg-accent/28"}`} />

        {message.products && message.products.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.resultMode === "close" && closeMatchesLabel && (
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-faint">{closeMatchesLabel}</p>
            )}

            {message.products.map((product) => (
              <Link
                key={product.id}
                href={`/products/${product.id}`}
                className="flex items-center gap-2 rounded-xl border border-border bg-surface-0 p-2 transition-colors hover:border-primary"
                onClick={() => onProductPress(product.id)}
              >
                <Image
                  src={resolveImage(product.image_url ?? undefined)}
                  alt={product.name}
                  width={32}
                  height={32}
                  className="rounded-lg object-cover shrink-0"
                  onError={(event) => {
                    (event.target as HTMLImageElement).src = PLACEHOLDER_IMAGE_PATH;
                  }}
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium leading-tight text-text">{product.name}</p>
                  <p className="text-sm font-semibold text-primary">{formatPrice(product.price)}</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {typeof product.rating === "number" && product.rating > 0 && (
                      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                        {product.rating.toFixed(1)} star
                      </span>
                    )}
                    {productTags(product).map((tag) => (
                      <span
                        key={`${product.id}-${tag}`}
                        className="rounded-full border border-border bg-surface-1 px-2 py-0.5 text-[10px] font-medium text-text-muted"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {message.isBot && message.suggestedPrompts && message.suggestedPrompts.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.suggestedPrompts.map((prompt, index) => (
              <Button variant="primary" className="rounded-full border px-2.5 py-1 text-[10px] font-semibold text-primary transition-colors disabled:opacity-50" key={`${message.id}-${prompt}`}
                type="button"
                onClick={() => onPromptPress(prompt)}
                disabled={typing}
              >
                {translatedPrompts[index] ?? prompt}
              </Button>
            ))}
          </div>
        )}

        <p className={`mt-1 text-[10px] ${message.isBot ? "text-text-faint" : "text-text-muted"}`}>
          {message.time}
        </p>
      </div>
    </div>
  );
}

function nowTime(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function shouldHideChatbot(pathname: string | null): boolean {
  if (!pathname) return false;
  if (pathname.startsWith("/admin")) return true;
  if (!pathname.startsWith("/supplier/")) return false;
  return !["/supplier/login", "/supplier/register"].includes(pathname);
}

function parseSupplierScope(rawSupplierId: string | null): number | null {
  if (!rawSupplierId) return null;
  const parsed = Number(rawSupplierId);
  if (!Number.isInteger(parsed) || parsed <= 0) return null;
  return parsed;
}

export default function Chatbot() {
  const tr = useLocaleStore((s) => s.t);
  const formatPrice = useCurrencyStore((s) => s.format);
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const scopedSupplierId = parseSupplierScope(searchParams?.get("supplier") ?? null);
  const isChatbotRoute = pathname === "/chatbot";

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => [
    {
      id: 1,
      text: useLocaleStore.getState().t("chatbotGreeting"),
      isBot: true,
      time: nowTime(),
      resultMode: "none",
      translateText: false,
      translatePrompts: false,
    },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const endRef = useRef<HTMLDivElement>(null);

  const recordProductClick = async (productId: number) => {
    if (!sessionId) return;
    try {
      await apiFetch(`/chatbot/record-click/${productId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch {
      // Click tracking should never interrupt navigation.
    }
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isChatbotRoute) {
      setIsOpen(true);
    }
  }, [isChatbotRoute]);

  if (shouldHideChatbot(pathname)) return null;

  const addBotMessage = (
    text: string,
    products?: SearchResult[],
    suggestedPrompts?: string[],
    resultMode: ChatbotResultMode = "none",
    options: { translateText?: boolean; translatePrompts?: boolean } = {}
  ) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + 1,
        text,
        isBot: true,
        time: nowTime(),
        products,
        suggestedPrompts,
        resultMode,
        translateText: options.translateText ?? false,
        translatePrompts: options.translatePrompts ?? false,
      },
    ]);
    setTyping(false);
  };

  const addFallbackReply = (query: string) => {
    const key = getChatbotReplyKey(query) as TranslationKey;
    addBotMessage(tr(key), undefined, undefined, "none");
  };

  const sendMessage = async (rawQuery: string) => {
    const query = rawQuery.trim();
    if (!query || typing) return;

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        text: query,
        isBot: false,
        time: nowTime(),
      },
    ]);
    setInput("");
    setTyping(true);

    try {
      const locale = useLocaleStore.getState().locale || "en";
      const supplierScopeQuery = scopedSupplierId ? `?supplier_id=${scopedSupplierId}` : "";
      const response = await apiFetch(`/chatbot/message${supplierScopeQuery}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query, session_id: sessionId, lang: locale }),
      });
      if (!response.ok) {
        throw new Error("chatbot request failed");
      }

      const payload = await response.json() as ChatbotResponsePayload;

      if (payload.session_id) setSessionId(payload.session_id);

      // The backend localizes reply text + suggested prompts by `lang`, so we
      // only run the frontend translator when the locale is NOT Arabic (en is a
      // no-op anyway). This prevents double-translating already-Arabic text.
      const shouldTranslate = locale !== "ar";

      addBotMessage(
        payload.reply || tr("chatbotNoResults"),
        payload.products,
        payload.suggested_prompts,
        payload.result_mode ?? (payload.products?.length ? "exact" : "none"),
        { translateText: shouldTranslate, translatePrompts: shouldTranslate }
      );
    } catch {
      addFallbackReply(query);
    }
  };

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    await sendMessage(input);
  };

  return (
    <>
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 right-4 z-50 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent px-4 py-3 text-on-accent shadow-glow-accent ring-1 ring-white/85 transition-transform"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        aria-label={tr("chatbotToggle")}
      >
        {isOpen ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        )}
        <span className="hidden text-xs font-black uppercase tracking-[0.28em] sm:inline">Chat</span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 20 }}
            className="fixed bottom-20 right-4 z-50 flex h-[min(70vh,40rem)] w-[min(24rem,calc(100vw-1.5rem))] max-w-96 flex-col overflow-hidden rounded-[28px] border border-border bg-surface-0/96 shadow-card-xl backdrop-blur-2xl"
          >
            <div className="border-b border-border bg-surface-1 px-4 py-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-text">{tr("chatbotTitle")}</h3>
                  {scopedSupplierId && (
                    <p className="mt-1 text-[11px] text-text-faint">
                      Supplier-focused mode enabled. Personal details are never shared.
                    </p>
                  )}
                </div>
                <div className="inline-flex shrink-0 items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary">
                  <span className="h-2 w-2 rounded-full bg-primary" />
                  {tr("chatbotOnline")}
                </div>
              </div>
            </div>

            <div className="flex-1 space-y-2 overflow-y-auto bg-surface-0 px-3 py-3">
              {messages.map((message) => (
                <ChatMessageBubble
                  key={message.id}
                  message={message}
                  formatPrice={formatPrice}
                  typing={typing}
                  onPromptPress={(prompt) => void sendMessage(prompt)}
                  onProductPress={(productId) => {
                    void recordProductClick(productId);
                    setIsOpen(false);
                  }}
                />
              ))}

              {typing && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-[20px] border border-border bg-surface-1 px-4 py-2 text-xs text-text-muted">
                    {[0, 0.2, 0.4].map((delay, index) => (
                      <motion.div
                        key={index}
                        className="w-2 h-2 bg-primary-light rounded-full"
                        animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }}
                        transition={{ duration: 1.2, repeat: Infinity, delay }}
                      />
                    ))}
                    <span>{tr("loading")}</span>
                  </div>
                </div>
              )}

              <div ref={endRef} />
            </div>

            <form onSubmit={send} className="flex gap-2 border-t border-border bg-surface-1 p-2.5">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder={tr("chatbotPlaceholder")}
                disabled={typing}
                className="theme-input flex-1 rounded-full border bg-surface-0 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
              <button
                type="submit"
                disabled={!input.trim() || typing}
                className="flex h-11 min-w-11 items-center justify-center rounded-full theme-btn-primary px-4 text-sm font-semibold disabled:opacity-50 disabled:bg-surface-3! disabled:text-text-faint!"
                aria-label={tr("sendMessage")}
              >
                Go
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}


