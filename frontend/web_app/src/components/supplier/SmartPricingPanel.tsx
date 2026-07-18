"use client";

import { Button } from "@/components/ui/Button";

import { useState } from 'react';
import { DollarSign, TrendingUp, Info, CheckCircle2 } from '@/lib/icons';

interface SmartPricingPanelProps {
  basePrice: string;
  onPriceChange: (price: string) => void;
  aiSuggestedPrice?: { min: number; max: number; suggested: number };
  onPublish: () => void;
  onSaveDraft: () => void;
  onEditDetails: () => void;
  onEditImages: () => void;
  publishing: boolean;
}

export default function SmartPricingPanel({
  basePrice,
  onPriceChange,
  aiSuggestedPrice,
  onPublish,
  onSaveDraft,
  onEditDetails,
  onEditImages,
  publishing,
}: SmartPricingPanelProps) {
  const [comparePrice, setComparePrice] = useState('');

  const price = parseFloat(basePrice) || 0;
  const compare = parseFloat(comparePrice) || 0;
  const discount = compare > price ? Math.round((1 - price / compare) * 100) : 0;

  return (
    <div className="space-y-5">
      {/* Price entry */}
      <div>
        <h3 className="text-sm font-semibold text-text mb-3">Finalize Listing</h3>
        <div className="space-y-3">
          <div>
            <p className="text-xs font-medium text-text-muted mb-1.5">Base Price (OMR)</p>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-text-muted">OMR</span>
              <input type="number" step="0.001" min="0" placeholder="0.000"
                value={basePrice}
                onChange={(e) => onPriceChange(e.target.value)}
                className="w-full pl-14 pr-4 py-3 border border-border rounded-xl text-sm bg-surface text-text focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none" />
            </div>
            {aiSuggestedPrice && (
              <div className="mt-1.5 flex items-start gap-1.5 text-xs text-text-muted">
                <TrendingUp className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <span>
                  AI suggests: <strong className="text-primary">{aiSuggestedPrice.suggested.toFixed(3)} OMR</strong>
                  &nbsp;(range: {aiSuggestedPrice.min.toFixed(3)} - {aiSuggestedPrice.max.toFixed(3)} OMR)
                </span>
              </div>
            )}
          </div>

          <div>
            <p className="text-xs font-medium text-text-muted mb-1.5">Compare Price (Optional)</p>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-text-muted">OMR</span>
              <input type="number" step="0.001" min="0" placeholder="0.000"
                value={comparePrice}
                onChange={(e) => setComparePrice(e.target.value)}
                className="w-full pl-14 pr-4 py-3 border border-border rounded-xl text-sm bg-surface text-text focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none" />
            </div>
            {discount > 0 && (
              <div className="mt-1.5 flex items-center gap-1.5 text-xs text-success">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{discount}% OFF — shown as discount on listing</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Preview card */}
      <div className="bg-gradient-to-br from-primary/5 to-accent/5 rounded-xl p-4 border border-primary/10 space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-medium text-text-muted mb-2">
          <Info className="w-3.5 h-3.5" />
          Listing Preview
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-text-muted">Price</span>
          <span className="font-semibold text-text">{price > 0 ? `${price.toFixed(3)} OMR` : 'Not set'}</span>
        </div>
        {compare > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">Was</span>
            <span className="text-text-faint line-through">{compare.toFixed(3)} OMR</span>
          </div>
        )}
        {discount > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">Discount</span>
            <span className="text-success font-medium">{discount}% OFF</span>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="space-y-2.5">
        <Button variant="primary" onClick={onPublish} disabled={publishing || price <= 0}>
          {publishing ? 'Publishing...' : 'Publish to Store'}
        </Button>
        <div className="grid grid-cols-2 gap-2.5">
          <button onClick={onEditDetails}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 border border-border text-text-muted rounded-xl hover:bg-surface-2 transition-colors text-sm">
            Edit Details
          </button>
          <button onClick={onEditImages}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 border border-border text-text-muted rounded-xl hover:bg-surface-2 transition-colors text-sm">
            Edit Images
          </button>
        </div>
        <button onClick={onSaveDraft}
          className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-text-faint rounded-xl hover:bg-surface-2 transition-colors text-xs">
          Save as Draft
        </button>
      </div>
    </div>
  );
}
