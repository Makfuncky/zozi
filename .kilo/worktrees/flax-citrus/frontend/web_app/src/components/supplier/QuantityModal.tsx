"use client";

import { X, ChevronLeft, ChevronRight, Copy, Wand2 } from '@/lib/icons';
import { useState, useEffect } from 'react';

interface QuantityModalProps {
  color: string;
  colorIndex: number;
  totalColors: number;
  sizes: string[];
  initialQuantities: Record<string, number>;
  onSave: (quantities: Record<string, number>) => void;
  onNext: () => void;
  onSkip?: () => void;
}

const DEFAULT_FILL = 50;

export default function QuantityModal({
  color,
  colorIndex,
  totalColors,
  sizes,
  initialQuantities,
  onSave,
  onNext,
  onSkip,
}: QuantityModalProps) {
  const [quantities, setQuantities] = useState<Record<string, number>>(initialQuantities);
  const [fillValue, setFillValue] = useState(DEFAULT_FILL);

  useEffect(() => {
    setQuantities(initialQuantities);
  }, [color, initialQuantities]);

  const updateQty = (size: string, val: string) => {
    const num = parseInt(val) || 0;
    setQuantities(prev => ({ ...prev, [size]: Math.max(0, num) }));
  };

  const fillAll = () => {
    const filled: Record<string, number> = {};
    sizes.forEach(s => { filled[s] = fillValue; });
    setQuantities(filled);
  };

  const copyFromPrev = () => {
    // Copy is handled by parent via initialQuantities
    onSave(quantities);
  };

  const handleNext = () => {
    onSave(quantities);
    onNext();
  };

  const totalStock = Object.values(quantities).reduce((s, v) => s + v, 0);
  const colorSwatch = color.toLowerCase();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" role="dialog" aria-modal="true">
      <div className="glass-panel relative w-full max-w-sm mx-4 rounded-xl border shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 pb-3 border-b border-border">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full border border-border"
                style={{ backgroundColor: colorSwatch }} />
              <h3 className="text-base font-semibold text-text">
                {color}
              </h3>
              <span className="text-xs text-text-faint">
                {colorIndex + 1} of {totalColors}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-xs font-medium text-text-muted">
                {totalStock} units
              </span>
              {onSkip && (
                <button onClick={onSkip} className="p-1 rounded hover:bg-surface-2 text-text-muted transition-colors">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Progress dots */}
          <div className="flex gap-1">
            {Array.from({ length: totalColors }).map((_, i) => (
              <div key={i}
                className={`flex-1 h-1 rounded-full transition-colors ${
                  i === colorIndex ? 'bg-primary' : i < colorIndex ? 'bg-success' : 'bg-surface-3'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="p-5 space-y-4">
          {/* Fill All shortcut */}
          <div className="flex items-center gap-2 p-3 bg-surface-2 rounded-xl">
            <Wand2 className="w-4 h-4 text-primary shrink-0" />
            <div className="flex items-center gap-1.5 flex-1">
              <span className="text-xs text-text-muted">Fill All</span>
              <input
                type="number"
                min="1"
                value={fillValue}
                onChange={(e) => setFillValue(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-16 px-2 py-1 text-xs text-center border border-border rounded-lg bg-surface-1 focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none"
              />
            </div>
            <button onClick={fillAll}
              className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
              Apply
            </button>
          </div>

          {/* Size quantity inputs */}
          <div className="space-y-2">
            {sizes.map(size => (
              <div key={size}
                className="flex items-center gap-3 p-2.5 bg-surface-2 rounded-xl hover:bg-surface-2/80 transition-colors">
                <span className="w-12 text-sm font-medium text-text">{size}</span>
                <input
                  type="number"
                  min="0"
                  placeholder="0"
                  value={quantities[size] ?? ''}
                  onChange={(e) => updateQty(size, e.target.value)}
                  onFocus={(e) => e.target.select()}
                  className="flex-1 px-3 py-2 text-sm text-center border border-border rounded-lg bg-surface-1 focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-colors"
                />
                <span className="w-16 text-xs text-text-faint text-right">units</span>
              </div>
            ))}
          </div>

          {/* Copy from previous */}
          {colorIndex > 0 && (
            <button onClick={copyFromPrev}
              className="w-full flex items-center justify-center gap-1.5 py-2 text-xs text-text-muted hover:text-primary transition-colors border border-dashed border-border rounded-lg">
              <Copy className="w-3.5 h-3.5" />
              Copy quantities from previous color
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="p-5 pt-0 flex items-center justify-between">
          <div>
            <p className="text-xs text-text-faint">Subtotal</p>
            <p className="text-sm font-bold text-text">{totalStock} units</p>
          </div>
          <div className="flex items-center gap-2">
            {colorIndex > 0 && (
              <button
                onClick={() => onSave(quantities)}
                className="px-3 py-2 text-xs text-text-muted hover:text-text transition-colors"
              >
                Save
              </button>
            )}
            {colorIndex < totalColors - 1 ? (
              <button onClick={handleNext}
                className="theme-btn-primary px-5 py-2.5 text-sm font-medium flex items-center gap-1.5">
                Next Color <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button onClick={handleNext}
                className="theme-btn-primary px-5 py-2.5 text-sm font-medium">
                Review & Publish
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
