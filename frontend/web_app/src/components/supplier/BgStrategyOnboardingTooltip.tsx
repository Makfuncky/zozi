"use client";

import { useState, useEffect } from "react";
import { Info, X, ChevronRight, Sparkles } from "@/lib/icons";

interface BgStrategyOnboardingTooltipProps {
  isOpen: boolean;
  onClose: () => void;
  category?: string;
}

interface StrategyGuide {
  key: string;
  label: string;
  description: string;
  bestFor: string[];
  icon: string;
}

const STRATEGY_GUIDES: StrategyGuide[] = [
  {
    key: "clean_commercial",
    label: "Clean · br05",
    description: "Gentle edge refinement. Best for simple product shots with clean backgrounds.",
    bestFor: ["clothing", "fashion", "textiles", "apparel"],
    icon: "Wand2",
  },
  {
    key: "precision_geometry",
    label: "Geometry · br06",
    description: "Precision geometry preservation. Best for electronics, accessories, and products with fine details.",
    bestFor: ["electronics", "tech", "gadgets", "beauty", "cosmetics"],
    icon: "Layers",
  },
  {
    key: "birefnet_production",
    label: "Production · br08",
    description: "Highest quality. Best for complex backgrounds and products with holes or gaps.",
    bestFor: ["home", "furniture", "decor"],
    icon: "Zap",
  },
  {
    key: "ultimate_gaps",
    label: "Gaps · br11",
    description: "Fast all-rounder. Use when you're unsure — it handles most product types well.",
    bestFor: ["unknown", "other"],
    icon: "Sparkles",
  },
  {
    key: "marketing_variants",
    label: "Marketing · br12",
    description: "Aggressive artifact removal. Best for clean marketing shots and floating objects.",
    bestFor: ["beauty", "cosmetics", "jewelry"],
    icon: "Tag",
  },
  {
    key: "lite_variants",
    label: "Lite · br13",
    description: "Lightweight and fast. Best for clothing/fabric and low-RAM environments.",
    bestFor: ["clothing", "fashion", "textiles", "lingerie"],
    icon: "Camera",
  },
];

export default function BgStrategyOnboardingTooltip({
  isOpen,
  onClose,
  category,
}: BgStrategyOnboardingTooltipProps) {
  const [step, setStep] = useState(0);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (isOpen && !dismissed) {
      setStep(0);
    }
  }, [isOpen, dismissed]);

  if (!isOpen || dismissed) return null;

  const categoryLower = (category || "").toLowerCase();
  const recommendedStrategies = STRATEGY_GUIDES.filter((g) =>
    g.bestFor.some((b) => categoryLower.includes(b))
  );
  const fallbackStrategies = STRATEGY_GUIDES.filter(
    (g) => !recommendedStrategies.includes(g)
  );
  const displayStrategies =
    recommendedStrategies.length > 0
      ? recommendedStrategies
      : [STRATEGY_GUIDES[3]]; // ultimate_gaps as fallback

  const handleNext = () => {
    if (step < displayStrategies.length - 1) {
      setStep(step + 1);
    } else {
      handleDismiss();
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    onClose();
  };

  const current = displayStrategies[step] || displayStrategies[0];

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center theme-overlay">
      <div className="glass-panel relative w-full max-w-md mx-4 rounded-xl border shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-lg font-semibold text-text flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Choose Your BG Strategy
          </h2>
          <button
            onClick={handleDismiss}
            className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Category badge */}
          {category && (
            <div className="inline-flex items-center px-2.5 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
              {category}
            </div>
          )}

          {/* Strategy card */}
          <div className="theme-card p-4 border border-border/50">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <span className="text-lg">{current.icon === "Wand2" ? "🪄" : current.icon === "Layers" ? "📐" : current.icon === "Zap" ? "⚡" : current.icon === "Sparkles" ? "✨" : current.icon === "Tag" ? "🏷️" : "📷"}</span>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-text">{current.label}</h3>
                <p className="text-xs text-text-muted mt-1 leading-relaxed">
                  {current.description}
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {current.bestFor.map((b) => (
                    <span
                      key={b}
                      className="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-2 text-[10px] text-text-muted capitalize"
                    >
                      {b}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Progress dots */}
          <div className="flex items-center justify-center gap-1.5">
            {displayStrategies.map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full transition-all ${
                  idx === step
                    ? "bg-primary w-4"
                    : idx < step
                    ? "bg-primary/40"
                    : "bg-surface-3"
                }`}
              />
            ))}
          </div>

          {/* Tip text */}
          <p className="text-xs text-text-faint text-center">
            {step === 0 && "This is the best strategy for your product type."}
            {step === 1 && "You can always switch strategies manually using the buttons below."}
            {step >= 2 && "The AI will auto-select the best strategy for each upload."}
          </p>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleNext}
              className="flex-1 theme-btn-primary py-2.5 text-sm font-medium flex items-center justify-center gap-2"
            >
              {step < displayStrategies.length - 1 ? (
                <>
                  Next <ChevronRight className="w-4 h-4" />
                </>
              ) : (
                "Got it!"
              )}
            </button>
            <button
              type="button"
              onClick={handleDismiss}
              className="px-4 py-2.5 text-sm text-text-muted hover:text-text transition-colors"
            >
              Skip
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
