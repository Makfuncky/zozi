"use client";

import {
  useState, useRef, useCallback, useEffect, useMemo,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Mic, Camera, Sparkles, X, Loader2, History, TrendingUp,
  ImageIcon, Cpu,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────

export type UnifiedSearchMode = "standard" | "ai";

export interface UnifiedSearchBarProps {
  /** Current search text */
  value: string;
  /** Called when the user confirms search (Enter, voice result, image upload) */
  onChange: (value: string) => void;
  /** Called when user commits (clicks search, presses Enter) */
  onSearch: () => void;
  /** Current search mode */
  mode?: UnifiedSearchMode;
  /** Called when AI mode toggles */
  onModeChange?: (mode: UnifiedSearchMode) => void;
  /** Whether AI search is available */
  aiAvailable?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Optional class */
  className?: string;
  /** Trending searches to show on focus */
  trendingSearches?: string[];
  /** Locale for voice recognition */
  locale?: string;
  /** Called when an image is uploaded for visual search (returns file) */
  onImageSearch?: (file: File) => void;
  /** Whether an image search is in progress */
  imageSearching?: boolean;
  /** Image preview URL if one is uploaded */
  imagePreview?: string | null;
  /** Called to clear image search */
  onClearImage?: () => void;
  /** Whether voice listening is active */
  isListening?: boolean;
  /** Called when voice input produces text */
  onVoiceResult?: (text: string) => void;
  /** Current voice amplitude (0-1) for waveform */
  voiceAmplitude?: number;
  /** On focus gained */
  onFocus?: () => void;
  /** On focus lost */
  onBlur?: () => void;
}

// ─── Waveform visualization ──────────────────────────────────────────────

function WaveformBars({ amplitude = 0.3, barCount = 16 }: { amplitude?: number; barCount?: number }) {
  const [tick, setTick] = useState(0);

  // Drive animation via requestAnimationFrame while listening
  useEffect(() => {
    let raf: number;
    let start = performance.now();
    const animate = () => {
      setTick((performance.now() - start) * 0.001);
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, []);

  const heights = useMemo(() => {
    const bars: number[] = [];
    for (let i = 0; i < barCount; i++) {
      const center = Math.abs(i - barCount / 2) / (barCount / 2);
      const variation = Math.sin(i * 1.2 + tick * 3) * 0.4 + 0.6;
      bars.push(Math.max(0.12, amplitude * (1 - center * 0.5) * variation));
    }
    return bars;
  }, [amplitude, barCount, tick]);

  return (
    <div className="flex items-center gap-[2px] h-6" aria-label="Voice waveform">
      {heights.map((h, i) => (
        <motion.div
          key={i}
          className="w-[2px] rounded-full bg-danger"
          animate={{ height: `${Math.max(4, h * 24)}px`, opacity: h > 0.15 ? 1 : 0.3 }}
          transition={{ duration: 0.08, ease: "linear" }}
        />
      ))}
    </div>
  );
}

// ─── Suggestions dropdown ────────────────────────────────────────────────

interface SuggestionItem {
  type: "product" | "supplier" | "trending";
  label: string;
  sublabel?: string;
}

function SuggestionsDropdown({
  items,
  selectedIndex,
  onSelect,
  onHover,
  aiMode,
}: {
  items: SuggestionItem[];
  selectedIndex: number;
  onSelect: (item: SuggestionItem) => void;
  onHover: (index: number) => void;
  aiMode: boolean;
}) {
  if (items.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -4, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -4, scale: 0.97 }}
      transition={{ duration: 0.12, ease: "easeOut" }}
      className="absolute top-full left-0 right-0 mt-1.5 z-[100] rounded-xl overflow-hidden glass-dropdown"
    >
      {aiMode && (
        <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-border/60 bg-primary/5">
          <Cpu className="w-3 h-3 text-primary" />
          <span className="text-[10px] font-semibold text-primary">AI semantic search active</span>
        </div>
      )}
      {items.map((item, i) => (
        <button
          key={`${item.type}-${item.label}`}
          type="button"
          onMouseDown={(e) => { e.preventDefault(); onSelect(item); }}
          onMouseEnter={() => onHover(i)}
          data-active={selectedIndex === i}
          className={cn(
            "flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors",
            selectedIndex === i ? "bg-primary/10 text-text" : "text-text-muted hover:bg-surface-2 hover:text-text",
          )}
        >
          {item.type === "trending" && <TrendingUp className="w-3 h-3 shrink-0 text-danger/60" />}
          {item.type === "product" && <Search className="w-3 h-3 shrink-0 text-text-faint" />}
          {item.type === "supplier" && <Sparkles className="w-3 h-3 shrink-0 text-primary/60" />}
          <div className="min-w-0 flex-1">
            <span className="text-[12px] font-medium truncate block">{item.label}</span>
            {item.sublabel && (
              <span className="text-[9px] text-text-faint truncate block">{item.sublabel}</span>
            )}
          </div>
        </button>
      ))}
    </motion.div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────

export default function UnifiedSearchBar({
  value,
  onChange,
  onSearch,
  mode = "standard",
  onModeChange,
  aiAvailable = true,
  placeholder = "Search products, brands, suppliers...",
  className,
  trendingSearches = [],
  locale = "en-US",
  onImageSearch,
  imageSearching = false,
  imagePreview = null,
  onClearImage,
  isListening = false,
  onVoiceResult,
  voiceAmplitude = 0.3,
  onFocus,
  onBlur,
}: UnifiedSearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const suggestionRef = useRef<HTMLDivElement>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [selectedSuggestionIdx, setSelectedSuggestionIdx] = useState(-1);
  const [showTrending, setShowTrending] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const addToast = useToastStore((s) => s.addToast);

  // Debounced autocomplete
  useEffect(() => {
    if (value.trim().length < 2) {
      setSuggestions([]);
      setSelectedSuggestionIdx(-1);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await apiFetch(`/search/autocomplete?q=${encodeURIComponent(value.trim())}&limit=8`);
        if (!res.ok) return;
        const data = await res.json();
        const items: SuggestionItem[] = (data.suggestions ?? []).map((s: string) => ({
          type: "product" as const,
          label: s,
        }));
        setSuggestions(items);
        setSelectedSuggestionIdx(-1);
      } catch {
        setSuggestions([]);
      }
    }, 120);
    return () => clearTimeout(timer);
  }, [value]);

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (selectedSuggestionIdx >= 0 && suggestions[selectedSuggestionIdx]) {
        onChange(suggestions[selectedSuggestionIdx].label);
        setShowSuggestions(false);
      }
      onSearch();
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedSuggestionIdx((prev) => Math.min(prev + 1, suggestions.length - 1));
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedSuggestionIdx((prev) => Math.max(prev - 1, -1));
    }
    if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  }, [onChange, onSearch, selectedSuggestionIdx, suggestions]);

  // Voice search
  const handleVoice = useCallback(() => {
    if (isListening) return; // Already listening, handled by parent

    const SpeechRecognitionAPI =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      addToast("Voice search is not supported in this browser", "info");
      return;
    }

    if (onVoiceResult) {
      // Signal parent to start listening
      onVoiceResult("__start__");
    }
  }, [isListening, onVoiceResult, addToast]);

  // Image upload
  const handleImageClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleImageFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (onImageSearch) {
      onImageSearch(file);
    }
    // Reset input so same file can be re-selected
    e.target.value = "";
  }, [onImageSearch]);

  // Focus management
  const handleFocus = useCallback(() => {
    setIsFocused(true);
    setShowSuggestions(true);
    if (trendingSearches.length > 0 && !value.trim()) {
      setShowTrending(true);
    }
    onFocus?.();
  }, [onFocus, trendingSearches, value]);

  const handleBlur = useCallback(() => {
    setTimeout(() => {
      setIsFocused(false);
      setShowSuggestions(false);
      setShowTrending(false);
    }, 180);
    onBlur?.();
  }, [onBlur]);

  // Build suggestion items from autocomplete + trending
  const suggestionItems = useMemo(() => {
    const items: SuggestionItem[] = [];
    if (showTrending && trendingSearches.length > 0 && !value.trim()) {
      trendingSearches.slice(0, 5).forEach((s) => {
        items.push({ type: "trending", label: s });
      });
    }
    items.push(...suggestions);
    return items;
  }, [showTrending, trendingSearches, value, suggestions]);

  return (
    <div className={cn("relative", className)}>
      {/* Glass bar */}
      <div
        className={cn(
          "relative flex items-stretch rounded-[1.4rem] transition-all duration-200",
          "bg-surface-1 border border-border",
          "focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10",
          isFocused && "shadow-lg shadow-primary/5",
        )}
      >
        {/* AI mode toggle */}
        {aiAvailable && (
          <button
            type="button"
            onClick={() => onModeChange?.(mode === "ai" ? "standard" : "ai")}
            title={mode === "ai" ? "AI semantic search active" : "Enable AI semantic search"}
            data-active={mode === "ai"}
            className={cn(
              "flex items-center gap-1.5 px-2.5 border-r border-border transition-colors rounded-l-[1.4rem]",
              mode === "ai"
                ? "bg-primary/10 text-primary"
                : "text-text-muted hover:text-text hover:bg-surface-2",
            )}
          >
            <Cpu className="w-4 h-4" />
            <span className="text-[10px] font-semibold hidden sm:inline">AI</span>
          </button>
        )}

        {/* Text input */}
        <div className="relative flex-1 flex items-center px-3 gap-2">
          <Search className="w-4 h-4 shrink-0 text-text-faint" />
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              setShowSuggestions(true);
              setShowTrending(false);
            }}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            placeholder={trendingSearches.length > 0 && !value
              ? `Try: ${trendingSearches.slice(0, 3).join(", ")}`
              : placeholder
            }
            className="flex-1 h-10 bg-transparent text-sm text-text placeholder:text-text-faint focus:outline-none"
          />
          {value && (
            <button
              type="button"
              onClick={() => { onChange(""); inputRef.current?.focus(); }}
              className="p-0.5 rounded text-text-faint hover:text-text transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center border-l border-border">
          {/* Image search */}
          <button
            type="button"
            onClick={handleImageClick}
            title="Search by image"
            disabled={imageSearching}
            className={cn(
              "relative flex items-center justify-center w-10 h-10 transition-colors",
              imagePreview ? "text-primary" : "text-text-muted hover:text-text hover:bg-surface-2",
              imageSearching && "animate-pulse",
            )}
          >
            {imageSearching ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : imagePreview ? (
              <div className="relative w-6 h-6 rounded overflow-hidden ring-1 ring-primary/40">
                <img src={imagePreview} alt="" className="w-full h-full object-cover" />
              </div>
            ) : (
              <Camera className="w-4 h-4" />
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleImageFile}
          />

          {/* Voice search */}
          <button
            type="button"
            onClick={handleVoice}
            title={isListening ? "Listening..." : "Voice search"}
            disabled={isListening}
            className={cn(
              "flex items-center justify-center w-10 h-10 transition-colors",
              isListening
                ? "text-danger"
                : "text-text-muted hover:text-text hover:bg-surface-2",
            )}
          >
            {isListening ? (
              <WaveformBars amplitude={voiceAmplitude} />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>

          {/* Search button */}
          <button
            type="button"
            onClick={onSearch}
            className="flex items-center gap-1.5 h-10 px-4 bg-primary text-on-brand rounded-r-[1.4rem] font-semibold text-xs hover:bg-primary/90 transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>
      </div>

      {/* Image preview chip */}
      <AnimatePresence>
        {imagePreview && (
          <motion.div
            initial={{ opacity: 0, y: -8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -8, height: 0 }}
            className="mt-2 flex items-center gap-2"
          >
            <div className="flex items-center gap-1.5 rounded-lg bg-primary/10 border border-primary/20 px-2.5 py-1">
              <div className="w-8 h-8 rounded overflow-hidden border border-border">
                <img src={imagePreview} alt="Search image" className="w-full h-full object-cover" />
              </div>
              <span className="text-[10px] font-medium text-primary">
                Visual search active
              </span>
              <button
                type="button"
                onClick={() => onClearImage?.()}
                className="ml-1 p-0.5 rounded text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Suggestions dropdown */}
      <AnimatePresence>
        {showSuggestions && suggestionItems.length > 0 && (
          <div ref={suggestionRef}>
            <SuggestionsDropdown
              items={suggestionItems}
              selectedIndex={selectedSuggestionIdx}
              onSelect={(item) => {
                onChange(item.label);
                setShowSuggestions(false);
                onSearch();
              }}
              onHover={setSelectedSuggestionIdx}
              aiMode={mode === "ai"}
            />
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
